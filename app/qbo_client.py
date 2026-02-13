import requests
from sqlalchemy.orm import Session

from .models import QBOToken
from .config import settings

class QBOClient:
    def __init__(self, access_token: str, realm_id: str):
        self.access_token = access_token
        self.realm_id = realm_id

        base_domain = (
            "sandbox-quickbooks.api.intuit.com"
            if settings.qbo_environment == "sandbox"
            else "quickbooks.api.intuit.com"
        )
        self.base_url = f"https://{base_domain}/v3/company/{self.realm_id}"

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def get_company_info(self):
        url = f"{self.base_url}/companyinfo/{self.realm_id}"
        resp = requests.get(url, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def query(self, query: str):
        url = f"{self.base_url}/query"
        params = {"query": query}
        resp = requests.get(url, headers=self._headers(), params=params)
        resp.raise_for_status()
        return resp.json()

def get_qbo_client_from_db(db: Session) -> QBOClient:
    """
    Get a QBOClient using the first stored token row (single-company use).
    """
    token = db.query(QBOToken).first()
    if not token:
        raise RuntimeError("No QBO tokens stored yet. Run /qbo/authorize first.")
    return QBOClient(access_token=token.access_token, realm_id=token.realm_id)
``
