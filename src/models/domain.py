"""Domain Models for Supply Chain Entities and Disruption Alerts."""

from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field

class DisruptionType(str, Enum):
    PORT_CONGESTION = "PORT_CONGESTION"
    CUSTOMS_HOLD = "CUSTOMS_HOLD"
    CARRIER_DELAY = "CARRIER_DELAY"
    SUPPLIER_OUTAGE = "SUPPLIER_OUTAGE"
    DEMAND_SURGE = "DEMAND_SURGE"

class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ShipmentStatus(str, Enum):
    ON_SCHEDULE = "ON_SCHEDULE"
    IN_TRANSIT = "IN_TRANSIT"
    CUSTOMS_HOLD = "CUSTOMS_HOLD"
    WEATHER_DELAY = "WEATHER_DELAY"
    PORT_BOTTLENECK = "PORT_BOTTLENECK"
    DELIVERED = "DELIVERED"

class Supplier(BaseModel):
    id: str
    name: str
    country: str
    tier: int = 1
    reliability_score: float = Field(ge=0.0, le=1.0, default=0.95)
    is_active: bool = True
    lead_time_days: int = 14
    expedited_available: bool = True
    expedited_surcharge_pct: float = 0.25

class InventoryItem(BaseModel):
    sku_id: str
    name: str
    category: str
    current_stock: int
    safety_stock: int
    daily_burn_rate: int
    unit_cost_usd: float
    reorder_point: int
    criticality: SeverityLevel = SeverityLevel.HIGH

    @property
    def days_of_supply(self) -> float:
        if self.daily_burn_rate <= 0:
            return 999.0
        return round(self.current_stock / self.daily_burn_rate, 1)

class Shipment(BaseModel):
    tracking_id: str
    sku_id: str
    supplier_id: str
    carrier_name: str
    origin_port: str
    destination_port: str
    status: ShipmentStatus
    units: int
    estimated_arrival_days: int
    reported_delay_days: int = 0

class DemandForecast(BaseModel):
    sku_id: str
    projected_daily_demand: int
    surge_multiplier: float = 1.0
    forecast_confidence: float = 0.90

class DisruptionAlert(BaseModel):
    alert_id: str
    sku_id: str
    disruption_type: DisruptionType
    severity: SeverityLevel
    summary: str
    detected_at: str
    affected_units: int
    projected_stockout_risk: float  # 0.0 to 1.0
    underlying_cause: str
