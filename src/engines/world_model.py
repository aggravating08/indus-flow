"""Meterless World Model Agent Engine Integration.

The World Model engine simulates dynamic multi-step environment rollouts,
enabling the agent to perform counterfactual reasoning and evaluate risk before
committing execution actions.
"""

from typing import Dict, Any, List
import copy
from pydantic import BaseModel, Field

def copy_model(model_inst):
    if hasattr(model_inst, "model_copy"):
        return model_inst.model_copy(deep=True)
    return model_inst.copy(deep=True)

def dump_model(model_inst):
    if hasattr(model_inst, "model_dump"):
        return model_inst.model_dump()
    return model_inst.dict()

def dump_model_json(model_inst):
    if hasattr(model_inst, "model_dump_json"):
        return model_inst.model_dump_json()
    return model_inst.json()

class WorldState(BaseModel):
    step_id: int = 0
    inventory_levels: Dict[str, int] = Field(default_factory=dict)
    port_congestion_index: float = Field(default=0.2)
    carrier_delays_days: Dict[str, float] = Field(default_factory=dict)
    lead_time_days: int = 7
    cost_penalty_usd: float = 0.0

class SimulationOutcome(BaseModel):
    scenario_name: str
    projected_risk_score: float  # 0.0 to 1.0 (1.0 = catastrophic stockout)
    predicted_stockout_days: int
    estimated_mitigation_cost: float
    recommended_action: str
    confidence_interval: List[float]

class MeterlessWorldModelEngine:
    """Implementation wrapper for Meterless World Model Engine."""

    def __init__(self, api_key: str = "", endpoint: str = "https://api.meterless.ai/v1"):
        self.api_key = api_key
        self.endpoint = endpoint
        self.engine_name = "world-model"

    def step_forward(self, current_state: WorldState, perturbation: Dict[str, Any]) -> WorldState:
        """Simulate single-step deterministic state evolution."""
        new_state = copy_model(current_state)
        new_state.step_id += 1

        # Apply perturbation shock (e.g., port strike or supplier factory downtime)
        if "congestion_delta" in perturbation:
            new_state.port_congestion_index = min(1.0, max(0.0, new_state.port_congestion_index + perturbation["congestion_delta"]))

        if "delayed_sku" in perturbation:
            sku = perturbation["delayed_sku"]
            delay = perturbation.get("days", 3)
            new_state.carrier_delays_days[sku] = new_state.carrier_delays_days.get(sku, 0.0) + delay

            # Decrement inventory by demand during delayed lead-time
            daily_burn = perturbation.get("daily_burn", 25)
            current_inv = new_state.inventory_levels.get(sku, 100)
            new_state.inventory_levels[sku] = max(0, current_inv - int(delay * daily_burn))

        return new_state

    def simulate_counterfactuals(
        self,
        baseline_state: WorldState,
        candidate_actions: List[Dict[str, Any]],
        horizon_steps: int = 5
    ) -> List[SimulationOutcome]:
        """Runs multi-branch rollout simulations across candidate mitigation strategies."""
        outcomes = []

        for action in candidate_actions:
            action_name = action.get("name", "Unnamed Action")
            state_cursor = copy_model(baseline_state)

            # Apply candidate action effects
            cost = action.get("cost_usd", 0.0)
            reroute_efficiency = action.get("efficiency_gain", 0.0)

            total_stockout_days = 0
            for step in range(horizon_steps):
                # Step simulation with baseline port congestion decayed by mitigation
                decayed_congestion = max(0.05, state_cursor.port_congestion_index * (1.0 - reroute_efficiency))
                state_cursor.port_congestion_index = decayed_congestion

                for sku, inv in list(state_cursor.inventory_levels.items()):
                    daily_burn = 20
                    if inv <= 0:
                        total_stockout_days += 1
                    else:
                        state_cursor.inventory_levels[sku] = max(0, inv - daily_burn)

            # Calculate composite risk score
            risk_score = min(1.0, (total_stockout_days * 0.25) + (state_cursor.port_congestion_index * 0.3))

            outcomes.append(
                SimulationOutcome(
                    scenario_name=action_name,
                    projected_risk_score=round(risk_score, 3),
                    predicted_stockout_days=total_stockout_days,
                    estimated_mitigation_cost=cost,
                    recommended_action=f"Execute {action_name}" if risk_score < 0.4 else f"Escalate {action_name}",
                    confidence_interval=[round(max(0.0, risk_score - 0.05), 3), round(min(1.0, risk_score + 0.05), 3)]
                )
            )

        # Sort by lowest risk score first
        outcomes.sort(key=lambda x: (x.projected_risk_score, x.estimated_mitigation_cost))
        return outcomes
