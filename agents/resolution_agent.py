# agents/resolution_agent.py
from typing import List
from backend.models import DiscrepancyItem, RecommendedAction


class ResolutionAgent:
    """
    Suggests remediation actions for each discrepancy.
    This can be made LLM-driven later; for now it's rules-based.
    """

    async def suggest_actions(
        self, classified_discrepancies: List[DiscrepancyItem]
    ) -> List[RecommendedAction]:
        actions: List[RecommendedAction] = []
        counter = 1

        for d in classified_discrepancies:
            action_id = f"ACT-{counter:04d}"

            if "Stock mismatch (ERP vs Warehouse)" in d.discrepancy_type:
                title = f"Cycle count for {d.material_id}"
                description = (
                    f"Perform a physical cycle count for {d.material_id} and reconcile "
                    f"ERP vs warehouse quantities. Discrepancy: {d.description}"
                )
                priority = "High" if d.severity == "High" else "Medium"

            elif "Stock mismatch (Warehouse vs Calculated)" in d.discrepancy_type:
                title = f"Investigate transaction history for {d.material_id}"
                description = (
                    "Review recent goods receipts, issues, and adjustments to understand "
                    f"why snapshot vs calculated inventory differ. {d.description}"
                )
                priority = "Medium"

            elif "Yield deviation" in d.discrepancy_type:
                title = f"Investigate yield deviation for batch {d.batch_id}"
                description = (
                    "Check batch records, line clearance, and equipment calibration for "
                    f"possible overconsumption or losses. {d.description}"
                )
                priority = "High" if d.severity == "High" else "Medium"

            elif "Expired inventory" in d.discrepancy_type:
                title = f"Quarantine expired stock for {d.material_id}"
                description = (
                    f"Move expired batch {d.batch_id} to quarantine/scrap as per SOP and "
                    "ensure it is not used in production."
                )
                priority = "Medium"

            else:
                title = f"Review discrepancy for {d.material_id}"
                description = f"Review and triage: {d.description}"
                priority = "Low"

            actions.append(
                RecommendedAction(
                    action_id=action_id,
                    title=title,
                    description=description,
                    priority=priority,
                )
            )

            counter += 1

        return actions
