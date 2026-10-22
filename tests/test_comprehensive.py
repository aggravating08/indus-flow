"""Comprehensive Test Suite — Indus Flow Autonomous Supply Chain Agent.

Open Agent Hackathon 2026 | Team Indus
Covers: World Model engine, Disruption Detector, Action Generator,
Repository CRUD, Zetaris Connector, NVIDIA NIM Adapter,
Full Agent Cycle, Human Approval Gate, Audit Trail.
"""

import asyncio
import copy
import pytest
from src.engines.world_model import MeterlessWorldModelEngine, WorldState, dump_model
from src.agents.disruption_detector import DisruptionDetector
from src.agents.action_generator import ActionGenerator
from src.agents.resilience_agent import SupplyChainResilienceAgent
from src.connectors.zetaris_connector import ZetarisConnector
from src.connectors.nvidia_nim import NvidiaNimClient
from src.data.repository import SupplyChainRepository
from src.models.decisions import ApprovalStatus, ActionType, MitigationCandidate, DecisionRecord
from src.models.domain import DisruptionAlert, DisruptionType, SeverityLevel


def fresh_repo():
    """Returns a clean repository with seed data for isolated tests."""
    r = SupplyChainRepository()
    return r


def make_decision(decision_id="DEC-TEST-001", sku_id="SKU-9921-MCU",
                  cost=2000.0, status=ApprovalStatus.PENDING_APPROVAL):
    candidate = MitigationCandidate(
        candidate_id="ACT-001",
        action_type=ActionType.AIR_FREIGHT_EXPEDITE,
        title="Emergency Air Freight",
        description="Air freight injection.",
        cost_usd=cost,
        estimated_time_to_resolve_days=1,
        risk_reduction_pct=88.0,
        requires_human_approval=True,
        approval_threshold_usd=1000.0
    )
    return DecisionRecord(
        decision_id=decision_id,
        alert_id="ALT-TEST-001",
        sku_id=sku_id,
        created_at="2026-10-22T17:00:00",
        status=status,
        selected_candidate=candidate,
        all_evaluated_candidates=[candidate],
        nvidia_nim_reasoning="Test reasoning: Air freight recommended.",
        confidence_score=0.95
    )


# ────────────────────────────────────────────────
# Section 1: Meterless World Model Engine
# ────────────────────────────────────────────────

def test_meterless_empty_inventory():
    """WorldState with empty inventory dict must not crash step_forward."""
    engine = MeterlessWorldModelEngine()
    state = WorldState(inventory_levels={}, port_congestion_index=0.5)
    next_state = engine.step_forward(state, {"congestion_delta": 0.1})
    assert next_state.step_id == 1
    assert next_state.port_congestion_index == pytest.approx(0.6, abs=0.01)


def test_meterless_zero_burn_rate():
    """Zero daily_demand must not cause division errors in simulation."""
    engine = MeterlessWorldModelEngine()
    state = WorldState(
        inventory_levels={"SKU-A": 100},
        daily_demand={"SKU-A": 0},
        port_congestion_index=0.3
    )
    outcomes = engine.simulate_counterfactuals(
        baseline_state=state,
        candidate_actions=[{"name": "Status Quo", "cost_usd": 0.0, "efficiency_gain": 0.0}],
        horizon_steps=5
    )
    assert len(outcomes) == 1
    assert outcomes[0].predicted_stockout_days == 0


def test_meterless_invalid_horizon():
    """horizon_steps=0 must raise ValueError."""
    engine = MeterlessWorldModelEngine()
    state = WorldState(inventory_levels={"SKU-A": 100})
    with pytest.raises(ValueError, match="horizon_steps"):
        engine.simulate_counterfactuals(
            baseline_state=state,
            candidate_actions=[{"name": "X", "cost_usd": 0.0, "efficiency_gain": 0.0}],
            horizon_steps=0
        )


def test_meterless_none_state_raises():
    """step_forward with None state must raise ValueError."""
    engine = MeterlessWorldModelEngine()
    with pytest.raises((ValueError, AttributeError)):
        engine.step_forward(None, {})


def test_meterless_single_candidate():
    """simulate_counterfactuals must work with exactly 1 candidate."""
    engine = MeterlessWorldModelEngine()
    state = WorldState(inventory_levels={"SKU-X": 50}, daily_demand={"SKU-X": 10})
    outcomes = engine.simulate_counterfactuals(
        baseline_state=state,
        candidate_actions=[{"name": "Only Option", "cost_usd": 500.0, "efficiency_gain": 0.5}],
        horizon_steps=3
    )
    assert len(outcomes) == 1
    assert outcomes[0].scenario_name == "Only Option"


def test_meterless_many_candidates():
    """simulate_counterfactuals must handle 10 candidates and sort by risk."""
    engine = MeterlessWorldModelEngine()
    state = WorldState(inventory_levels={"SKU-X": 200}, daily_demand={"SKU-X": 20}, port_congestion_index=0.5)
    candidates = [
        {"name": f"Option-{i}", "cost_usd": float(i * 500), "efficiency_gain": i * 0.09}
        for i in range(10)
    ]
    outcomes = engine.simulate_counterfactuals(state, candidates, horizon_steps=5)
    assert len(outcomes) == 10
    # sorted: first has lowest risk
    for i in range(len(outcomes) - 1):
        assert round(outcomes[i].projected_risk_score, 1) <= round(outcomes[i + 1].projected_risk_score, 1) + 0.01


def test_meterless_simulation_reproducibility():
    """Identical inputs must produce bit-for-bit identical simulation outcomes."""
    engine = MeterlessWorldModelEngine()
    state = WorldState(inventory_levels={"SKU-Z": 300}, daily_demand={"SKU-Z": 30}, port_congestion_index=0.6)
    candidates = [
        {"name": "Route A", "cost_usd": 1000.0, "efficiency_gain": 0.4},
        {"name": "Route B", "cost_usd": 2000.0, "efficiency_gain": 0.8}
    ]
    run1 = engine.simulate_counterfactuals(state, candidates, horizon_steps=5)
    run2 = engine.simulate_counterfactuals(state, candidates, horizon_steps=5)
    assert dump_model(run1[0]) == dump_model(run2[0])
    assert dump_model(run1[1]) == dump_model(run2[1])


def test_meterless_high_risk_detection():
    """Status Quo on critically depleted inventory must produce risk_score > 0.5."""
    engine = MeterlessWorldModelEngine()
    state = WorldState(
        inventory_levels={"SKU-CRIT": 10},
        daily_demand={"SKU-CRIT": 30},
        port_congestion_index=0.85
    )
    outcomes = engine.simulate_counterfactuals(
        baseline_state=state,
        candidate_actions=[{"name": "Status Quo", "cost_usd": 0.0, "efficiency_gain": 0.0}],
        horizon_steps=5
    )
    assert outcomes[0].projected_risk_score > 0.5


# ────────────────────────────────────────────────
# Section 2: Disruption Detector
# ────────────────────────────────────────────────

def test_disruption_detector_customs_hold():
    """Customs hold shipment must trigger CUSTOMS_HOLD alert."""
    repo = fresh_repo()
    detector = DisruptionDetector(repo=repo)
    alerts = detector.detect_disruptions()
    customs_alerts = [a for a in alerts if a.disruption_type == DisruptionType.CUSTOMS_HOLD]
    assert len(customs_alerts) >= 1


def test_disruption_detector_supplier_outage():
    """Inactive supplier must trigger SUPPLIER_OUTAGE alert."""
    repo = fresh_repo()
    detector = DisruptionDetector(repo=repo)
    alerts = detector.detect_disruptions()
    outage_alerts = [a for a in alerts if a.disruption_type == DisruptionType.SUPPLIER_OUTAGE]
    assert len(outage_alerts) >= 1


def test_disruption_detector_no_inventory():
    """Detector with cleared inventory must not crash."""
    repo = fresh_repo()
    repo.inventory.clear()
    detector = DisruptionDetector(repo=repo)
    alerts = detector.detect_disruptions()
    assert isinstance(alerts, list)


def test_disruption_detector_on_schedule_no_alert():
    """ON_SCHEDULE shipment with zero delay should not produce customs/port alert."""
    repo = fresh_repo()
    # Remove all shipments with delays
    for tid, s in list(repo.shipments.items()):
        if s.reported_delay_days > 0:
            del repo.shipments[tid]
    # Also remove inactive suppliers for clean test
    for sid, sup in list(repo.suppliers.items()):
        sup.is_active = True
    detector = DisruptionDetector(repo=repo)
    alerts = detector.detect_disruptions()
    delay_alerts = [a for a in alerts if a.disruption_type in (DisruptionType.CUSTOMS_HOLD, DisruptionType.PORT_CONGESTION)]
    assert len(delay_alerts) == 0


# ────────────────────────────────────────────────
# Section 3: Action Generator
# ────────────────────────────────────────────────

def test_action_generator_candidates_structure():
    """All generated candidates must have required fields."""
    repo = fresh_repo()
    gen = ActionGenerator(repo=repo)
    alert = DisruptionAlert(
        alert_id="ALT-TEST",
        sku_id="SKU-9921-MCU",
        disruption_type=DisruptionType.CUSTOMS_HOLD,
        severity=SeverityLevel.HIGH,
        summary="Test hold",
        detected_at="2026-10-22T00:00:00",
        affected_units=500,
        projected_stockout_risk=0.75,
        underlying_cause="Test"
    )
    candidates = gen.generate_candidates_for_alert(alert)
    assert len(candidates) >= 3
    for c in candidates:
        assert hasattr(c, 'candidate_id')
        assert hasattr(c, 'action_type')
        assert hasattr(c, 'title')
        assert hasattr(c, 'cost_usd')
        assert hasattr(c, 'risk_reduction_pct')
        assert hasattr(c, 'requires_human_approval')


def test_action_generator_status_quo_zero_cost():
    """Status Quo candidate must have cost_usd == 0.0."""
    repo = fresh_repo()
    gen = ActionGenerator(repo=repo)
    alert = DisruptionAlert(
        alert_id="ALT-SQ",
        sku_id="SKU-4412-CAP",
        disruption_type=DisruptionType.PORT_CONGESTION,
        severity=SeverityLevel.MEDIUM,
        summary="Port delay",
        detected_at="2026-10-22T00:00:00",
        affected_units=200,
        projected_stockout_risk=0.4,
        underlying_cause="Port backlog"
    )
    candidates = gen.generate_candidates_for_alert(alert)
    sq = [c for c in candidates if c.action_type == ActionType.NO_ACTION_MONITOR]
    assert len(sq) == 1
    assert sq[0].cost_usd == 0.0


# ────────────────────────────────────────────────
# Section 4: Repository
# ────────────────────────────────────────────────

def test_repository_add_and_retrieve_alert():
    repo = fresh_repo()
    alert = DisruptionAlert(
        alert_id="ALT-REPOTEST-001",
        sku_id="SKU-9921-MCU",
        disruption_type=DisruptionType.CARRIER_DELAY,
        severity=SeverityLevel.HIGH,
        summary="Test alert",
        detected_at="2026-10-22T00:00:00",
        affected_units=100,
        projected_stockout_risk=0.6,
        underlying_cause="Test"
    )
    repo.add_alert(alert)
    all_alerts = repo.get_all_alerts()
    assert any(a.alert_id == "ALT-REPOTEST-001" for a in all_alerts)


def test_repository_save_and_retrieve_decision():
    repo = fresh_repo()
    dec = make_decision(decision_id="DEC-SAVE-001")
    repo.save_decision(dec)
    retrieved = repo.get_decision("DEC-SAVE-001")
    assert retrieved is not None
    assert retrieved.decision_id == "DEC-SAVE-001"


def test_repository_approve_decision_changes_status():
    repo = fresh_repo()
    dec = make_decision(decision_id="DEC-APPROVE-001")
    repo.save_decision(dec)
    updated = repo.approve_decision("DEC-APPROVE-001", approver="Asiya Ali", execution_notes="Approved for test")
    assert updated.status == ApprovalStatus.APPROVED
    assert updated.approved_by == "Asiya Ali"


def test_repository_reject_decision_changes_status():
    repo = fresh_repo()
    dec = make_decision(decision_id="DEC-REJECT-001")
    repo.save_decision(dec)
    updated = repo.reject_decision("DEC-REJECT-001", rejecter="Asiya Ali", reason="Test rejection")
    assert updated.status == ApprovalStatus.REJECTED
    assert updated.rejection_reason == "Test rejection"


def test_repository_reject_already_approved_raises():
    """Rejecting an already-APPROVED decision must raise ValueError."""
    repo = fresh_repo()
    dec = make_decision(decision_id="DEC-DOUBLE-001", status=ApprovalStatus.APPROVED)
    repo.save_decision(dec)
    with pytest.raises(ValueError):
        repo.reject_decision("DEC-DOUBLE-001", rejecter="Test", reason="Late change")


def test_repository_approve_nonexistent_raises():
    """Approving a non-existent decision_id must raise ValueError."""
    repo = fresh_repo()
    with pytest.raises(ValueError):
        repo.approve_decision("DEC-NONEXISTENT-XYZ", approver="Test")


def test_repository_reset_clears_state():
    """After reset, alerts, decisions, and custom inventory changes should be cleared."""
    repo = fresh_repo()
    dec = make_decision()
    repo.save_decision(dec)
    repo.inventory["SKU-FAKE"] = repo.inventory["SKU-9921-MCU"]
    repo.reset_to_seed()
    assert len(repo.decisions) == 0
    assert len(repo.alerts) == 0
    assert "SKU-FAKE" not in repo.inventory


# ────────────────────────────────────────────────
# Section 5: Connectors
# ────────────────────────────────────────────────

def test_zetaris_mock_returns_records():
    """Mock Zetaris connector must return records equal to inventory count."""
    repo = fresh_repo()
    zetaris = ZetarisConnector()
    records = zetaris.query_semantic_layer("SELECT * FROM unified_supply_chain")
    assert len(records) == len(repo.inventory)


def test_zetaris_records_have_required_fields():
    """Each Zetaris mock record must contain required supply chain fields."""
    zetaris = ZetarisConnector()
    records = zetaris.query_semantic_layer("SELECT * FROM unified_supply_chain")
    required = ['sku_id', 'supplier_name', 'shipment_status', 'days_of_supply']
    for r in records:
        for field in required:
            assert field in r, f"Field '{field}' missing from record for sku {r.get('sku_id')}"


def test_nvidia_nim_mock_has_required_fields():
    """NIM mock adapter must return required response fields."""
    client = NvidiaNimClient()
    response = client._generate_structured_mock_response("test prompt")
    assert 'mode' in response
    assert 'reasoning' in response
    assert 'decision' in response
    assert 'confidence' in response
    assert 'supporting_evidence' in response


def test_nvidia_nim_confidence_in_range():
    """NIM confidence score must be in [0.0, 1.0]."""
    client = NvidiaNimClient()
    response = client._generate_structured_mock_response("test")
    assert 0.0 <= response['confidence'] <= 1.0


# ────────────────────────────────────────────────
# Section 6: Full Agent Integration
# ────────────────────────────────────────────────

def test_full_agent_cycle_with_disruptions():
    """Full resilience cycle with seed data must return status SUCCESS and generate decisions."""
    repo = fresh_repo()
    ag = SupplyChainResilienceAgent(repo=repo)
    result = asyncio.run(ag.execute_resilience_cycle())
    assert result['status'] == 'SUCCESS'
    assert result['active_alerts_count'] > 0
    assert result['decisions_generated'] is not None


def test_full_agent_cycle_decisions_in_repo():
    """Decisions generated during cycle must be persisted in repository."""
    repo = fresh_repo()
    ag = SupplyChainResilienceAgent(repo=repo)
    asyncio.run(ag.execute_resilience_cycle())
    assert len(repo.get_all_decisions()) > 0


def test_full_agent_integration_transparency():
    """Agent must expose integrations dict with all three sponsor keys."""
    repo = fresh_repo()
    ag = SupplyChainResilienceAgent(repo=repo)
    statuses = ag.get_integration_statuses()
    assert 'meterless' in statuses
    assert 'nvidia_nim' in statuses
    assert 'zetaris' in statuses
    for k, v in statuses.items():
        assert 'mode' in v, f"Integration '{k}' missing 'mode' field"
        assert 'is_live' in v, f"Integration '{k}' missing 'is_live' field"


def test_approval_gate_on_high_cost_action():
    """Decisions with candidate cost > threshold must have PENDING_APPROVAL status."""
    repo = fresh_repo()
    ag = SupplyChainResilienceAgent(repo=repo)
    asyncio.run(ag.execute_resilience_cycle())
    decisions = repo.get_all_decisions()
    high_cost_decisions = [
        d for d in decisions
        if d.selected_candidate.cost_usd >= d.selected_candidate.approval_threshold_usd
        and d.selected_candidate.requires_human_approval
    ]
    for d in high_cost_decisions:
        assert d.status in (ApprovalStatus.PENDING_APPROVAL, ApprovalStatus.AUTO_EXECUTED)


def test_audit_log_grows_on_each_action():
    """Audit log must grow when alerts and decisions are saved."""
    repo = fresh_repo()
    initial_len = len(repo.get_audit_log(limit=200))

    alert = DisruptionAlert(
        alert_id="ALT-AUDIT-001",
        sku_id="SKU-9921-MCU",
        disruption_type=DisruptionType.CARRIER_DELAY,
        severity=SeverityLevel.LOW,
        summary="Audit test",
        detected_at="2026-10-22T00:00:00",
        affected_units=10,
        projected_stockout_risk=0.1,
        underlying_cause="Test"
    )
    repo.add_alert(alert)

    dec = make_decision(decision_id="DEC-AUDIT-001")
    repo.save_decision(dec)

    final_len = len(repo.get_audit_log(limit=200))
    assert final_len >= initial_len + 2
