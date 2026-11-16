from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    allow_origins: str = "http://localhost:5173"

    # Abstract API — email deliverability (SMTP RCPT TO probing via their service)
    # Leave empty to disable. Get your free key at:
    # https://app.abstractapi.com/users/signup → Email Validation API
    # Free tier: 100 requests/month. No credit card required.
    abstract_api_key: str = ""

    # CSV limits
    max_csv_bytes: int = 2_097_152        # 2 MB
    max_csv_rows: int = 1_000
    max_running_jobs: int = 2
    max_waiting_jobs: int = 3
    job_result_ttl_seconds: int = 900     # 15 min after READY
    failed_job_ttl_seconds: int = 60      # 1 min after FAILED
    max_job_lifetime_seconds: int = 1_800 # 30-min hard cap
    dns_timeout_seconds: float = 3.0
    dns_concurrency: int = 20
    rate_single_per_min: int = 20
    rate_bulk_per_hour: int = 5
    memory_guard_mb: int = 380            # [verify in C7]

settings = Settings()
