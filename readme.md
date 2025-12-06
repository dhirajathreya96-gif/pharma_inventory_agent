# 🧪 Automated Pharma Inventory Reconciliation Agent  
### FastAPI • Streamlit • Agentic AI • Rules Engine • Python

![GitHub repo size](https://img.shields.io/github/repo-size/dhirajathreya96-gif/pharma_inventory_agent)
![GitHub last commit](https://img.shields.io/github/last-commit/dhirajathreya96-gif/pharma_inventory_agent)
![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-success)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-ff4b4b)
![License](https://img.shields.io/badge/License-MIT-purple)

---

# 🎥 **Demo Video**
Click below to watch the full walkthrough of the project:

<p align="center">
  <a href="https://www.youtube.com/watch?v=9gYl-wywoQA" target="_blank">
    <img src="https://img.youtube.com/vi/9gYl-wywoQA/maxresdefault.jpg" width="70%" />
  </a>
</p>

---

# 🚀 **Overview**

The **Automated Pharma Inventory Reconciliation Agent** is a **rule-based Agentic AI system** that performs daily inventory reconciliation for pharmaceutical operations — **without needing an LLM**.

It autonomously:

- Reads multiple Excel inventory files  
- Detects mismatches across ERP, warehouse & batch-level stock  
- Classifies severity (High / Medium / Low)  
- Generates recommended operational actions  
- Displays results in a clean Streamlit dashboard  

This replaces hours of manual reconciliation with a fully automated workflow.

---

# 🧠 **Why This Is Agentic AI (Without LLMs)**

Agentic AI ≠ LLM.

An **agent** is a system that can:

✔ Ingest data  
✔ Reason using rules  
✔ Decide next steps  
✔ Trigger workflows  
✔ Produce actions autonomously  

This system does all of this using a **deterministic rules engine**, making it ideal for accuracy-critical pharma operations.

---

# 🏗 **Architecture**

Pharma_Inventory_Agent/
│
├── backend/
│ ├── main.py # FastAPI server
│ ├── api_routes.py # Endpoints for reconciliation
│ ├── models.py # Request/response schemas
│
├── agents/
│ ├── reconciliation_agent.py # Core variance detection + logic
│ ├── resolution_agent.py # Recommended action generator
│ ├── exception_agent.py # Validation + error handling
│
├── frontend/
│ ├── app.py # Streamlit dashboard UI
│
├── rules/
│ ├── business_rules.py # Severity + action rules engine
│
├── data/ # Example Excel files
├── tests/ # Test suite
└── requirements.txt


---

# ⚙️ **Features**

### 🔍 Inventory Reconciliation Engine  
- ERP vs Warehouse  
- Warehouse vs Batch Totals  
- ERP vs Calculated Consumption  

### 📊 Severity Classification  
- 🔴 High  
- 🟡 Medium  
- 🟢 Low  

### 🧭 Rules-Based Action Engine  
Generates clear recommended actions like:  
- Cycle count  
- Investigate material movements  
- Review GRN & issues  
- Validate ERP posting delays  
- Recompute batch usage  

### 🖥 Streamlit Dashboard  
- File upload  
- Summary KPIs  
- Discrepancy tables with color-coding  
- Recommended actions table  
- Instant feedback  

### 🚀 Fully Local & Lightweight  
- No LLM  
- No cloud dependencies  
- Perfect for regulated industries  

---

# 🧩 **How It Works**

### 1️⃣ Upload inventory Excel files  
- Raw Material inventory  
- Finished Goods  
- Master Data  
- ERP stock snapshot  

### 2️⃣ Backend processes them  
- Cleans  
- Standardizes  
- Validates structure  

### 3️⃣ Reconciliation agent detects mismatches  
Applies variance logic across sources.

### 4️⃣ Rules engine classifies and recommends  
- Cycle count  
- Investigate movements  
- Check posting delays  
- Review consumption  

### 5️⃣ Streamlit UI displays everything beautifully  

---

# 🖥 **Run Locally**

### Backend (FastAPI)

```bash
uvicorn backend.main:app --reload
