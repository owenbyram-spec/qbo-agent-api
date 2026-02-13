from ..qbo_client import QBOClient

def _extract_amount(cell: dict) -> float:
    try:
        return float(cell.get("value", "0") or 0)
    except Exception:
        return 0.0

def profit_and_margin_by_month(qbo_client: QBOClient):
    """
    Uses the ProfitAndLoss report summarized by month to compute:
      - income, COGS, gross profit, and gross margin % per month.
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
    col_keys = [c.get("ColTitle", "") for c in cols]

    income_by_month = [0.0] * len(col_keys)
    cogs_by_month = [0.0] * len(col_keys)

    for row in report.get("Rows", {}).get("Row", []):
        if row.get("type") != "Section":
            continue

        section_title = row.get("Header", {}).get("ColData", [{}])[0].get("value", "")
        rows = row.get("Rows", {}).get("Row", [])

        # Income section
        if "Income" in section_title:
            for r in rows:
                cells = r.get("ColData", [])
                for i, cell in enumerate(cells[1:], start=0):
                    income_by_month[i] += _extract_amount(cell)

        # COGS section (Cost of Goods Sold)
        if "Cost of Goods Sold" in section_title:
            for r in rows:
                cells = r.get("ColData", [])
                for i, cell in enumerate(cells[1:], start=0):
                    cogs_by_month[i] += _extract_amount(cell)

    result = []
    for i, month_label in enumerate(col_keys):
        inc = income_by_month[i]
        cogs = cogs_by_month[i]
        gross = inc - cogs
        margin_pct = (gross / inc * 100.0) if inc else 0.0
        result.append(
            {
                "month": month_label,
                "income": inc,
                "cogs": cogs,
                "gross_profit": gross,
                "gross_margin_pct": margin_pct,
            }
        )

    return {
        "months": result,
        "total_income": sum(income_by_month),
        "total_cogs": sum(cogs_by_month),
        "total_gross_profit": sum(income_by_month) - sum(cogs_by_month),
    }
