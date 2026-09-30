from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://alvo:alvo@localhost:5432/alvo_leiloes"
    api_bearer_token: str = "dev-token-troque-em-producao"
    allowed_origins: str = ""
    """Origens extras liberadas no CORS em produção, separadas por vírgula
    (ex.: "https://alvo-leiloes.pages.dev"). Localhost já é liberado via regex."""

    @field_validator("database_url")
    @classmethod
    def _forca_driver_psycopg3(cls, v: str) -> str:
        """Neon (e outros provedores) fornecem a connection string sem o driver
        explícito (`postgresql://...`), o que faz o SQLAlchemy tentar psycopg2 —
        não instalado, já que este projeto usa psycopg 3. Normaliza para
        `postgresql+psycopg://` independente do que vier na env var."""
        for prefixo in ("postgresql://", "postgres://"):
            if v.startswith(prefixo):
                return "postgresql+psycopg://" + v[len(prefixo):]
        return v

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
