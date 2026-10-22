"""Candidate Mitigation Strategy Generator.

Constructs realistic, policy-compliant candidate interventions for detected
supply chain bottlenecks to feed into the Meterless World Model simulation engine.
"""

from typing import List, Dict, Any
from src.models.domain import DisruptionAlert, DisruptionType, SeverityLevel
from src.models.decisions import MitigationCandidate, ActionType
from src.data.repository import repository

class ActionGenerator:
    """Generates parameterized mitigation candidates tailored to specific disruption alerts."""

    def __init__(self, repo=None):
        self.repo = repo or repository

    def generate_candidates_for_alert(self, alert: DisruptionAlert) -> List[MitigationCandidate]:
        """Constructs diverse mitigation strategies based on disruption type and severity."""
        item = self.repo.get_inventory_item(alert.sku_id)
        unit_cost = item.unit_cost_usd if item else 50.0

        candidates = [
            # 1. Baseline: Do Nothing (Status Quo)
            MitigationCandidate(
                candidate_id=f"ACT-STATUSQUO-{alert.sku_id[-3:]}",
                action_type=ActionType.NO_ACTION_MONITOR,
                title="Status Quo (Continuous Monitoring)",
                description="Maintain existing shipment schedule without capital deployment; monitor port release.",
                cost_usd=0.0,
                estimated_time_to_resolve_days=10,
                risk_reduction_pct=0.0,
                requires_human_approval=False,
                approval_threshold_usd=0.0
            ),
            # 2. Port Reroute / Intermodal Switch
            MitigationCandidate(
                candidate_id=f"ACT-REROUTE-{alert.sku_id[-3:]}",
                action_type=ActionType.PORT_REROUTE,
                title="Intermodal Port Diversion (Bypass to Port of Seattle)",
                description="Divert ocean cargo container to Port of Seattle with rail freight expedited delivery to warehouse.",
                cost_usd=1200.0,
                estimated_time_to_resolve_days=3,
                risk_reduction_pct=55.0,
                requires_human_approval=True,
                approval_threshold_usd=1000.0
            ),
            # 3. Expedited Air Freight
            MitigationCandidate(
                candidate_id=f"ACT-AIRFREIGHT-{alert.sku_id[-3:]}",
                action_type=ActionType.AIR_FREIGHT_EXPEDITE,
                title="Emergency Air Freight Buffer Injection (200 Units)",
                description="Charter expedited direct air freight delivery from secondary distribution center to bridge the delay gap.",
                cost_usd=round(min(5000.0, 150 * unit_cost * 0.4), 2),
                estimated_time_to_resolve_days=1,
                risk_reduction_pct=88.0,
                requires_human_approval=True,
                approval_threshold_usd=1000.0
            ),
            # 4. Secondary Supplier Purchase Order
            MitigationCandidate(
                candidate_id=f"ACT-ALTSUPPLIER-{alert.sku_id[-3:]}",
                action_type=ActionType.ALTERNATE_SUPPLIER_PO,
                title="Split Emergency PO with EuroSilicon GmbH (Tier 2)",
                description="Issue spot purchase order for 150 units with pre-qualified European supplier to diversify transit routes.",
                cost_usd=round(150 * unit_cost * 1.25, 2),
                estimated_time_to_resolve_days=4,
                risk_reduction_pct=75.0,
                requires_human_approval=True,
                approval_threshold_usd=1000.0
            )
        ]

        return candidates
