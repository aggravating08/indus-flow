"""Zetaris Cloud Gateway & Semantic Layer Connector.

Provides a unified interface for executing federated SQL queries over virtualized
enterprise data sources (ERP tables, supplier REST APIs, shipment telemetry feeds).

Supports two distinct operation modes:
1. LIVE_ZETARIS: Connects via PostgreSQL wire protocol to Zetaris Lightning SQL on port 10000.
2. MOCK_SEMANTIC_ADAPTER: Emulates the virtualized semantic catalog using the local repository,
   transparently labeled as a mock adapter for local testing and offline evaluation.
"""

from typing import List, Dict, Any, Optional
import logging
from src.config import settings

logger = logging.getLogger(__name__)

class ZetarisConnector:
    """Zetaris Unified Semantic Layer Connector."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None
    ):
        self.host = host or settings.zetaris_host
        self.port = port or settings.zetaris_port
        self.user = user or settings.zetaris_user
        self.password = password or settings.zetaris_password
        self.database = database or settings.zetaris_database

        # Determine mode transparently
        self.is_live = False
        self.mode = "MOCK_SEMANTIC_ADAPTER"
        self._check_connectivity()

    def _check_connectivity(self):
        """Attempts connection if a non-default/live host is supplied."""
        # Only attempt live socket connection if not default 'localhost' or explicit flag set
        if self.host not in ("localhost", "127.0.0.1") or settings.app_env == "production":
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    dbname=self.database,
                    connect_timeout=2
                )
                conn.close()
                self.is_live = True
                self.mode = "LIVE_ZETARIS_GATEWAY"
                logger.info(f"Connected to live Zetaris Lightning SQL Gateway at {self.host}:{self.port}")
            except Exception as e:
                logger.warning(f"Live Zetaris connection failed ({e}). Falling back to MOCK_SEMANTIC_ADAPTER.")
                self.is_live = False
                self.mode = "MOCK_SEMANTIC_ADAPTER"
        else:
            self.mode = "MOCK_SEMANTIC_ADAPTER"

    def query_semantic_layer(self, sql_query: str) -> List[Dict[str, Any]]:
        """Executes federated SQL query against the semantic catalog."""
        logger.info(f"[{self.mode}] Executing query: {sql_query}")

        if self.is_live:
            return self._execute_live_sql(sql_query)
        else:
            return self._execute_mock_virtual_view(sql_query)

    def _execute_live_sql(self, sql_query: str) -> List[Dict[str, Any]]:
        """Executes query over live psycopg2 connection to Zetaris."""
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            dbname=self.database,
            connect_timeout=5
        )
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql_query)
                records = cur.fetchall()
                return [dict(r) for r in records]
        finally:
            conn.close()

    def _execute_mock_virtual_view(self, sql_query: str) -> List[Dict[str, Any]]:
        """Virtual semantic catalog emulator backed by the state repository."""
        from src.data.repository import repository

        # Virtual join: Suppliers x Shipments x Inventory x Demand
        results = []
        for sku_id, item in repository.inventory.items():
            shipments = repository.get_shipments_for_sku(sku_id)
            primary_shipment = shipments[0] if shipments else None
            supplier = repository.get_supplier(primary_shipment.supplier_id) if primary_shipment else None
            demand = repository.demand.get(sku_id)

            record = {
                "sku_id": item.sku_id,
                "item_name": item.name,
                "category": item.category,
                "current_stock": item.current_stock,
                "safety_stock": item.safety_stock,
                "daily_burn_rate": item.daily_burn_rate,
                "days_of_supply": item.days_of_supply,
                "unit_cost_usd": item.unit_cost_usd,
                "criticality": item.criticality.value,
                "supplier_id": supplier.id if supplier else "N/A",
                "supplier_name": supplier.name if supplier else "Unassigned",
                "supplier_country": supplier.country if supplier else "N/A",
                "supplier_reliability": supplier.reliability_score if supplier else 0.0,
                "supplier_active": supplier.is_active if supplier else False,
                "lead_time_days": supplier.lead_time_days if supplier else 0,
                "shipment_tracking_id": primary_shipment.tracking_id if primary_shipment else "NONE",
                "carrier_name": primary_shipment.carrier_name if primary_shipment else "NONE",
                "origin_port": primary_shipment.origin_port if primary_shipment else "NONE",
                "destination_port": primary_shipment.destination_port if primary_shipment else "NONE",
                "shipment_status": primary_shipment.status.value if primary_shipment else "NO_TRANSIT",
                "reported_delay_days": primary_shipment.reported_delay_days if primary_shipment else 0,
                "projected_daily_demand": demand.projected_daily_demand if demand else item.daily_burn_rate,
                "data_source_provenance": f"{self.mode} (Zetaris Virtual Catalog)"
            }
            results.append(record)

        return results
