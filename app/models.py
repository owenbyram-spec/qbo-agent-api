from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from .db import Base   # <-- THIS is crucial: imports Base from db.py


class QBOToken(Base):
    """
    Stores QuickBooks Online OAuth tokens per QuickBooks company (realmId).
    """
    __tablename__ = "qbo_tokens"

    id = Column(Integer, primary_key=True, index=True)
    realm_id = Column(String, unique=True, index=True, nullable=False)

    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    access_expires_at = Column(DateTime, nullable=False)
    refresh_expires_at = Column(DateTime, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
