import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    memory_url: str = os.getenv("MEMORY_DATABASE_URL", "sqlite:///./jarvis-dev.sqlite3")
    operational_url: str = os.getenv("OPERATIONAL_DATABASE_URL", "")
    environment: str = os.getenv("APP_ENV", "development")
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    model: str = os.getenv("OPENAI_MODEL", "")
    allow_external: bool = os.getenv("ALLOW_EXTERNAL_AI", "false").lower() == "true"
    allow_search: bool = os.getenv("ALLOW_EXTERNAL_SEARCH", "false").lower() == "true"
    bridge_token: str = os.getenv("BRIDGE_TOKEN", "")
    rm: str = os.getenv("REGIONAL_NAME", "ORLEAN DA SILVA DO NASCIMENTO")
    # Must be approved after checking source history; fail closed until then.
    approved: str = os.getenv("APPROVED_INDICATORS", "")
    rate_limit: int = int(os.getenv("REQUESTS_PER_MINUTE", "30"))
    retention_days: int = int(os.getenv("RETENTION_DAYS", "365"))

    def validate(self):
        if self.environment == "production":
            if not self.memory_url.startswith("postgresql+psycopg://"):
                raise ValueError("Produção exige PostgreSQL para memória.")
            if len(self.bridge_token) < 32:
                raise ValueError("Configure BRIDGE_TOKEN com pelo menos 32 caracteres.")
        if self.operational_url and self.operational_url == self.memory_url:
            raise ValueError(
                "Use credenciais distintas para memória e leitura operacional."
            )
