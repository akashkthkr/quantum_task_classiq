import os
from pydantic import BaseModel


class Settings(BaseModel):
	postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
	postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
	postgres_db: str = os.getenv("POSTGRES_DB", "quantum")
	postgres_user: str = os.getenv("POSTGRES_USER", "quantum")
	postgres_password: str = os.getenv("POSTGRES_PASSWORD", "quantum")

	redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
	celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
	celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

	num_shots: int = int(os.getenv("NUM_SHOTS", "1024"))
	log_level: str = os.getenv("LOG_LEVEL", "INFO")

	@property
	def sqlalchemy_url(self) -> str:
		return (
			f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
			f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
		)


settings = Settings()  # singleton-like
