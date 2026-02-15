import os
from typing import Dict, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from openai import OpenAI, RateLimitError
from requests.exceptions import HTTPError

from .db import get_db
from .qbo_client import get_qbo_client_from_db

# Analysis packs
from .analysis.vendor_spend import vendor_spend_summary
from .analysis.customer_revenue import customer_revenue_summary
from .analysis.expense_trends import expense_trend_mom
from .analysis.profit_margin import profit_and_margin_by_month
from .analysis.cogs_anomaly import cogs_anomalies
from .analysis.cashflow_forecast import cashflow_forecast
from .analysis.ar_aging import ar_aging
from .analysis.anomalies import transaction_anomalies


router = APIRouter(prefix="/assistant", tags=["Peregrine CFO Assistant"])

# OpenAI client (v2 library)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class AssistantQuery(BaseModel):
    """
    Payload from the UI:
      - question: the natural language question
      - realm_id: which QuickBooks company to analyze
    """
    question: str
    realm_id: str


@router.post("/query")
def ask_peregrine(body: AssistantQuery, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Main AI endpoint for Peregrine CFO.

    1. Builds a QBO client for the requested company.
    2. Runs all analysis packs (vendor, customers, margins, COGS, CF, AR, anomalies).
    3. Sends the combined structured data + question to the LLM.
    4. Returns the answer + raw analyses for debugging/inspection.
    """

    # 1) Build QBO client for selected company
    qbo = get_qbo_client_from_db(db, body.realm_id)

    analyses: Dict[str, Any] = {}
    errors: Dict[str, str] = {}

    # Helper to run each pack defensively
    def run_pack(key: str, fn):
        try:
            analyses[key] = fn(qbo)
        except HTTPError as e:
            errors[key] = f"HTTP error from QBO: {e}"
        except Exception as e:
            errors[key] = f"Unexpected error: {e}"

    # 2) Run all analysis packs
    run_pack("vendor_spend", vendor_spend_summary)
    run_pack("customer_revenue", customer_revenue_summary)
    run_pack("expense_trends", expense_trend_mom)
    run_pack("profit_margins", profit_and_margin_by_month)
    run_pack("cogs_anomalies", cogs_anomalies)
    run_pack("cashflow_forecast", cashflow_forecast)
    run_pack("ar_aging", ar_aging)
    run_pack("transaction_anomalies", transaction_anomalies)

    # 3) Call LLM to interpret the data
    # If OpenAI quota is exhausted, fall back gracefully.
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or gpt-4.1 if your account has it
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Peregrine CFO — an advanced financial analysis agent. "
                        "You receive structured outputs from multiple QuickBooks analysis packs:\n"
                        "- vendor_spend\n"
                        "- customer_revenue\n"
                        "- expense_trends\n"
                        "- profit_margins\n"
                        "- cogs_anomalies\n"
                        "- cashflow_forecast\n"
                        "- ar_aging\n"
                        "- transaction_anomalies\n\n"
                        "Use ONLY the relevant parts of this data to answer the user's question. "
                        "Explain clearly, call out risks/opportunities, and keep the tone like a seasoned CFO."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"User question: {body.question}\n\n"
                        f"Here is the full analysis data as JSON:\n{analyses}\n\n"
                        f"If some packs failed, here are their errors:\n{errors}"
                    ),
                },
            ],
        )

        answer = response.choices[0].message.content

    except RateLimitError:
        answer = (
            "Peregrine CFO tried to run an AI analysis, but the OpenAI API reported "
            "an insufficient quota or rate limit. You can still inspect the raw data "
            "from each analysis pack in the 'analyses' field."
        )

    # 4) Return answer + raw data (useful for debugging or future UI features)
    return {
        "answer": answer,
        "analyses": analyses,
        "errors": errors,
    }
