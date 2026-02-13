from ..qbo_client import QBOClient
from collections import defaultdict

def customer_revenue_summary(qbo_client: QBOClient, limit: int = 1000):
    """
    Returns revenue per customer based on Invoices.
    """
    revenue = defaultdict(float)

    invoices = qbo_client.query(f"SELECT * FROM Invoice STARTPOSITION 1 MAXRESULTS {limit}")
    for inv in invoices.get("QueryResponse", {}).get("Invoice", []):
        customer = inv.get("CustomerRef", {}).get("name", "Unknown Customer")
        amount = inv.get("TotalAmt", 0)
        revenue[customer] += amount

    sorted_customers = sorted(revenue.items(), key=lambda x: x[1], reverse=True)

    return {
        "total_customers": len(sorted_customers),
        "top_5_customers": sorted_customers[:5],
        "customer_breakdown": sorted_customers,
    }
