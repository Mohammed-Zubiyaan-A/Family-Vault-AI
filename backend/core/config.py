"""
Central settings. Per AGENTS.md: never hardcode a model name or endpoint
in code — always read from env vars, so switching is a config change.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Local model size ---
    OLLAMA_MODEL_LOCAL: str = "qwen3:4b"
    OLLAMA_HOST: str = "http://localhost:11434"

    # --- Local vs. cloud mode (two independent settings, do not conflate) ---
    OLLAMA_MODE: str = "local"  # "local" (default) or "cloud"
    OLLAMA_MODEL_CLOUD: str = "gemma4:31b-cloud"
    OLLAMA_API_KEY: str = ""
    # Without this, a slow/blocked network call to Ollama (local or cloud)
    # hangs forever with nothing surfaced to the user — this bounds it so
    # a failure becomes a visible error instead of a silent stall.
    OLLAMA_TIMEOUT_SECONDS: int = 120

    # --- Data stores ---
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/familyvault"
    GRAPH_DB_URL: str = "bolt://localhost:7687"  # unused until knowledge-graph stretch phase

    # --- Uploads ---
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_MB: int = 25

    # --- Embeddings ---
    EMBEDDING_MODEL: str = "BAAI/bge-m3"

    def validate_mode(self) -> None:
        if self.OLLAMA_MODE not in ("local", "cloud"):
            raise ValueError(
                f"OLLAMA_MODE must be 'local' or 'cloud', got {self.OLLAMA_MODE!r}"
            )
        if self.OLLAMA_MODE == "cloud" and not self.OLLAMA_API_KEY:
            raise ValueError(
                "OLLAMA_MODE=cloud requires OLLAMA_API_KEY to be set"
            )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_mode()
    return settings
