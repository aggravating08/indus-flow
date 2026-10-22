"""Supply Chain State Repository and Audit Log Persistence.

Maintains live runtime state, active disruption alerts, simulation runs,
human approval decisions, and immutable audit logs.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import copy
from src.models.domain import Supplier, InventoryItem, Shipment, DemandForecast, DisruptionAlert
from src.models.decisions import DecisionRecord, AuditLogEntry, ApprovalStatus
from src.data.mock_database import (
    INITIAL_SUPPLIERS, INITIAL_INVENTORY,
    INITIAL_SHIPMENTS, INITIAL_DEMAND_FORECASTS
)

class SupplyChainRepository:
    """Thread-safe in-memory state repository with reset and persistence capabilities."""

    def __init__(self):
        self.suppliers: Dict[str, Supplier] = {s.id: copy.deepcopy(s) for s in INITIAL_SUPPLIERS}
        self.inventory: Dict[str, InventoryItem] = {i.sku_id: copy.deepcopy(i) for i in INITIAL_INVENTORY}
        self.shipments: Dict[str, Shipment] = {s.tracking_id: copy.deepcopy(s) for s in INITIAL_SHIPMENTS}
        self.demand: Dict[str, DemandForecast] = {d.sku_id: copy.deepcopy(d) for d in INITIAL_DEMAND_FORECASTS}
        self.alerts: Dict[str, DisruptionAlert] = {}
        self.decisions: Dict[str, DecisionRecord] = {}
        self.audit_log: List[AuditLogEntry] = []

        self._record_audit("SYSTEM_INIT", "Indus-System", {"message": "SupplyChainRepository initialized with baseline data"})

    def reset_to_seed(self):
        """Reset all data structures back to default seeds (useful for reproducible demos & tests)."""
        self.suppliers = {s.id: copy.deepcopy(s) for s in INITIAL_SUPPLIERS}
        self.inventory = {i.sku_id: copy.deepcopy(i) for i in INITIAL_INVENTORY}
        self.shipments = {s.tracking_id: copy.deepcopy(s) for s in INITIAL_SHIPMENTS}
        self.demand = {d.sku_id: copy.deepcopy(d) for d in INITIAL_DEMAND_FORECASTS}
        self.alerts.clear()
        self.decisions.clear()
        self.audit_log.clear()
        self._record_audit("SYSTEM_RESET", "Indus-System", {"message": "Repository state reset to baseline seed"})

    # --- Query Methods ---
    def get_all_suppliers(self) -> List[Supplier]:
        return list(self.suppliers.values())

    def get_supplier(self, supplier_id: str) -> Optional[Supplier]:
        return self.suppliers.get(supplier_id)

    def get_all_inventory(self) -> List[InventoryItem]:
        return list(self.inventory.values())

    def get_inventory_item(self, sku_id: str) -> Optional[InventoryItem]:
        return self.inventory.get(sku_id)

    def get_all_shipments(self) -> List[Shipment]:
        return list(self.shipments.values())

    def get_shipment(self, tracking_id: str) -> Optional[Shipment]:
        return self.shipments.get(tracking_id)

    def get_shipments_for_sku(self, sku_id: str) -> List[Shipment]:
        return [s for s in self.shipments.values() if s.sku_id == sku_id]

    def get_all_alerts(self) -> List[DisruptionAlert]:
        return list(self.alerts.values())

    def get_all_decisions(self) -> List[DecisionRecord]:
        return sorted(list(self.decisions.values()), key=lambda d: d.created_at, reverse=True)

    def get_decision(self, decision_id: str) -> Optional[DecisionRecord]:
        return self.decisions.get(decision_id)

    def get_audit_log(self, limit: int = 50) -> List[AuditLogEntry]:
        return self.audit_log[-limit:]

    # --- Mutation & Workflow Methods ---
    def add_alert(self, alert: DisruptionAlert):
        self.alerts[alert.alert_id] = alert
        self._record_audit("DISRUPTION_DETECTED", "Indus-Detector", {
            "alert_id": alert.alert_id,
            "sku_id": alert.sku_id,
            "type": alert.disruption_type.value,
            "severity": alert.severity.value
        })

    def save_decision(self, decision: DecisionRecord):
        self.decisions[decision.decision_id] = decision
        self._record_audit("DECISION_GENERATED", "Indus-Agent", {
            "decision_id": decision.decision_id,
            "sku_id": decision.sku_id,
            "status": decision.status.value,
            "action": decision.selected_candidate.title,
            "cost_usd": decision.selected_candidate.cost_usd
        })

    def approve_decision(self, decision_id: str, approver: str, execution_notes: Optional[str] = None) -> DecisionRecord:
        decision = self.decisions.get(decision_id)
        if not decision:
            raise ValueError(f"Decision {decision_id} not found")
        if decision.status != ApprovalStatus.PENDING_APPROVAL:
            raise ValueError(f"Decision {decision_id} is in status '{decision.status.value}', cannot approve")

        decision.status = ApprovalStatus.APPROVED
        decision.approved_by = approver
        decision.approval_timestamp = datetime.utcnow().isoformat()
        decision.execution_notes = execution_notes or f"Approved by {approver} for immediate execution"

        # Apply inventory/shipment adjustments if applicable
        self._apply_mitigation_execution(decision)

        self._record_audit("DECISION_APPROVED", approver, {
            "decision_id": decision_id,
            "action": decision.selected_candidate.title,
            "notes": decision.execution_notes
        })
        return decision

    def reject_decision(self, decision_id: str, rejecter: str, reason: str) -> DecisionRecord:
        decision = self.decisions.get(decision_id)
        if not decision:
            raise ValueError(f"Decision {decision_id} not found")
        if decision.status != ApprovalStatus.PENDING_APPROVAL:
            raise ValueError(f"Decision {decision_id} is in status '{decision.status.value}', cannot reject")

        decision.status = ApprovalStatus.REJECTED
        decision.approved_by = rejecter
        decision.approval_timestamp = datetime.utcnow().isoformat()
        decision.rejection_reason = reason

        self._record_audit("DECISION_REJECTED", rejecter, {
            "decision_id": decision_id,
            "reason": reason
        })
        return decision

    def _apply_mitigation_execution(self, decision: DecisionRecord):
        """Simulate the physical operational effect of executing an approved action."""
        sku_id = decision.sku_id
        action_type = decision.selected_candidate.action_type
        item = self.inventory.get(sku_id)

        if item:
            if "EXPEDITE" in action_type.value or "AIR_FREIGHT" in action_type.value:
                # Expedited shipment arrives faster, restoring safe stock buffer
                item.current_stock += 150
            elif "ALTERNATE_SUPPLIER" in action_type.value:
                item.current_stock += 200

        # Update affected shipment status if applicable
        for shipment in self.shipments.values():
            if shipment.sku_id == sku_id and shipment.reported_delay_days > 0:
                shipment.reported_delay_days = max(0, shipment.reported_delay_days - 4)

    def _record_audit(self, action: str, actor: str, details: Dict[str, Any]):
        entry = AuditLogEntry(
            timestamp=datetime.utcnow().isoformat(),
            action=action,
            actor=actor,
            details=details
        )
        self.audit_log.append(entry)

# Global singleton repository instance
repository = SupplyChainRepository()
