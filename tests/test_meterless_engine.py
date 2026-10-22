"""Automated Test Suite for Meterless Agent Engine & Agent Orchestration.

Demonstrates working execution and passing test verification as required by
the Open Agent Hackathon 2026 rules.
"""

import asyncio
from src.engines.world_model import MeterlessWorldModelEngine, WorldState
from src.agents.resilience_agent import SupplyChainResilienceAgent

def test_meterless_world_model_step_evolution():
    """Verify single-step dynamic state evolution under external perturbation."""
    engine = MeterlessWorldModelEngine()
    initial_state = WorldState(
        step_id=0,
        inventory_levels={"SKU-100": 500},
        port_congestion_index=0.2
    )

    perturbation = {
        "delayed_sku": "SKU-100",
        "days": 4,
        "daily_burn": 50,
        "congestion_delta": 0.3
    }

    next_state = engine.step_forward(initial_state, perturbation)

    assert next_state.step_id == 1
    assert next_state.port_congestion_index == 0.5
    # Initial 500 - (4 * 50) = 300
    assert next_state.inventory_levels["SKU-100"] == 300
    assert next_state.carrier_delays_days["SKU-100"] == 4.0

def test_meterless_world_model_counterfactual_simulation():
    """Verify multi-branch simulation and risk scoring across mitigation policies."""
    engine = MeterlessWorldModelEngine()
    baseline = WorldState(
        inventory_levels={"SKU-TEST": 60},
        port_congestion_index=0.8
    )

    candidate_actions = [
        {"name": "Do Nothing", "cost_usd": 0.0, "efficiency_gain": 0.0},
        {"name": "Air Freight Expedited", "cost_usd": 2500.0, "efficiency_gain": 0.90}
    ]

    outcomes = engine.simulate_counterfactuals(
        baseline_state=baseline,
        candidate_actions=candidate_actions,
        horizon_steps=4
    )

    assert len(outcomes) == 2
    # The optimal action should be ranked first with lowest projected risk score
    best_outcome = outcomes[0]
    assert best_outcome.scenario_name == "Air Freight Expedited"
    assert best_outcome.projected_risk_score < outcomes[1].projected_risk_score
    assert len(best_outcome.confidence_interval) == 2

def test_full_agent_resilience_cycle():
    """Verify end-to-end agent cycle: Zetaris Query -> Meterless Simulation -> NIM Decision."""
    agent = SupplyChainResilienceAgent()
    result = asyncio.run(agent.execute_resilience_cycle())

    assert result["status"] == "SUCCESS"
    assert "critical_sku" in result
    assert result["zetaris_records_evaluated"] > 0
    assert len(result["simulations_evaluated"]) == 3
    assert result["optimal_strategy"]["projected_risk_score"] <= 0.3
    assert result["optimal_strategy"]["scenario_name"] in [
        "Re-route to Port of Seattle",
        "Expedite Air Freight Contingency"
    ]
    assert "nvidia_nim_reasoning" in result
