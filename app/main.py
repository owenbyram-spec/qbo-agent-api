from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .qbo_auth import router as qbo_auth_router
from .qbo_client import get_qbo_client_from_db

# Analysis imports
from .analysis.basic_metrics import invoices_summary
from .analysis.vendor_spend import vendor_spend_summary
from .analysis.customer_revenue import customer_revenue_summary
from .analysis.expense_trends import expense_trend_mom
from .analysis.profit_margin import profit_and_margin_by_month
from .analysis.cogs_anomaly import cogs_anomalies
from .analysis.cashflow_forecast import cashflow_forecast
from .analysis.ar_aging import ar_aging
from .analysis.anomalies import transaction_anomalies

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


@app.get("/analysis/vendor-spend")
def get_vendor_spend(limit: int = 1000, db: Session = Depends(get_db)):
    client = get_qbo_client_from_db(db)
    return vendor_spend_summary(client, limit)


@app.get("/analysis/customer-revenue")
def get_customer_revenue(limit: int = 1000, db: Session = Depends(get_db)):
    client = get_qbo_client_from_db(db)
    return customer_revenue_summary(client, limit)


@app.get("/analysis/expense-trend")
def get_expense_trend(limit: int = 1000, db: Session = Depends(get_db)):
    client = get_qbo_client_from_db(db)
    return expense_trend_mom(client, limit)


@app.get("/analysis/profit-margin")
def get_profit_and_margin(db: Session = Depends(get_db)):
    client = get_qbo_client_from_db(db)
    return profit_and_margin_by_month(client)


@app.get("/analysis/cogs-anomalies")
def get_cogs_anomalies(z_threshold: float = 2.0, db: Session = Depends(get_db)):
    client = get_qbo_client_from_db(db)
    return cogs_anomalies(client, z_threshold)


@app.get("/analysis/cashflow-forecast")
def get_cashflow_forecast(horizon_months: int = 3, db: Session = Depends(get_db)):
    client = get_qbo_client_from_db(db)
    return cashflow_forecast(client, horizon_months)


@app.get("/analysis/ar-aging")
def get_ar_aging(limit: int = 1000, db: Session = Depends(get_db)):
    client = get_qbo_client_from_db(db)
    return ar_aging(client, limit)


@app.get("/analysis/transaction-anomalies")
def get_transaction_anomalies(
    limit: int = 1000,
    z_threshold: float = 2.5,
    db: Session = Depends(get_db),
):
    client = get_qbo_client_from_db(db)
    return transaction_anomalies(client, limit=limit, z_threshold=z_threshold)
