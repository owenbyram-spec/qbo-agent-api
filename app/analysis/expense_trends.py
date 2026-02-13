from ..qbo_client import QBOClient
from collections import defaultdict
import datetime

def expense_trend_mom(qbo_client: QBOClient, limit: int = 1000):
    """
    Returns month-over-month expense totals.
    """
    monthly = defaultdict(float)

    purchases = qbo_client.query(f"SELECT * FROM Purchase STARTPOSITION 1 MAXRESULTS {limit}")
    for exp in purchases.get("QueryResponse", {}).get("Purchase", []):
        date_str = exp.get("TxnDate")
        if not date_str:
            continue
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        key = date_obj.strftime("%Y-%m")
        monthly[key] += exp.get("TotalAmt", 0)

    # Sort months chronologically
    trend = sorted(monthly.items(), key=lambda x: x[0])

    return {
        "months": [m for m, _ in trend],
        "expense_totals": [v for _, v in trend],
        "month_over_month": trend,
    }
