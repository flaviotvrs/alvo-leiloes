from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://alvo:alvo@localhost:5432/alvo_leiloes"
    api_bearer_token: str = "dev-token-troque-em-producao"
    allowed_origins: str = ""
    """Origens extras liberadas no CORS em produção, separadas por vírgula
    (ex.: "https://alvo-leiloes.pages.dev"). Localhost já é liberado via regex."""

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
