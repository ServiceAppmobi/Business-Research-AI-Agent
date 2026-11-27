from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    tavily_api_key: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    resend_api_key: str = ""
    email_from: str = ""
    product_currency: str = "pln"
    research_report_price_minor: int = 4900
    app_base_url: str = "http://localhost:8000"
    database_path: str = "./data/research_orders.sqlite3"
    app_env: str = "development"
    allow_direct_ai_api: bool = False
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
