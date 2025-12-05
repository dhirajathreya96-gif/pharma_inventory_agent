# tests/test_reconciliation.py
import pytest
from agents.reconciliation_agent import run_reconciliation_workflow


@pytest.mark.asyncio
async def test_reconciliation_workflow_runs_with_defaults():
    result = await run_reconciliation_workflow(dfs=None)
    assert result.total_items_checked > 0
    assert result.total_discrepancies >= 0
    assert isinstance(result.summary, str)
