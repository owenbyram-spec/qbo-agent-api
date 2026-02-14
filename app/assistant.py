import os
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from openai import OpenAI, RateLimitError

from .db import get_db
from .qbo_client import get_qbo_client_from_db
from .analysis.vendor_spend import vendor_spend_summary

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class AssistantQuery(BaseModel):
    question: str
    realm_id: str  # now used to select the company


@router.post("/query")
def ask_ai(body: AssistantQuery, db: Session = Depends(get_db)):
    # Use the selected company (realm_id)
    qbo = get_qbo_client_from_db(db, body.realm_id)

    # Example analysis: vendor spend
    vendor_data = vendor_spend_summary(qbo)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or gpt-4.1 if available
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert financial analyst. "
                        "Use the provided QuickBooks data to answer the user's question. "
                        "Be concise, clear, and business-focused."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"User question: {body.question}\n\n"
                        f"Vendor spend data (JSON): {vendor_data}"
                    ),
                },
            ],
        )
        # OpenAI v2 style: message.content, not ["content"]
        answer = response.choices[0].message.content
    except RateLimitError:
        answer = (
            "The AI analysis is temporarily unavailable due to OpenAI rate limits "
            "or quota. Here is the raw vendor data instead."
        )

    return {
        "answer": answer,
        "data_used": vendor_data,
    }
