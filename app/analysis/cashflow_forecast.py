from ..qbo_client import QBOClient
from collections import defaultdict
import statistics

def cashflow_forecast(qbo_client: QBOClient, horizon_months: int = 3):
    """
    Very simple cash flow forecast based on ProfitAndLoss summarized by month.
    Not production-grade, but gives a sense of trend:
      cash_flow_month = income - cogs - expenses
    """
    report = qbo_client.get_report(
        "ProfitAndLoss",
        {
            "summarize_column_by": "Month",
            "columns": "total",
            "date_macro": "ThisFiscalYearToDate",
        },
    )

    cols = report.get("Columns", {}).get("Column", [])
    month_labels = [c.get("ColTitle", "") for c in cols]
    income = [0.0] * len(month_labels)
    cogs = [0.0] * len(month_labels)
    expenses = [0.0] * len(month_labels)

    def extract_amount(cell):
        try:
            return float(cell.get("value", "0") or 0)
        except Exception:
            return 0.0

    for section in report.get("Rows", {}).get("Row", []):
        if section.get("type") != "Section":
            continue
        title = section.get("Header", {}).get("ColData", [{}])[0].get("value", "")
        rows = section.get("Rows", {}).get("Row", [])

        for r in rows:
            cells = r.get("ColData", [])
            for i, cell in enumerate(cells[1:], start=0):
                amt = extract_amount(cell)
                if "Income" in title:
                    income[i] += amt
                elif "Cost of Goods Sold" in title:
                    cogs[i] += amt
                elif "Expenses" in title:
                    expenses[i] += amt

    cash_flow = []
    for i, label in enumerate(month_labels):
        cf = income[i] - cogs[i] - expenses[i]
        cash_flow.append({"month": label, "cash_flow": cf})

    past_values = [m["cash_flow"] for m in cash_flow if m["cash_flow"] is not None]
    avg_cf = statistics.mean(past_values) if past_values else 0.0

    forecast = [
        {
            "month": f"Forecast+{i+1}",
            "cash_flow": avg_cf,
        }
        for i in range(horizon_months)
    ]

    return {
        "historical": cash_flow,
        "avg_monthly_cash_flow": avg_cf,
        "forecast": forecast,
    }
