from ..qbo_client import QBOClient

def invoices_summary(qbo_client: QBOClient, limit: int = 50):
    """
    Simple example analysis:
    - Pulls up to `limit` invoices
    - Returns count, total amount, average amount
    """
    query = f"SELECT * FROM Invoice STARTPOSITION 1 MAXRESULTS {limit}"
    data = qbo_client.query(query)

    invoices = data.get("QueryResponse", {}).get("Invoice", [])
    if not invoices:
        return {"count": 0, "total_amount": 0, "avg_amount": 0}

    amounts = [inv.get("TotalAmt", 0) for inv in invoices]
    total = sum(amounts)
    avg = total / len(invoices) if invoices else 0

    return {
        "count": len(invoices),
        "total_amount": total,
        "avg_amount": avg,
    }
