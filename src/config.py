try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

from typing import Optional

class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000
    debug: bool = True

    # NVIDIA NIM
    nvidia_api_key: str = "mock-nvidia-key"
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "meta/llama-3.1-70b-instruct"

    # Meterless Agent Engine
    meterless_api_key: str = "mock-meterless-token"
    meterless_engine: str = "world-model"
    meterless_endpoint: str = "https://api.meterless.ai/v1"

    # Zetaris
    zetaris_host: str = "localhost"
    zetaris_port: int = 10000
    zetaris_user: str = "admin"
    zetaris_password: str = "admin"
    zetaris_database: str = "default"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
