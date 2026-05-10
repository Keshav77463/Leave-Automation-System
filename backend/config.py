from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ERPNext
    erpnext_url: str
    erpnext_api_key: str
    erpnext_api_secret: str

    # Employee
    employee_id: str
    department: str

    # Groq
    groq_api_key: str

    # App
    app_name: str = "Leave Request Automation"
    app_version: str = "1.0.0"


settings = Settings()