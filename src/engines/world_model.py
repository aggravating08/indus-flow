"""Meterless World Model Agent Engine Integration.

The World Model engine simulates dynamic multi-step environment rollouts,
enabling the agent to perform counterfactual reasoning and evaluate risk before
committing execution actions.

Provides:
- Validated state input and trajectory evolution
- Multi-step horizon rollouts with step-by-step time series
- Counterfactual scenario evaluation across diverse interventions
- Reproducible deterministic simulations
"""

from typing import Dict, Any, List, Optional
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
    port_congestion_index: float = Field(default=0.2, ge=0.0, le=1.0)
    carrier_delays_days: Dict[str, float] = Field(default_factory=dict)
    daily_demand: Dict[str, int] = Field(default_factory=dict)
    lead_time_days: int = 7
    cost_penalty_usd: float = 0.0

class StepTrajectory(BaseModel):
    step: int
    inventory_levels: Dict[str, int]
    port_congestion: float
    stockouts_detected: List[str]

class SimulationOutcome(BaseModel):
    scenario_name: str
    projected_risk_score: float  # 0.0 (safe) to 1.0 (catastrophic failure)
    predicted_stockout_days: int
    estimated_mitigation_cost: float
    recommended_action: str
    confidence_interval: List[float]
    trajectory: List[StepTrajectory] = Field(default_factory=list)

class MeterlessWorldModelEngine:
    """Implementation wrapper for Meterless World Model Engine."""

    def __init__(self, api_key: str = "", endpoint: str = "https://api.meterless.ai/v1"):
        self.api_key = api_key
        self.endpoint = endpoint
        self.engine_name = "world-model"
        is_live_key = bool(api_key) and "mock" not in api_key.lower() and "token_here" not in api_key.lower()
        self.mode = "LIVE_METERLESS_API" if is_live_key else "LOCAL_METERLESS_WORLD_MODEL_ENGINE"

    def step_forward(self, current_state: WorldState, perturbation: Dict[str, Any]) -> WorldState:
        """Simulate single-step deterministic state evolution with input validation."""
        if current_state is None:
            raise ValueError("current_state cannot be None")

        new_state = copy_model(current_state)
        new_state.step_id += 1

        # Apply perturbation shock (e.g., port strike or supplier factory downtime)
        if "congestion_delta" in perturbation:
            delta = float(perturbation["congestion_delta"])
            new_state.port_congestion_index = min(1.0, max(0.0, new_state.port_congestion_index + delta))

        if "delayed_sku" in perturbation:
            sku = str(perturbation["delayed_sku"])
            delay = float(perturbation.get("days", 3.0))
            new_state.carrier_delays_days[sku] = new_state.carrier_delays_days.get(sku, 0.0) + delay

            # Decrement inventory by demand during delayed lead-time
            daily_burn = int(perturbation.get("daily_burn", new_state.daily_demand.get(sku, 25)))
            current_inv = new_state.inventory_levels.get(sku, 100)
            new_state.inventory_levels[sku] = max(0, current_inv - int(delay * daily_burn))

        return new_state

    def simulate_counterfactuals(
        self,
        baseline_state: WorldState,
        candidate_actions: List[Dict[str, Any]],
        horizon_steps: int = 5
    ) -> List[SimulationOutcome]:
        """Runs multi-branch rollout simulations across candidate mitigation strategies.

        Evaluates step-by-step state trajectories, calculates risk curves, and ranks policies.
        """
        if baseline_state is None:
            raise ValueError("baseline_state cannot be None")
        if not candidate_actions:
            raise ValueError("candidate_actions cannot be empty")
        if horizon_steps <= 0:
            raise ValueError("horizon_steps must be greater than zero")

        outcomes = []

        for action in candidate_actions:
            action_name = action.get("name", "Unnamed Action")
            state_cursor = copy_model(baseline_state)

            cost = float(action.get("cost_usd", 0.0))
            reroute_efficiency = float(action.get("efficiency_gain", 0.0))
            inventory_injection = int(action.get("immediate_stock_injection", 0))

            # Apply immediate action injection (e.g., air freight arrival)
            for sku in state_cursor.inventory_levels:
                state_cursor.inventory_levels[sku] += inventory_injection

            trajectory: List[StepTrajectory] = []
            total_stockout_days = 0

            for step in range(1, horizon_steps + 1):
                # Congestion decay or mitigation factor
                decayed_congestion = max(0.05, state_cursor.port_congestion_index * (1.0 - reroute_efficiency))
                state_cursor.port_congestion_index = round(decayed_congestion, 3)

                step_stockouts = []
                for sku, inv in list(state_cursor.inventory_levels.items()):
                    daily_burn = state_cursor.daily_demand.get(sku, 20)
                    if inv <= 0:
                        step_stockouts.append(sku)
                        total_stockout_days += 1
                    else:
                        state_cursor.inventory_levels[sku] = max(0, inv - daily_burn)

                trajectory.append(
                    StepTrajectory(
                        step=step,
                        inventory_levels=copy.deepcopy(state_cursor.inventory_levels),
                        port_congestion=state_cursor.port_congestion_index,
                        stockouts_detected=step_stockouts
                    )
                )

            # Calculate composite risk score (0.0 = zero risk, 1.0 = total stockout failure)
            # Weighted by stockout days and residual congestion
            risk_score = min(1.0, (total_stockout_days * 0.20) + (state_cursor.port_congestion_index * 0.35))
            risk_score = max(0.02, risk_score)  # baseline residual uncertainty

            outcomes.append(
                SimulationOutcome(
                    scenario_name=action_name,
                    projected_risk_score=round(risk_score, 3),
                    predicted_stockout_days=total_stockout_days,
                    estimated_mitigation_cost=cost,
                    recommended_action=f"Execute {action_name}" if risk_score < 0.35 else f"Review {action_name}",
                    confidence_interval=[
                        round(max(0.0, risk_score - 0.04), 3),
                        round(min(1.0, risk_score + 0.04), 3)
                    ],
                    trajectory=trajectory
                )
            )

        # Sort: lowest risk first; if risk is within 0.05 tolerance, prefer lower cost
        outcomes.sort(key=lambda x: (round(x.projected_risk_score, 1), x.estimated_mitigation_cost))
        return outcomes
