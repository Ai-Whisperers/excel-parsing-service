"""
Configuration settings
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    java_layer_url: str = "http://localhost:8080"
    max_file_size_mb: int = 100
    arrow_compression: str = "zstd"  # Options: zstd, lz4, snappy, gzip, none

    # Arrow Flight settings
    flight_host: str = "0.0.0.0"
    flight_port: int = 8815

    # REST API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
