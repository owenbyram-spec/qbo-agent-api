import base64
from datetime import datetime, timedelta
import secrets
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import QBOToken

router = APIRouter(prefix="/qbo", tags=["QBO Auth"])

# Temporary in-memory store for OAuth state (OK for single internal user)
oauth_state_store: dict[str, bool] = {}

def get_basic_auth_header(client_id: str, client_secret: str) -> str:
    token = f"{client_id}:{client_secret}"
    b64_token = base64.b64encode(token.encode()).decode()
    return f"Basic {b64_token}"

@router.get("/authorize")
def authorize():
    """
    Redirect user to QuickBooks Online OAuth consent screen.
    """
    if not settings.qbo_client_id or not settings.qbo_redirect_uri:
        raise HTTPException(status_code=500, detail="QBO OAuth not configured properly.")

    state = secrets.token_urlsafe(16)
    oauth_state_store[state] = True

    params = {
        "client_id": settings.qbo_client_id,
        "redirect_uri": settings.qbo_redirect_uri,
        "response_type": "code",
        "scope": "com.intuit.quickbooks.accounting",
        "state": state,
    }

    auth_url = f"{settings.intuit_auth_base}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/callback")
def callback(
    request: Request,
    code: str,
    state: str,
    realmId: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Handles Intuit redirect, exchanges code → access_token + refresh_token,
    and stores them in Postgres.
    """
    if state not in oauth_state_store:
        raise HTTPException(status_code=400, detail="Invalid OAuth state.")
    oauth_state_store.pop(state, None)

    headers = {
        "Authorization": get_basic_auth_header(
            settings.qbo_client_id,
            settings.qbo_client_secret,
        ),
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.qbo_redirect_uri,
    }

    token_resp = requests.post(
        settings.intuit_token_endpoint,
        headers=headers,
        data=data,
    )

    if not token_resp.ok:
        raise HTTPException(
            status_code=token_resp.status_code,
            detail=f"Token exchange failed: {token_resp.text}",
        )

    token_data = token_resp.json()

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in")
    refresh_expires_in = token_data.get("x_refresh_token_expires_in")

    if not access_token or not refresh_token or not realmId:
        raise HTTPException(status_code=500, detail="Missing token or realmId.")

    now = datetime.utcnow()
    access_expires_at = now + timedelta(seconds=expires_in or 3600)
    refresh_expires_at = now + timedelta(seconds=refresh_expires_in or 86400)

    existing = db.query(QBOToken).filter(QBOToken.realm_id == realmId).first()

    if existing:
        existing.access_token = access_token
        existing.refresh_token = refresh_token
        existing.access_expires_at = access_expires_at
        existing.refresh_expires_at = refresh_expires_at
    else:
        db.add(
            QBOToken(
                realm_id=realmId,
                access_token=access_token,
                refresh_token=refresh_token,
                access_expires_at=access_expires_at,
                refresh_expires_at=refresh_expires_at,
            )
        )

    db.commit()

    return {
        "message": "OAuth successful; tokens stored in Postgres.",
        "realmId": realmId,
        "access_expires_at": access_expires_at.isoformat(),
    }
