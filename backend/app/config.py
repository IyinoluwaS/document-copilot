from pathlib import Path
from typing import Annotated

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Resolved from this file so the app and Alembic find .env regardless of cwd.
    # On Railway there is no .env file; values come from the service's env vars.
    # Validation errors would otherwise echo secret values into startup logs.
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", hide_input_in_errors=True
    )

    supabase_url: str
    supabase_anon_key: SecretStr
    supabase_service_role_key: SecretStr

    database_url: SecretStr

    openai_api_key: SecretStr
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    allowed_origins: Annotated[list[str], NoDecode]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def split_origins(cls, value: str) -> list[str]:
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    @field_validator("database_url")
    @classmethod
    def reject_transaction_pooler(cls, value: SecretStr) -> SecretStr:
        # Migrations and index builds need session-level behavior that the
        # transaction pooler (port 6543) doesn't provide.
        if ":6543/" in value.get_secret_value():
            raise ValueError(
                "use the direct or session connection, not the transaction pooler (port 6543)"
            )
        return value


settings = Settings()
