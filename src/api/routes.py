"""REST API Routes for Indus Flow Autonomous Resilience Agent."""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from src.data.repository import repository
from src.agents.resilience_agent import SupplyChainResilienceAgent
from src.engines.world_model import WorldState, dump_model
from src.config import settings

router = APIRouter()
agent = SupplyChainResilienceAgent()

class ApprovalRequest(BaseModel):
    approver: str = Field(default="Asiya Ali (Operations Lead)")
    notes: Optional[str] = Field(default="Approved for operational deployment")

class RejectionRequest(BaseModel):
    rejecter: str = Field(default="Asiya Ali (Operations Lead)")
    reason: str = Field(default="Cost exceeds acceptable tolerance; explore alternate rail route")

class CustomSimulationRequest(BaseModel):
    sku_id: str = "SKU-9921-MCU"
    initial_stock: int = 140
    daily_demand: int = 25
    port_congestion: float = 0.70
    horizon_steps: int = 7
    candidate_actions: Optional[List[Dict[str, Any]]] = None

@router.get("/overview")
def get_supply_chain_overview():
    """Returns high-level KPI dashboard metrics."""
    inventory = repository.get_all_inventory()
    shipments = repository.get_all_shipments()
    alerts = repository.get_all_alerts()
    decisions = repository.get_all_decisions()

    critical_items = [i for i in inventory if i.current_stock <= i.safety_stock]
    delayed_shipments = [s for s in shipments if s.reported_delay_days > 0]
    pending_approvals = [d for d in decisions if d.status.value == "PENDING_APPROVAL"]

    return {
        "system_status": "MONITORING_ACTIVE",
        "team": "Indus",
        "project": "Indus Flow",
        "metrics": {
            "total_skus_tracked": len(inventory),
            "critical_stock_count": len(critical_items),
            "total_shipments": len(shipments),
            "delayed_shipments_count": len(delayed_shipments),
            "active_alerts_count": len(alerts),
            "pending_approvals_count": len(pending_approvals),
            "total_decisions_logged": len(decisions)
        },
        "integrations": agent.get_integration_statuses()
    }

@router.get("/suppliers")
def get_suppliers():
    return [dump_model(s) for s in repository.get_all_suppliers()]

@router.get("/inventory")
def get_inventory():
    return [dump_model(i) for i in repository.get_all_inventory()]

@router.get("/shipments")
def get_shipments():
    return [dump_model(s) for s in repository.get_all_shipments()]

@router.get("/alerts")
def get_alerts():
    return [dump_model(a) for a in repository.get_all_alerts()]

@router.get("/decisions")
def get_decisions():
    return [dump_model(d) for d in repository.get_all_decisions()]

@router.get("/decisions/{decision_id}")
def get_decision_detail(decision_id: str):
    decision = repository.get_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision record not found")
    return dump_model(decision)

@router.post("/decisions/{decision_id}/approve")
def approve_decision(decision_id: str, request: ApprovalRequest = Body(...)):
    """Human approval gate for high-consequence mitigation actions."""
    try:
        updated = repository.approve_decision(
            decision_id=decision_id,
            approver=request.approver,
            execution_notes=request.notes
        )
        return {"status": "SUCCESS", "decision": dump_model(updated)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/decisions/{decision_id}/reject")
def reject_decision(decision_id: str, request: RejectionRequest = Body(...)):
    """Human rejection gate with audit reasoning."""
    try:
        updated = repository.reject_decision(
            decision_id=decision_id,
            rejecter=request.rejecter,
            reason=request.reason
        )
        return {"status": "SUCCESS", "decision": dump_model(updated)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/agent/run")
async def run_autonomous_cycle():
    """Trigger complete sense-simulate-decide-gate autonomous loop."""
    try:
        result = await agent.execute_resilience_cycle()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autonomous cycle failed: {str(e)}")

@router.post("/simulation/simulate")
def run_custom_simulation(request: CustomSimulationRequest):
    """Direct invocation of Meterless World Model engine for scenario planning."""
    state = WorldState(
        inventory_levels={request.sku_id: request.initial_stock},
        daily_demand={request.sku_id: request.daily_demand},
        port_congestion_index=request.port_congestion
    )

    actions = request.candidate_actions or [
        {"name": "Status Quo", "cost_usd": 0.0, "efficiency_gain": 0.0, "immediate_stock_injection": 0},
        {"name": "Intermodal Port Diversion", "cost_usd": 1200.0, "efficiency_gain": 0.55, "immediate_stock_injection": 0},
        {"name": "Emergency Air Freight", "cost_usd": 3200.0, "efficiency_gain": 0.88, "immediate_stock_injection": 150}
    ]

    outcomes = agent.world_model.simulate_counterfactuals(
        baseline_state=state,
        candidate_actions=actions,
        horizon_steps=request.horizon_steps
    )

    return {
        "engine": agent.world_model.engine_name,
        "mode": agent.world_model.mode,
        "horizon_steps": request.horizon_steps,
        "baseline_state": dump_model(state),
        "outcomes": [dump_model(o) for o in outcomes]
    }

@router.get("/audit-log")
def get_audit_log(limit: int = 50):
    return [dump_model(a) for a in repository.get_audit_log(limit=limit)]

@router.post("/reset")
def reset_system_state():
    """Reset repository back to clean seed data."""
    repository.reset_to_seed()
    return {"status": "SUCCESS", "message": "Repository reset to clean baseline seed"}
