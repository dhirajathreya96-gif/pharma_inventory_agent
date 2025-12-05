# backend/models.py
from pydantic import BaseModel
from typing import List, Optional


class DiscrepancyItem(BaseModel):
    material_id: str
    description: str
    discrepancy_type: str
    severity: str
    erp_qty: Optional[float] = None
    wh_qty: Optional[float] = None
    batch_id: Optional[str] = None


class RecommendedAction(BaseModel):
    action_id: str
    title: str
    description: str
    priority: str


class ReconciliationResponse(BaseModel):
    summary: str
    total_items_checked: int
    total_discrepancies: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    discrepancies: List[DiscrepancyItem]
    recommended_actions: List[RecommendedAction]
