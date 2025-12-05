# backend/api_routes.py
from fastapi import APIRouter, UploadFile, File
from typing import List, Dict, Optional
import io

import pandas as pd

from backend.models import ReconciliationResponse
from agents.reconciliation_agent import run_reconciliation_workflow

router = APIRouter(tags=["Reconciliation"])


def _map_filename_to_key(filename: str) -> Optional[str]:
    """Heuristic to map uploaded filename to logical dataset key."""
    name = filename.lower()

    if "raw" in name and "material" in name:
        return "raw_material"
    if "finished" in name or ("fg" in name and "inventory" in name):
        return "finished_goods"
    if "consumption" in name or "logs" in name:
        return "consumption_logs"
    if "erp" in name and "snapshot" in name:
        return "erp_inventory"
    if "master" in name and ("data" in name or "yield" in name):
        return "master_data"

    return None


def _read_uploaded_files(files: List[UploadFile]) -> Dict[str, pd.DataFrame]:
    """Read uploaded Excel/CSV files into DataFrames keyed by logical name."""
    dataframes: Dict[str, pd.DataFrame] = {}

    for f in files:
        key = _map_filename_to_key(f.filename)
        if key is None:
            # Ignore unknown file types for now
            continue

        content = f.file.read()
        buffer = io.BytesIO(content)

        if f.filename.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(buffer)
        elif f.filename.lower().endswith(".csv"):
            df = pd.read_csv(buffer)
        else:
            continue

        dataframes[key] = df

    return dataframes


@router.post("/reconcile", response_model=ReconciliationResponse)
async def reconcile_inventory(
    files: List[UploadFile] = File(...),
):
    """
    Accepts uploaded files (Excel/CSV), runs the reconciliation agent,
    and returns summarized results.
    """
    dfs = _read_uploaded_files(files)

    # If user didn't upload all needed files, the agent will load defaults.
    result = await run_reconciliation_workflow(dfs=dfs)
    return result
