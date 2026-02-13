from ..qbo_client import QBOClient
from collections import defaultdict

def vendor_spend_summary(qbo_client: QBOClient, limit: int = 1000):
    """
    Returns total spend per vendor across Bills and Expenses.
    """
    results = defaultdict(float)

    # Pull Bills
    bills = qbo_client.query(f"SELECT * FROM Bill STARTPOSITION 1 MAXRESULTS {limit}")
    for bill in bills.get("QueryResponse", {}).get("Bill", []):
        vendor = bill.get("VendorRef", {}).get("name", "Unknown Vendor")
        amount = bill.get("TotalAmt", 0)
        results[vendor] += amount

    # Pull Expenses
    expenses = qbo_client.query(f"SELECT * FROM Purchase STARTPOSITION 1 MAXRESULTS {limit}")
    for exp in expenses.get("QueryResponse", {}).get("Purchase", []):
        vendor = exp.get("EntityRef", {}).get("name", "Unknown Vendor")
        amount = exp.get("TotalAmt", 0)
        results[vendor] += amount

    # Sort vendors by total spend
    sorted_vendors = sorted(results.items(), key=lambda x: x[1], reverse=True)

    return {
        "total_vendors": len(sorted_vendors),
        "top_5_vendors": sorted_vendors[:5],
        "vendor_breakdown": sorted_vendors,
    }
