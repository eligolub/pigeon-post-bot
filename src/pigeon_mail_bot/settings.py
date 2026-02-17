from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    enable_json_store: bool = Field(default=True, alias="ENABLE_JSON_STORE")

    bot_token: str = Field(alias="BOT_TOKEN")
    channel_id: int = Field(alias="CHANNEL_ID")

    google_sa_json: str | None = Field(default=None, alias="GOOGLE_SA_JSON")
    google_sheet_id: str | None = Field(default=None, alias="GOOGLE_SHEET_ID")
    google_sheet_tab: str = Field(default="Sheet1", alias="GOOGLE_SHEET_TAB")
    google_sa_json_content: str | None = Field(default=None, alias="GOOGLE_SA_JSON_CONTENT")



def get_settings() -> Settings:
    return Settings()
