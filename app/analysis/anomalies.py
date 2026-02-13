from ..qbo_client import QBOClient
import statistics

def transaction_anomalies(qbo_client: QBOClient, limit: int = 1000, z_threshold: float = 2.5):
    """
    Simple anomaly detector: looks at Invoice and Purchase amounts and flags
    transactions with unusually high amounts (z-score above threshold).
    """
    txns = []

    inv_data = qbo_client.query(f"SELECT * FROM Invoice STARTPOSITION 1 MAXRESULTS {limit}")
    for inv in inv_data.get("QueryResponse", {}).get("Invoice", []):
        amt = inv.get("TotalAmt", 0.0)
        txns.append(
            {
                "type": "Invoice",
                "id": inv.get("Id"),
                "name": inv.get("CustomerRef", {}).get("name", "Unknown"),
                "date": inv.get("TxnDate"),
                "amount": amt,
            }
        )

    pur_data = qbo_client.query(f"SELECT * FROM Purchase STARTPOSITION 1 MAXRESULTS {limit}")
    for p in pur_data.get("QueryResponse", {}).get("Purchase", []):
        amt = p.get("TotalAmt", 0.0)
        txns.append(
            {
                "type": "Purchase",
                "id": p.get("Id"),
                "name": p.get("EntityRef", {}).get("name", "Unknown"),
                "date": p.get("TxnDate"),
                "amount": amt,
            }
        )

    amounts = [t["amount"] for t in txns]
    if len(amounts) < 2:
        return {
            "message": "Not enough transactions to compute anomalies.",
            "transactions": txns,
            "anomalies": [],
        }

    mean_amt = statistics.mean(amounts)
    stdev_amt = statistics.pstdev(amounts)

    anomalies = []
    for t in txns:
        if stdev_amt > 0:
            z = (t["amount"] - mean_amt) / stdev_amt
        else:
            z = 0.0
        if z >= z_threshold:
            t_with_z = dict(t)
            t_with_z["z_score"] = z
            anomalies.append(t_with_z)

    return {
        "mean_amount": mean_amt,
        "stdev_amount": stdev_amt,
        "transactions": txns,
        "anomalies": sorted(anomalies, key=lambda x: x["z_score"], reverse=True),
    }
