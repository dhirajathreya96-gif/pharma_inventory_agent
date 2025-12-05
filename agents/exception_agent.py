# agents/exception_agent.py
from typing import List
from backend.models import DiscrepancyItem


class ExceptionClassifier:
    """
    Placeholder exception classifier.
    Later this can:
      - Normalize discrepancy_type labels
      - Upgrade/downgrade severity based on risk rules
      - Use LLM to cluster similar issues
    """

    async def classify(self, discrepancies: List[DiscrepancyItem]) -> List[DiscrepancyItem]:
        # For now, simply return the same list.
        # You could add extra logic here if needed.
        return discrepancies
