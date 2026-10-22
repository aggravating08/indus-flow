"""Decision, Human Approval, and Audit Trail Data Models."""

from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field

class ApprovalStatus(str, Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    AUTO_EXECUTED = "AUTO_EXECUTED"

class ActionType(str, Enum):
    AIR_FREIGHT_EXPEDITE = "AIR_FREIGHT_EXPEDITE"
    PORT_REROUTE = "PORT_REROUTE"
    ALTERNATE_SUPPLIER_PO = "ALTERNATE_SUPPLIER_PO"
    INVENTORY_RATIONING = "INVENTORY_RATIONING"
    NO_ACTION_MONITOR = "NO_ACTION_MONITOR"

class MitigationCandidate(BaseModel):
    candidate_id: str
    action_type: ActionType
    title: str
    description: str
    cost_usd: float
    estimated_time_to_resolve_days: int
    risk_reduction_pct: float
    requires_human_approval: bool = True
    approval_threshold_usd: float = 1000.0

class DecisionRecord(BaseModel):
    decision_id: str
    alert_id: str
    sku_id: str
    created_at: str
    status: ApprovalStatus
    selected_candidate: MitigationCandidate
    all_evaluated_candidates: List[MitigationCandidate] = Field(default_factory=list)
    meterless_simulation_ref: Dict[str, Any] = Field(default_factory=dict)
    nvidia_nim_reasoning: str
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.92)
    approved_by: Optional[str] = None
    approval_timestamp: Optional[str] = None
    rejection_reason: Optional[str] = None
    execution_notes: Optional[str] = None

class AuditLogEntry(BaseModel):
    timestamp: str
    action: str
    actor: str  # "Indus-Agent" or user name
    details: Dict[str, Any]
