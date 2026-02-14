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
    realm_id: str

@router.post("/query")
def ask_ai(body: AssistantQuery, db: Session = Depends(get_db)):
    realm_id = body.realm_id
    question = body.question

    qbo = get_qbo_client_from_db(db, realm_id)

    # Minimal example analysis
    vendor_data = vendor_spend_summary(qbo)

    # LLM reasoning
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system",
             "content": "You are an expert financial analyst."},
            {"role": "user",
             "content": f"Question: {question}\nData: {vendor_data}"}
        ]
    )

    answer = response.choices[0].message["content"]
    return {"answer": answer, "data_used": vendor_data}
