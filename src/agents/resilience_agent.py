"""Indus Flow Master Autonomous Resilience Agent.

Coordinates:
1. Ingestion via Zetaris Cloud Gateway / Semantic Layer
2. Disruption detection across inventory, carriers, and suppliers
3. Multi-branch counterfactual simulation via Meterless World Model Engine
4. Structured trade-off analysis & policy synthesis via NVIDIA NIM
5. Human-in-the-loop approval gating for consequential actions
6. State persistence and audit logging
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from src.engines.world_model import (
    MeterlessWorldModelEngine, WorldState, SimulationOutcome,
    dump_model, dump_model_json
)
from src.connectors.zetaris_connector import ZetarisConnector
from src.connectors.nvidia_nim import NvidiaNimClient
from src.agents.disruption_detector import DisruptionDetector
from src.agents.action_generator import ActionGenerator
from src.models.decisions import DecisionRecord, ApprovalStatus
from src.data.repository import repository
from src.config import settings

class SupplyChainResilienceAgent:
    """Master autonomous orchestrator for supply chain resilience."""

    def __init__(self, repo=None):
        self.repo = repo or repository
        self.world_model = MeterlessWorldModelEngine(
            api_key=settings.meterless_api_key,
            endpoint=settings.meterless_endpoint
        )
        self.zetaris = ZetarisConnector(
            host=settings.zetaris_host,
            port=settings.zetaris_port,
            user=settings.zetaris_user,
            password=settings.zetaris_password
        )
        self.nvidia = NvidiaNimClient(
            api_key=settings.nvidia_api_key,
            base_url=settings.nvidia_base_url,
            model=settings.nvidia_model
        )
        self.detector = DisruptionDetector(repo=self.repo)
        self.action_generator = ActionGenerator(repo=self.repo)

    async def execute_resilience_cycle(self) -> Dict[str, Any]:
        """Executes full autonomous cycle: Sense -> Detect -> Simulate -> Decide -> Gate -> Persist."""
        # 1. Sense: Query Zetaris Semantic Data Layer
        semantic_records = self.zetaris.query_semantic_layer(
            "SELECT * FROM virtual_supply_chain_catalog WHERE shipment_status != 'DELIVERED'"
        )

        # 2. Detect Disruptions
        alerts = self.detector.detect_disruptions()
        for alert in alerts:
            self.repo.add_alert(alert)

        new_decisions: List[DecisionRecord] = []

        # If no alerts detected, create a baseline proactive health check
        if not alerts:
            return {
                "status": "HEALTHY",
                "message": "All supply chain nodes operating within normal parameters. Zero stockout risks detected.",
                "semantic_records_evaluated": len(semantic_records),
                "active_alerts_count": 0,
                "decisions_generated": [],
                "integrations": self.get_integration_statuses()
            }

        # 3. Process each alert through Meterless World Model & NVIDIA NIM
        for alert in alerts:
            item = self.repo.get_inventory_item(alert.sku_id)
            shipments = self.repo.get_shipments_for_sku(alert.sku_id)
            reported_delay = shipments[0].reported_delay_days if shipments else 0

            # Construct World State for simulation
            current_stock = item.current_stock if item else 100
            daily_burn = item.daily_burn_rate if item else 20
            baseline_state = WorldState(
                inventory_levels={alert.sku_id: current_stock},
                daily_demand={alert.sku_id: daily_burn},
                port_congestion_index=0.70 if "PORT" in alert.disruption_type.value or "CUSTOMS" in alert.disruption_type.value else 0.30,
                carrier_delays_days={alert.sku_id: float(reported_delay)}
            )

            # Generate Candidate Mitigation Actions
            candidates = self.action_generator.generate_candidates_for_alert(alert)

            # Format candidate actions for Meterless World Model
            meterless_actions = []
            for c in candidates:
                meterless_actions.append({
                    "name": c.title,
                    "cost_usd": c.cost_usd,
                    "efficiency_gain": c.risk_reduction_pct / 100.0,
                    "immediate_stock_injection": 150 if "AIR_FREIGHT" in c.action_type.value else 0
                })

            # Run Multi-Branch Simulations
            simulations: List[SimulationOutcome] = self.world_model.simulate_counterfactuals(
                baseline_state=baseline_state,
                candidate_actions=meterless_actions,
                horizon_steps=7
            )

            # Map the optimal simulation outcome back to candidate
            best_sim = simulations[0]
            best_candidate = next(
                (c for c in candidates if c.title == best_sim.scenario_name),
                candidates[1]  # fallback to first mitigation candidate
            )

            # Generate NVIDIA NIM Decision Reasoning
            nim_prompt = (
                f"Disruption detected for SKU {alert.sku_id}: {alert.summary}. "
                f"Cause: {alert.underlying_cause}. "
                f"Meterless World Model evaluated {len(simulations)} simulation branches. "
                f"Top ranked scenario: {best_sim.scenario_name} with risk score {best_sim.projected_risk_score} "
                f"and {best_sim.predicted_stockout_days} stockout days. "
                f"Cost: ${best_candidate.cost_usd}. "
                f"Provide executive recommendation, cost-benefit rationale, and operational risk appraisal."
            )
            nim_response = await self.nvidia.generate_reasoning_trace(nim_prompt)

            # Determine Human Approval Requirement
            # If cost > $1,000 or significant operational change, require human confirmation
            needs_approval = best_candidate.requires_human_approval and (best_candidate.cost_usd >= best_candidate.approval_threshold_usd)
            initial_status = ApprovalStatus.PENDING_APPROVAL if needs_approval else ApprovalStatus.AUTO_EXECUTED

            decision_id = f"DEC-{alert.sku_id[:8]}-{datetime.utcnow().strftime('%M%S')}"
            decision_record = DecisionRecord(
                decision_id=decision_id,
                alert_id=alert.alert_id,
                sku_id=alert.sku_id,
                created_at=datetime.utcnow().isoformat(),
                status=initial_status,
                selected_candidate=best_candidate,
                all_evaluated_candidates=candidates,
                meterless_simulation_ref={
                    "engine": self.world_model.engine_name,
                    "mode": self.world_model.mode,
                    "optimal_scenario": dump_model(best_sim),
                    "all_scenarios": [dump_model(s) for s in simulations]
                },
                nvidia_nim_reasoning=nim_response.get("reasoning", ""),
                confidence_score=nim_response.get("confidence", 0.94),
                execution_notes="Awaiting operator confirmation" if needs_approval else "Auto-executed within pre-approved micro-budget"
            )

            self.repo.save_decision(decision_record)
            new_decisions.append(decision_record)

        return {
            "status": "SUCCESS",
            "semantic_records_evaluated": len(semantic_records),
            "active_alerts_count": len(alerts),
            "decisions_generated": [dump_model(d) for d in new_decisions],
            "pending_approvals_count": sum(1 for d in new_decisions if d.status == ApprovalStatus.PENDING_APPROVAL),
            "integrations": self.get_integration_statuses()
        }

    def get_integration_statuses(self) -> Dict[str, Any]:
        """Transparent disclosure of integration modes across all sponsors."""
        return {
            "meterless": {
                "sponsor": "Meterless",
                "engine": self.world_model.engine_name,
                "mode": self.world_model.mode,
                "endpoint": self.world_model.endpoint,
                "is_live": self.world_model.mode == "LIVE_METERLESS_API"
            },
            "nvidia_nim": {
                "sponsor": "NVIDIA",
                "model": self.nvidia.model,
                "mode": self.nvidia.mode,
                "is_live": self.nvidia.is_live
            },
            "zetaris": {
                "sponsor": "Zetaris",
                "mode": self.zetaris.mode,
                "catalog": "Virtual Unified Supply Catalog",
                "is_live": self.zetaris.is_live
            }
        }
