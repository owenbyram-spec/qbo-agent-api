from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from .db import Base, engine, get_db      # <-- THIS imports Base
from .qbo_auth import router as qbo_auth_router
from .qbo_client import get_qbo_client_from_db
from .analysis.basic_metrics import invoices_summary

# Create DB tables at startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="QBO Financial Analysis Agent")

# Include OAuth routes (/qbo/authorize and /qbo/callback)
app.include_router(qbo_auth_router)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/analysis/invoices-summary")
def get_invoices_summary(limit: int = 50, db: Session = Depends(get_db)):
    """
    Simple endpoint to test DB + QBO + analysis.
    """
    try:
        client = get_qbo_client_from_db(db)
        return invoices_summary(client, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
