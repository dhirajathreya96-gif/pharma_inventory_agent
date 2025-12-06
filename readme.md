# Pharma Inventory Reconciliation Agent (Agentic AI)

Automated **daily inventory reconciliation** for a pharmaceutical company using **agentic AI** (LangChain + LangGraph + LLMs).

🎥 **Project Demo Video:** 
https://www.youtube.com/watch?v=9gYl-wywoQA

## Features (Planned)

- Ingests:
  - Raw material inventory
  - Finished goods inventory
  - ERP inventory snapshot
  - Consumption logs
  - Master data (yields, QA rules)
- Reconciles **expected vs. actual** quantities
- Detects:
  - Stock mismatches
  - Yield deviations
  - Expired batch usage
  - Negative inventory
- Generates:
  - Exception list
  - Recommended actions for operations / QA

## Tech Stack

- Backend: FastAPI
- AI: LangChain, LangGraph, OpenAI
- Frontend: Streamlit
- Data: Pandas, Excel files

## Project Structure

(then paste the tree)

## Getting Started

```bash
# 1. Clone repo
git clone <your-repo-url>
cd pharma-inventory-agent

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env
cp .env.example .env
# Fill in OPENAI_API_KEY, etc.

# 5. Run backend
uvicorn backend.main:app --reload

# 6. Run frontend
streamlit run frontend/app.py
# pharma_inventory_agent
