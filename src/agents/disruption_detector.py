"""Automated Supply Chain Disruption Detection Engine.

Scans inventory levels, shipment telemetry, carrier delays, and supplier statuses
to detect emerging bottlenecks and risk conditions before stockouts occur.
"""

from typing import List, Dict, Any
from datetime import datetime
from src.models.domain import (
    DisruptionAlert, DisruptionType, SeverityLevel, ShipmentStatus,
    InventoryItem, Shipment, Supplier
)
from src.data.repository import repository

class DisruptionDetector:
    """Evaluates supply chain health signals and produces structured disruption alerts."""

    def __init__(self, repo=None):
        self.repo = repo or repository

    def detect_disruptions(self) -> List[DisruptionAlert]:
        """Runs rule-based and predictive anomaly detection across current operational state."""
        alerts = []

        inventory_items = self.repo.get_all_inventory()
        shipments = self.repo.get_all_shipments()
        suppliers = {s.id: s for s in self.repo.get_all_suppliers()}

        for item in inventory_items:
            sku_id = item.sku_id
            sku_shipments = [s for s in shipments if s.sku_id == sku_id]

            # 1. Check for Active Shipment Delays or Holds
            for shipment in sku_shipments:
                if shipment.status in (ShipmentStatus.CUSTOMS_HOLD, ShipmentStatus.PORT_BOTTLENECK, ShipmentStatus.WEATHER_DELAY) or shipment.reported_delay_days > 2:
                    supplier = suppliers.get(shipment.supplier_id)
                    supplier_name = supplier.name if supplier else "Unknown"

                    # Calculate if delay breaches buffer
                    burn_during_delay = item.daily_burn_rate * shipment.reported_delay_days
                    projected_stock = item.current_stock - burn_during_delay
                    is_critical = projected_stock < item.safety_stock

                    alert_type = DisruptionType.CUSTOMS_HOLD if shipment.status == ShipmentStatus.CUSTOMS_HOLD else DisruptionType.PORT_CONGESTION
                    severity = SeverityLevel.CRITICAL if projected_stock <= 0 else (SeverityLevel.HIGH if is_critical else SeverityLevel.MEDIUM)

                    risk_score = round(min(1.0, max(0.1, (item.safety_stock - projected_stock) / max(1, item.safety_stock))), 2)

                    alert = DisruptionAlert(
                        alert_id=f"ALT-{sku_id[:8]}-{shipment.tracking_id[-4:]}",
                        sku_id=sku_id,
                        disruption_type=alert_type,
                        severity=severity,
                        summary=f"{shipment.status.value.replace('_', ' ')} detected on shipment {shipment.tracking_id} ({shipment.units} units)",
                        detected_at=datetime.utcnow().isoformat(),
                        affected_units=shipment.units,
                        projected_stockout_risk=risk_score,
                        underlying_cause=(
                            f"Shipment {shipment.tracking_id} delayed by {shipment.reported_delay_days} days "
                            f"at {shipment.destination_port}. Inventory buffer of {item.current_stock} units "
                            f"will deplete in {item.days_of_supply} days at {item.daily_burn_rate}/day burn rate."
                        )
                    )
                    alerts.append(alert)

            # 2. Check for Low Stock / Imminent Stockout without incoming shipments
            if item.current_stock <= item.safety_stock and not sku_shipments:
                alert = DisruptionAlert(
                    alert_id=f"ALT-LOWSTOCK-{sku_id[:8]}",
                    sku_id=sku_id,
                    disruption_type=DisruptionType.CARRIER_DELAY,
                    severity=SeverityLevel.HIGH,
                    summary=f"Critical buffer deficit on {item.name}: Current stock {item.current_stock} < Safety {item.safety_stock}",
                    detected_at=datetime.utcnow().isoformat(),
                    affected_units=item.safety_stock - item.current_stock,
                    projected_stockout_risk=0.85,
                    underlying_cause=f"No replenishment shipments scheduled. Days of supply: {item.days_of_supply}."
                )
                alerts.append(alert)

            # 3. Check for Supplier Outages (via shipment link)
            for shipment in sku_shipments:
                supplier = suppliers.get(shipment.supplier_id)
                if supplier and not supplier.is_active:
                    alert = DisruptionAlert(
                        alert_id=f"ALT-SUPOUT-{sku_id[:8]}",
                        sku_id=sku_id,
                        disruption_type=DisruptionType.SUPPLIER_OUTAGE,
                        severity=SeverityLevel.CRITICAL,
                        summary=f"Primary supplier {supplier.name} is offline/inactive",
                        detected_at=datetime.utcnow().isoformat(),
                        affected_units=shipment.units,
                        projected_stockout_risk=0.95,
                        underlying_cause=f"Supplier {supplier.name} (Tier {supplier.tier}) has halted operations."
                    )
                    alerts.append(alert)

        # 4. Global supplier outage scan — catch inactive suppliers not yet tied to a shipment
        seen_outage_sids = set()
        for supplier in suppliers.values():
            if not supplier.is_active and supplier.id not in seen_outage_sids:
                seen_outage_sids.add(supplier.id)
                # Find first inventory item associated with this supplier via any shipment
                affected_sku = "N/A"
                for s in self.repo.get_all_shipments():
                    if s.supplier_id == supplier.id:
                        affected_sku = s.sku_id
                        break
                alert = DisruptionAlert(
                    alert_id=f"ALT-GSUPOUT-{supplier.id}",
                    sku_id=affected_sku,
                    disruption_type=DisruptionType.SUPPLIER_OUTAGE,
                    severity=SeverityLevel.CRITICAL,
                    summary=f"Supplier {supplier.name} ({supplier.country}) is offline",
                    detected_at=datetime.utcnow().isoformat(),
                    affected_units=0,
                    projected_stockout_risk=0.90,
                    underlying_cause=f"Supplier {supplier.name} (Tier {supplier.tier}) flagged as inactive in catalog."
                )
                alerts.append(alert)

        return alerts
