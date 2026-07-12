import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """תצורה מרכזית. ניתנת לשינוי דרך משתני סביבה, שימושי ב-CI."""

    host: str = os.environ.get("SUT_HOST", "127.0.0.1")
    port: int = int(os.environ.get("SUT_PORT", "8000"))
    username: str = os.environ.get("SUT_USERNAME", "demo")
    password: str = os.environ.get("SUT_PASSWORD", "demo123")

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


settings = Settings()