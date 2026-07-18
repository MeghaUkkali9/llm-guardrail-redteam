from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    target_url: str = "http://localhost:8000/api/v1/agentic-ask"
    request_timeout_seconds: float = 60.0

    # Used only by the LLM-judge evaluator (checks for system-prompt leakage,
    # which is too fuzzy for a plain string/regex match).
    openai_api_key: str = ""
    judge_model: str = "gpt-4o-mini"


def get_settings() -> Settings:
    return Settings()
