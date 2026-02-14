from typing import Optional, Dict, Any
import requests
from sqlalchemy.orm import Session

from .config import settings
from .models import QBOToken


class QBOClient:
    """
    Thin wrapper around the QuickBooks Online Accounting API for a single company.
    """

    def __init__(self, access_token: str, realm_id: str):
        self.access_token = access_token
        self.realm_id = realm_id

        base_domain = (
            "sandbox-quickbooks.api.intuit.com"
            if settings.qbo_environment == "sandbox"
            else "quickbooks.api.intuit.com"
        )
        self.base_url = f"https://{base_domain}/v3/company/{self.realm_id}"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def get_company_info(self) -> Dict[str, Any]:
        """
        Fetch high-level company info, including CompanyName.
        """
        url = f"{self.base_url}/companyinfo/{self.realm_id}"
        resp = requests.get(url, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def query(self, query: str) -> Dict[str, Any]:
        """
        Run a QuickBooks SQL-like query, e.g.:

            SELECT * FROM Invoice STARTPOSITION 1 MAXRESULTS 50
        """
        url = f"{self.base_url}/query"
        params = {"query": query}
        resp = requests.get(url, headers=self._headers(), params=params)
        resp.raise_for_status()
        return resp.json()

    def get_report(
        self,
        report_name: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call a QuickBooks Online report endpoint, e.g. ProfitAndLoss.

        Example:
            client.get_report(
                "ProfitAndLoss",
                {"date_macro": "ThisFiscalYearToDate", "summarize_column_by": "Month"}
            )
        """
        url = f"{self.base_url}/reports/{report_name}"
        resp = requests.get(url, headers=self._headers(), params=params or {})
        resp.raise_for_status()
        return resp.json()


def get_qbo_client_from_db(
    db: Session,
    realm_id: Optional[str] = None
) -> QBOClient:
    """
    Return a QBOClient for the given realm_id, or the first token if realm_id is None.

    This supports:
      - Single-company usage (no realm_id passed)
      - Multi-company switching (realm_id provided from the UI or assistant)
    """
    query = db.query(QBOToken)

    if realm_id:
        token = query.filter(QBOToken.realm_id == realm_id).first()
    else:
        token = query.first()

    if not token:
        raise RuntimeError(
            "No QBO tokens stored yet. Run /qbo/authorize at least once to connect "
            "a QuickBooks company."
        )

    return QBOClient(access_token=token.access_token, realm_id=token.realm_id)
