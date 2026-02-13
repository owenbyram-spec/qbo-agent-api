from ..qbo_client import QBOClient
from .profit_margin import profit_and_margin_by_month
import statistics

def cogs_anomalies(qbo_client: QBOClient, z_threshold: float = 2.0):
    """
    Flags months where COGS is unusually high relative to the year-to-date average.
    """
    pm = profit_and_margin_by_month(qbo_client)
    months = pm["months"]
    cogs_values = [m["cogs"] for m in months if m["cogs"] is not None]

    if len(cogs_values) < 2:
        return {
            "months": months,
            "anomalies": [],
            "message": "Not enough COGS data points to compute anomalies.",
        }

    mean_cogs = statistics.mean(cogs_values)
    stdev_cogs = statistics.pstdev(cogs_values)

    anomalies = []
    for m in months:
        cogs = m["cogs"]
        if stdev_cogs > 0:
            z = (cogs - mean_cogs) / stdev_cogs
        else:
            z = 0.0
        if z >= z_threshold:
            anomalies.append(
                {
                    "month": m["month"],
                    "cogs": cogs,
                    "z_score": z,
                }
            )

    return {
        "mean_cogs": mean_cogs,
        "stdev_cogs": stdev_cogs,
        "months": months,
        "anomalies": anomalies,
    }
