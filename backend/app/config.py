"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All config loaded from environment variables."""

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # Anthropic
    anthropic_api_key: str = ""

    # Stripe (optional until Stripe account is set up)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = ""

    # Google Sheets (waitlist)
    google_service_account_json: str = ""  # full JSON string from service account key file
    google_sheet_id: str = ""  # ID from the Sheet URL

    # App
    frontend_url: str = "http://localhost:3000"
    environment: str = "development"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
