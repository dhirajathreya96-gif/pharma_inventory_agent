# frontend/app.py

import io
import json
from typing import List

import pandas as pd
import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000/api"


# -----------------------------
# Helper functions
# -----------------------------
def call_reconciliation_api(uploaded_files: List[st.runtime.uploaded_file_manager.UploadedFile]):
    files = [
        ("files", (f.name, f.getvalue(), "application/octet-stream"))
        for f in uploaded_files
    ]
    resp = requests.post(f"{API_BASE_URL}/reconcile", files=files)
    return resp


def to_dataframe(records, fallback_columns=None) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=fallback_columns or [])
    return pd.DataFrame(records)


def add_severity_styles(df: pd.DataFrame):
    def highlight_severity(val):
        if val == "High":
            return "background-color: rgba(255,0,0,0.25); font-weight: 600;"
        if val == "Medium":
            return "background-color: rgba(255,165,0,0.18); font-weight: 500;"
        if val == "Low":
            return "background-color: rgba(0,255,0,0.12);"
        return ""

    if "severity" in df.columns:
        return df.style.applymap(highlight_severity, subset=["severity"])
    return df.style


def get_severity_counts(discrepancies_df: pd.DataFrame):
    if discrepancies_df.empty or "severity" not in discrepancies_df.columns:
        return 0, 0, 0
    counts = discrepancies_df["severity"].value_counts()
    high = int(counts.get("High", 0))
    med = int(counts.get("Medium", 0))
    low = int(counts.get("Low", 0))
    return high, med, low


# -----------------------------
# Streamlit app
# -----------------------------
def main():
    st.set_page_config(
        page_title="Pharma Inventory Reconciliation Agent",
        layout="wide",
    )

    st.title("💊 Automated Inventory Reconciliation Agent")
    st.markdown(
        "Upload daily inventory files and trigger the **agentic reconciliation workflow**.\n\n"
        "The agent compares ERP vs warehouse, flags yield deviations and expired stock, "
        "and suggests concrete actions for Ops & QA."
    )

    # Session state to keep last result
    if "result" not in st.session_state:
        st.session_state.result = None
    if "raw_response" not in st.session_state:
        st.session_state.raw_response = None

    # -----------------------------
    # File upload panel
    # -----------------------------
    with st.expander("📂 Upload inventory files", expanded=True):
        st.write("**Tip:** Upload all 5 files for a complete reconciliation:")
        st.markdown(
            "- `raw_material_inventory.xlsx`\n"
            "- `finished_goods_inventory.xlsx`\n"
            "- `erp_inventory_snapshot.xlsx`\n"
            "- `consumption_logs.xlsx`\n"
            "- `master_data.xlsx`"
        )

        uploaded_files = st.file_uploader(
            "Upload relevant Excel files (raw material, FG, ERP, etc.)",
            type=["xlsx", "xls", "csv"],
            accept_multiple_files=True,
        )

        run_col, info_col = st.columns([1, 3])
        with run_col:
            run_clicked = st.button("▶ Run Reconciliation", use_container_width=True)

        with info_col:
            if uploaded_files:
                st.success(f"{len(uploaded_files)} file(s) selected.")
            else:
                st.info("No files selected yet. You can still run using default sample data on the backend.")

    # -----------------------------
    # Call backend when button is clicked
    # -----------------------------
    if run_clicked:
        with st.spinner("Running agentic reconciliation workflow..."):
            try:
                resp = call_reconciliation_api(uploaded_files or [])
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.result = data
                    st.session_state.raw_response = resp.text
                    st.success("✅ Reconciliation complete!")
                else:
                    st.error(f"API error: {resp.status_code} - {resp.text}")
            except Exception as e:
                st.error(f"Request failed: {e}")

    result = st.session_state.result

    if not result:
        st.info("Run a reconciliation to see results.")
        return

    # Convert result to DataFrames
    discrepancies_df = to_dataframe(result.get("discrepancies", []))
    actions_df = to_dataframe(result.get("recommended_actions", []))

    total_items_checked = result.get("total_items_checked", 0)
    total_discrepancies = result.get("total_discrepancies", 0)
    high, med, low = get_severity_counts(discrepancies_df)
    summary_text = result.get("summary", "")

    # -----------------------------
    # KPI Section
    # -----------------------------
    st.markdown("---")
    st.markdown(f"### 🧾 Summary\n\n{summary_text}")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Items Checked", f"{total_items_checked:,}")
    kpi2.metric("Total Discrepancies", f"{total_discrepancies:,}")
    kpi3.metric("High Severity", f"{high:,}")
    kpi4.metric("Medium / Low", f"{med:,} med • {low:,} low")

    st.markdown("---")

    # -----------------------------
    # Tabs for detailed exploration
    # -----------------------------
    tab_overview, tab_disc, tab_actions, tab_downloads = st.tabs(
        ["📊 Overview", "🚨 Discrepancies", "✅ Recommended Actions", "📥 Downloads & Logs"]
    )

    # -----------------------------
    # OVERVIEW TAB
    # -----------------------------
    with tab_overview:
        left, right = st.columns([2, 1])

        with left:
            st.subheader("Severity distribution")
            if not discrepancies_df.empty and "severity" in discrepancies_df.columns:
                severity_counts = discrepancies_df["severity"].value_counts().reset_index()
                severity_counts.columns = ["severity", "count"]
                st.bar_chart(severity_counts.set_index("severity"))
            else:
                st.info("No discrepancies available for chart.")

            st.subheader("Top materials by discrepancy count")
            if not discrepancies_df.empty and "material_id" in discrepancies_df.columns:
                top_materials = (
                    discrepancies_df.groupby("material_id")
                    .size()
                    .reset_index(name="discrepancy_count")
                    .sort_values("discrepancy_count", ascending=False)
                    .head(15)
                    .set_index("material_id")
                )
                st.bar_chart(top_materials)
            else:
                st.info("No material-level data available.")

        with right:
            st.subheader("Quick insights")
            st.markdown(
                f"""
                - **{high:,}** high severity issues need urgent attention  
                - **{med:,}** medium and **{low:,}** low severity issues identified  
                - Data checked across **ERP vs Warehouse**, **yield deviations**, and **expired stock**  
                """
            )

            if not discrepancies_df.empty:
                types = discrepancies_df["discrepancy_type"].value_counts().to_dict()
                st.markdown("**Discrepancy types:**")
                for t, c in types.items():
                    st.write(f"- {t}: **{c}**")

    # -----------------------------
    # DISCREPANCIES TAB
    # -----------------------------
    with tab_disc:
        st.subheader("Discrepancies")

        if discrepancies_df.empty:
            st.info("No discrepancies returned by the agent.")
        else:
            # Filters
            filter_col1, filter_col2, filter_col3 = st.columns(3)

            with filter_col1:
                severity_filter = st.selectbox(
                    "Filter by severity",
                    options=["All", "High", "Medium", "Low"],
                    index=0,
                )

            with filter_col2:
                types = ["All"]
                if "discrepancy_type" in discrepancies_df.columns:
                    types += sorted(discrepancies_df["discrepancy_type"].dropna().unique().tolist())
                discrepancy_type_filter = st.selectbox(
                    "Filter by discrepancy type",
                    options=types,
                    index=0,
                )

            with filter_col3:
                material_search = st.text_input(
                    "Search by Material ID (e.g., RM-0123)",
                    value="",
                )

            filtered_df = discrepancies_df.copy()

            if severity_filter != "All" and "severity" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["severity"] == severity_filter]

            if discrepancy_type_filter != "All" and "discrepancy_type" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["discrepancy_type"] == discrepancy_type_filter]

            if material_search and "material_id" in filtered_df.columns:
                filtered_df = filtered_df[
                    filtered_df["material_id"].str.contains(material_search, case=False, na=False)
                ]

            st.caption(f"Showing {len(filtered_df):,} of {len(discrepancies_df):,} discrepancies.")

            styled = add_severity_styles(filtered_df)
            st.dataframe(styled, use_container_width=True)

    # -----------------------------
    # RECOMMENDED ACTIONS TAB
    # -----------------------------
    with tab_actions:
        st.subheader("Recommended Actions")

        if actions_df.empty:
            st.info("No recommended actions were returned.")
        else:
            st.caption(f"{len(actions_df):,} actions suggested by the agent.")
            st.dataframe(actions_df, use_container_width=True)

            st.markdown("#### Quick view by priority")
            if "priority" in actions_df.columns:
                pr_counts = actions_df["priority"].value_counts().reset_index()
                pr_counts.columns = ["priority", "count"]
                st.bar_chart(pr_counts.set_index("priority"))

    # -----------------------------
    # DOWNLOADS & LOGS TAB
    # -----------------------------
    with tab_downloads:
        st.subheader("Downloads & Raw Response")

        col_a, col_b = st.columns(2)

        # Discrepancies CSV
        with col_a:
            if not discrepancies_df.empty:
                csv_bytes = discrepancies_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇ Download discrepancies (CSV)",
                    data=csv_bytes,
                    file_name="discrepancies_report.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

        # Actions CSV
        with col_b:
            if not actions_df.empty:
                act_bytes = actions_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇ Download recommended actions (CSV)",
                    data=act_bytes,
                    file_name="recommended_actions.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

        st.markdown("#### Raw JSON response (for debugging / auditing)")
        if st.session_state.raw_response:
            with st.expander("Show raw JSON from backend"):
                try:
                    parsed = json.loads(st.session_state.raw_response)
                    st.json(parsed)
                except Exception:
                    st.text(st.session_state.raw_response)


if __name__ == "__main__":
    main()
