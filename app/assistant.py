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
    realm_id: str  # currently unused, kept for future multi-company support

@router.post("/query")
def ask_ai(body: AssistantQuery, db: Session = Depends(get_db)):
    # Get QBO client (currently first token / sandbox)
    qbo = get_qbo_client_from_db(db)

    # Pull vendor spend data from QBO
    vendor_data = vendor_spend_summary(qbo)

    # Call OpenAI, but fail gracefully if quota hits again
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # adjust if you have a different model
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert financial analyst. "
                        "Use the provided QuickBooks vendor spend data "
                        "to answer the user's question. "
                        "Be concise and business-focused."
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

        # ✅ Correct way to get the content with OpenAI v2 client
        answer = response.choices[0].message.content

    except RateLimitError:
        answer = (
            "The AI analysis is temporarily unavailable because the OpenAI API "
            "returned a rate limit or quota error. Here is the raw vendor data instead."
        )

    return {
        "answer": answer,
        "data_used": vendor_data,
    }
