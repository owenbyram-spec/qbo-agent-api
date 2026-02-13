from ..qbo_client import QBOClient
from datetime import datetime, date
from collections import defaultdict

def ar_aging(qbo_client: QBOClient, limit: int = 1000):
    """
    Computes AR aging buckets for open invoices:
      0-30, 31-60, 61-90, 90+ days past due.
    """
    today = date.today()
    query = f"SELECT * FROM Invoice WHERE Balance > 0 STARTPOSITION 1 MAXRESULTS {limit}"
    data = qbo_client.query(query)

    buckets = {
        "0-30": 0.0,
        "31-60": 0.0,
        "61-90": 0.0,
        "90+": 0.0,
    }
    detail = []

    invoices = data.get("QueryResponse", {}).get("Invoice", [])
    for inv in invoices:
        balance = inv.get("Balance", 0.0)
        due_str = inv.get("DueDate") or inv.get("TxnDate")
        if not due_str:
            continue
        try:
            due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
        except Exception:
            continue

        days_past_due = (today - due_date).days

        if days_past_due <= 30:
            bucket = "0-30"
        elif days_past_due <= 60:
            bucket = "31-60"
        elif days_past_due <= 90:
            bucket = "61-90"
        else:
            bucket = "90+"

        buckets[bucket] += balance
        detail.append(
            {
                "invoice_id": inv.get("Id"),
                "customer": inv.get("CustomerRef", {}).get("name", "Unknown"),
                "balance": balance,
                "due_date": due_str,
                "days_past_due": days_past_due,
                "bucket": bucket,
            }
        )

    return {
        "as_of": today.isoformat(),
        "buckets": buckets,
        "invoices": detail,
    }
