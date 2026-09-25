"""Central, environment-driven configuration.

Every value can be overridden via environment variables or a `.env` file
(see `.env.example`). Nothing environment-specific is hard-coded in tests.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- UI (Sauce Demo) ---
    ui_base_url: str = "https://www.saucedemo.com"
    ui_standard_user: str = "standard_user"
    ui_locked_user: str = "locked_out_user"
    ui_password: str = "secret_sauce"
    browser_executable_path: str | None = None

    # --- API (Restful Booker) ---
    api_base_url: str = "https://restful-booker.herokuapp.com"
    api_username: str = "admin"
    api_password: str = "password123"

    # --- SQL ---
    db_path: str = ":memory:"

    # --- AI: chatbot under test (open-source model served by Ollama) ---
    ollama_host: str = "http://localhost:11434"
    chatbot_model: str = "qwen2.5:1.5b"
    chatbot_temperature: float = 0.0
    chatbot_seed: int = 42
    chatbot_timeout_s: int = 180

    # --- AI: evaluation ---
    # Judge is intentionally a different model family from the bot to reduce self-preference bias.
    judge_model: str = "llama3.2:3b"
    # Ragas' structured prompts need a stronger judge; its tests skip if this model isn't pulled.
    ragas_judge_model: str = "qwen2.5:7b"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    similarity_threshold: float = 0.70
    faithfulness_threshold: float = 0.70


@lru_cache
def get_settings() -> Settings:
    return Settings()
