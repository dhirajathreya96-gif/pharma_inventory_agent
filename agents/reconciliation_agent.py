# agents/reconciliation_agent.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from backend.models import (
    ReconciliationResponse,
    DiscrepancyItem,
    RecommendedAction,
)
from rules.business_rules import RULES
from agents.exception_agent import ExceptionClassifier
from agents.resolution_agent import ResolutionAgent
from config.settings import settings


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _load_default_data() -> Dict[str, pd.DataFrame]:
    """Load default Excel files from /data if not provided by the user."""
    data: Dict[str, pd.DataFrame] = {}

    paths = {
        "raw_material": DATA_DIR / "raw_material_inventory.xlsx",
        "finished_goods": DATA_DIR / "finished_goods_inventory.xlsx",
        "consumption_logs": DATA_DIR / "consumption_logs.xlsx",
        "erp_inventory": DATA_DIR / "erp_inventory_snapshot.xlsx",
        "master_data": DATA_DIR / "master_data.xlsx",
    }

    for key, path in paths.items():
        if path.exists():
            data[key] = pd.read_excel(path)

    return data


def _ensure_all_data(dfs: Optional[Dict[str, pd.DataFrame]]) -> Dict[str, pd.DataFrame]:
    base = _load_default_data()
    dfs = dfs or {}
    base.update(dfs)  # uploaded overrides defaults
    return base


def _compute_stock_mismatches(
    raw_df: pd.DataFrame,
    erp_df: pd.DataFrame,
) -> List[DiscrepancyItem]:
    """
    Compare ERP_Closing_Qty vs Warehouse_Closing_Qty and vs derived raw inventory.
    """
    discrepancies: List[DiscrepancyItem] = []

    # Aggregate warehouse (raw material) closing by Material_ID
    wh_summary = (
        raw_df.groupby("Material_ID", as_index=False)["Closing_Qty"].sum()
        .rename(columns={"Closing_Qty": "WH_Calc_Closing_Qty"})
    )

    merged = erp_df.merge(wh_summary, on="Material_ID", how="left")

    for _, row in merged.iterrows():
        material_id = row["Material_ID"]
        erp_qty = float(row["ERP_Closing_Qty"])
        wh_reported = float(row["Warehouse_Closing_Qty"])
        wh_calc = float(row.get("WH_Calc_Closing_Qty") or 0.0)

        # difference between ERP and warehouse reported
        diff_erp_wh = erp_qty - wh_reported
        abs_diff_erp_wh = abs(diff_erp_wh)

        if abs_diff_erp_wh > RULES.stock_mismatch_threshold:
            severity = "Low"
            if abs_diff_erp_wh >= RULES.high_severity_gap:
                severity = "High"
            elif abs_diff_erp_wh >= RULES.medium_severity_gap:
                severity = "Medium"

            desc = (
                f"ERP shows {erp_qty} units, warehouse snapshot shows {wh_reported} units "
                f"for {material_id}. Difference: {diff_erp_wh:+.1f}."
            )

            discrepancies.append(
                DiscrepancyItem(
                    material_id=material_id,
                    description=desc,
                    discrepancy_type="Stock mismatch (ERP vs Warehouse)",
                    severity=severity,
                    erp_qty=erp_qty,
                    wh_qty=wh_reported,
                    batch_id=None,
                )
            )

        # difference between warehouse reported and calculated from raw_df
        diff_wh_calc = wh_reported - wh_calc
        abs_diff_wh_calc = abs(diff_wh_calc)

        if abs_diff_wh_calc > RULES.stock_mismatch_threshold:
            severity = "Low"
            if abs_diff_wh_calc >= RULES.high_severity_gap:
                severity = "High"
            elif abs_diff_wh_calc >= RULES.medium_severity_gap:
                severity = "Medium"

            desc = (
                f"Warehouse snapshot shows {wh_reported} units but sum of raw material "
                f"batches is {wh_calc} units for {material_id}. Difference: {diff_wh_calc:+.1f}."
            )

            discrepancies.append(
                DiscrepancyItem(
                    material_id=material_id,
                    description=desc,
                    discrepancy_type="Stock mismatch (Warehouse vs Calculated)",
                    severity=severity,
                    erp_qty=erp_qty,
                    wh_qty=wh_calc,
                    batch_id=None,
                )
            )

    return discrepancies


def _compute_yield_deviations(
    cons_df: pd.DataFrame,
    master_df: pd.DataFrame,
) -> List[DiscrepancyItem]:
    """
    Identify batches where Actual_Consumption exceeds Expected_Consumption
    beyond Yield_Loss_Threshold%.
    """
    discrepancies: List[DiscrepancyItem] = []

    master_sel = master_df[["Material_ID", "Yield_Loss_Threshold"]].drop_duplicates()
    merged = cons_df.merge(master_sel, on="Material_ID", how="left")

    for _, row in merged.iterrows():
        mat = row["Material_ID"]
        batch_id = row["Batch_ID"]
        expected = float(row["Expected_Consumption"])
        actual = float(row["Actual_Consumption"])
        variance = actual - expected

        if expected <= 0:
            continue

        variance_pct = (variance / expected) * 100.0
        allowed_pct = float(row.get("Yield_Loss_Threshold") or RULES.yield_loss_default_threshold)

        if variance_pct > allowed_pct:
            # classify severity by % deviation
            severity = "Low"
            if variance_pct >= RULES.high_severity_gap:
                severity = "High"
            elif variance_pct >= RULES.medium_severity_gap:
                severity = "Medium"

            desc = (
                f"Batch {batch_id} for {mat}: expected {expected:.1f} units, "
                f"actual {actual:.1f} units, variance {variance:+.1f} "
                f"({variance_pct:.1f}% vs allowed {allowed_pct:.1f}%)."
            )

            discrepancies.append(
                DiscrepancyItem(
                    material_id=mat,
                    description=desc,
                    discrepancy_type="Yield deviation (overconsumption)",
                    severity=severity,
                    erp_qty=None,
                    wh_qty=None,
                    batch_id=batch_id,
                )
            )

    return discrepancies


def _compute_expired_inventory(raw_df: pd.DataFrame) -> List[DiscrepancyItem]:
    """
    Flag materials with non-zero Closing_Qty where Expiry_Date < today.
    """
    discrepancies: List[DiscrepancyItem] = []

    # Filter expired & non-zero closing
    today = pd.Timestamp("today").normalize()
    mask = (pd.to_datetime(raw_df["Expiry_Date"]) < today) & (raw_df["Closing_Qty"] > 0)
    expired_df = raw_df[mask]

    for _, row in expired_df.iterrows():
        mat = row["Material_ID"]
        batch = row["Batch_Number"]
        closing = float(row["Closing_Qty"])
        exp_date = pd.to_datetime(row["Expiry_Date"]).date()

        desc = (
            f"Batch {batch} of {mat} has {closing} units remaining but expired on {exp_date}."
        )

        discrepancies.append(
            DiscrepancyItem(
                material_id=mat,
                description=desc,
                discrepancy_type="Expired inventory on hand",
                severity="Medium",
                erp_qty=None,
                wh_qty=closing,
                batch_id=batch,
            )
        )

    return discrepancies


def _summarize_discrepancies(discrepancies: List[DiscrepancyItem]) -> str:
    """
    Simple text summary. Later we could plug in an LLM for a nicer narrative summary.
    """
    total = len(discrepancies)
    high = sum(1 for d in discrepancies if d.severity == "High")
    med = sum(1 for d in discrepancies if d.severity == "Medium")
    low = sum(1 for d in discrepancies if d.severity == "Low")

    summary = (
        f"Reconciliation completed. Found {total} discrepancies "
        f"({high} high, {med} medium, {low} low severity)."
    )

    # OPTIONAL: If you want to use an LLM summary later, you can add it here.
    # from langchain_openai import ChatOpenAI
    # if settings.openai_api_key:
    #     llm = ChatOpenAI(openai_api_key=settings.openai_api_key, model="gpt-4o-mini")
    #     # build a prompt from discrepancy descriptions and call llm.invoke(...)

    return summary


async def run_reconciliation_workflow(
    dfs: Optional[Dict[str, pd.DataFrame]] = None
) -> ReconciliationResponse:
    """
    Main orchestration entry point for the reconciliation agent.
    Receives an optional dict of DataFrames (from uploads). Missing ones
    are loaded from /data.
    """
    data = _ensure_all_data(dfs)

    raw_df = data["raw_material"]
    erp_df = data["erp_inventory"]
    cons_df = data["consumption_logs"]
    master_df = data["master_data"]

    # 1) Numeric / rules-based discrepancy detection
    stock_mismatches = _compute_stock_mismatches(raw_df, erp_df)
    yield_devs = _compute_yield_deviations(cons_df, master_df)
    expired_inv = _compute_expired_inventory(raw_df)

    all_discrepancies: List[DiscrepancyItem] = (
        stock_mismatches + yield_devs + expired_inv
    )

    # 2) Exception classification agent (can be LLM-enhanced later)
    classifier = ExceptionClassifier()
    classified = await classifier.classify(all_discrepancies)

    # 3) Resolution suggestion agent
    resolver = ResolutionAgent()
    actions: List[RecommendedAction] = await resolver.suggest_actions(classified)

    # 4) Aggregate metrics
    total_items_checked = len(erp_df.index) + len(cons_df.index)
    total_discrepancies = len(classified)
    high_risk = sum(1 for d in classified if d.severity == "High")
    medium_risk = sum(1 for d in classified if d.severity == "Medium")
    low_risk = sum(1 for d in classified if d.severity == "Low")

    summary = _summarize_discrepancies(classified)

    return ReconciliationResponse(
        summary=summary,
        total_items_checked=total_items_checked,
        total_discrepancies=total_discrepancies,
        high_risk_count=high_risk,
        medium_risk_count=medium_risk,
        low_risk_count=low_risk,
        discrepancies=classified,
        recommended_actions=actions,
    )
