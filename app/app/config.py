import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class Settings(BaseModel):
    qbo_client_id: str = os.getenv("QBO_CLIENT_ID", "")
    qbo_client_secret: str = os.getenv("QBO_CLIENT_SECRET", "")
    qbo_redirect_uri: str = os.getenv("QBO_REDIRECT_URI", "")
    qbo_environment: str = os.getenv("QBO_ENVIRONMENT", "sandbox")
    database_url: str = os.getenv("DATABASE_URL", "")

    @property
    def intuit_auth_base(self):
        return "https://appcenter.intuit.com/connect/oauth2"

    @property
    def intuit_token_endpoint(self):
        return "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

settings = Settings()
