# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api_routes import router as api_router

app = FastAPI(
    title="Pharma Inventory Reconciliation Agent",
    version="0.1.0",
    description="Automated agentic AI for daily pharma inventory reconciliation.",
)

# CORS (so Streamlit frontend can talk to it)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Run with:
# uvicorn backend.main:app --reload
