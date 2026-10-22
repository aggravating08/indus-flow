"""Enterprise Supply Chain Mock Database Seeds.

Provides structured, high-fidelity supply chain seed data representing a global
electronics & automotive manufacturing supply network.
"""

from src.models.domain import (
    Supplier, InventoryItem, Shipment, DemandForecast,
    SeverityLevel, ShipmentStatus
)

INITIAL_SUPPLIERS = [
    Supplier(
        id="SUP-001",
        name="Apex Semiconductor Ltd",
        country="Taiwan",
        tier=1,
        reliability_score=0.96,
        is_active=True,
        lead_time_days=14,
        expedited_available=True,
        expedited_surcharge_pct=0.30
    ),
    Supplier(
        id="SUP-002",
        name="Shenzhen Electrics Co",
        country="China",
        tier=1,
        reliability_score=0.91,
        is_active=True,
        lead_time_days=10,
        expedited_available=True,
        expedited_surcharge_pct=0.25
    ),
    Supplier(
        id="SUP-003",
        name="EuroSilicon Microchips GmbH",
        country="Germany",
        tier=2,
        reliability_score=0.98,
        is_active=True,
        lead_time_days=7,
        expedited_available=True,
        expedited_surcharge_pct=0.40
    ),
    Supplier(
        id="SUP-004",
        name="Pacific Precision Assembly",
        country="Vietnam",
        tier=2,
        reliability_score=0.84,
        is_active=True,
        lead_time_days=18,
        expedited_available=False,
        expedited_surcharge_pct=0.0
    ),
    Supplier(
        id="SUP-005",
        name="Kyoto Sensor Dynamics",
        country="Japan",
        tier=1,
        reliability_score=0.99,
        is_active=False,  # Outage / maintenance mode for edge case testing
        lead_time_days=21,
        expedited_available=False,
        expedited_surcharge_pct=0.0
    )
]

INITIAL_INVENTORY = [
    InventoryItem(
        sku_id="SKU-9921-MCU",
        name="Automotive Grade Microcontroller 32-bit",
        category="Semiconductors",
        current_stock=140,
        safety_stock=200,
        daily_burn_rate=25,
        unit_cost_usd=42.50,
        reorder_point=250,
        criticality=SeverityLevel.CRITICAL
    ),
    InventoryItem(
        sku_id="SKU-4412-CAP",
        name="Multilayer Ceramic Capacitor 10uF",
        category="Passive Components",
        current_stock=850,
        safety_stock=400,
        daily_burn_rate=60,
        unit_cost_usd=0.85,
        reorder_point=500,
        criticality=SeverityLevel.MEDIUM
    ),
    InventoryItem(
        sku_id="SKU-7734-PWR",
        name="SiC MOSFET Power Module 1200V",
        category="Power Electronics",
        current_stock=80,
        safety_stock=150,
        daily_burn_rate=20,
        unit_cost_usd=115.00,
        reorder_point=180,
        criticality=SeverityLevel.CRITICAL
    ),
    InventoryItem(
        sku_id="SKU-1089-BAT",
        name="Li-Ion Prismatic Battery Cell 3.7V 50Ah",
        category="Energy Storage",
        current_stock=420,
        safety_stock=300,
        daily_burn_rate=35,
        unit_cost_usd=68.00,
        reorder_point=350,
        criticality=SeverityLevel.HIGH
    ),
    InventoryItem(
        sku_id="SKU-3320-HAR",
        name="Shielded High-Voltage Wiring Harness",
        category="Cables & Connectors",
        current_stock=600,
        safety_stock=250,
        daily_burn_rate=30,
        unit_cost_usd=24.50,
        reorder_point=300,
        criticality=SeverityLevel.LOW
    )
]

INITIAL_SHIPMENTS = [
    Shipment(
        tracking_id="TRK-US-9821",
        sku_id="SKU-9921-MCU",
        supplier_id="SUP-001",
        carrier_name="Ocean Express Logistics",
        origin_port="Port of Kaohsiung",
        destination_port="Port of Long Beach",
        status=ShipmentStatus.CUSTOMS_HOLD,
        units=500,
        estimated_arrival_days=4,
        reported_delay_days=7
    ),
    Shipment(
        tracking_id="TRK-EU-4402",
        sku_id="SKU-7734-PWR",
        supplier_id="SUP-002",
        carrier_name="Maersk Intermodal",
        origin_port="Port of Shanghai",
        destination_port="Port of Los Angeles",
        status=ShipmentStatus.PORT_BOTTLENECK,
        units=250,
        estimated_arrival_days=3,
        reported_delay_days=5
    ),
    Shipment(
        tracking_id="TRK-VN-1198",
        sku_id="SKU-4412-CAP",
        supplier_id="SUP-004",
        carrier_name="Evergreen Marine",
        origin_port="Port of Da Nang",
        destination_port="Port of Oakland",
        status=ShipmentStatus.IN_TRANSIT,
        units=2000,
        estimated_arrival_days=6,
        reported_delay_days=0
    ),
    Shipment(
        tracking_id="TRK-DE-8831",
        sku_id="SKU-1089-BAT",
        supplier_id="SUP-003",
        carrier_name="DHL Global Forwarding",
        origin_port="Frankfurt Airport",
        destination_port="Chicago O'Hare",
        status=ShipmentStatus.ON_SCHEDULE,
        units=400,
        estimated_arrival_days=2,
        reported_delay_days=0
    )
]

INITIAL_DEMAND_FORECASTS = [
    DemandForecast(sku_id="SKU-9921-MCU", projected_daily_demand=25, surge_multiplier=1.25),
    DemandForecast(sku_id="SKU-4412-CAP", projected_daily_demand=60, surge_multiplier=1.0),
    DemandForecast(sku_id="SKU-7734-PWR", projected_daily_demand=20, surge_multiplier=1.35),
    DemandForecast(sku_id="SKU-1089-BAT", projected_daily_demand=35, surge_multiplier=1.10),
    DemandForecast(sku_id="SKU-3320-HAR", projected_daily_demand=30, surge_multiplier=1.0)
]
