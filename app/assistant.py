import os
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from openai import OpenAI

from .db import get_db
from .qbo_client import get_qbo_client_from_db
from .analysis.vendor_spend import vendor_spend_summary

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class AssistantQuery(BaseModel):
    question: str
    realm_id: str  # kept for future multi-company; not used yet

@router.post("/query")
def ask_ai(body: AssistantQuery, db: Session = Depends(get_db)):
    # For now, ignore realm_id and just use the first (sandbox) company from DB
    qbo = get_qbo_client_from_db(db)

    # Run one analysis as an example (vendor spend)
    vendor_data = vendor_spend_summary(qbo)

    # Ask the LLM to interpret this data in light of the question
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or "gpt-4.1" if your account has it
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
                "content": f"User question: {body.question}\n\nVendor spend data: {vendor_data}",
            },
        ],
    )

    answer = response.choices[0].message["content"]

    return {
        "answer": answer,
        "data_used": vendor_data,
    }
