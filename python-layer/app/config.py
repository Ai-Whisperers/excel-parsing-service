"""
Configuration settings
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    java_layer_url: str = "http://localhost:8080"
    max_file_size_mb: int = 100
    arrow_compression: str = "zstd"  # Options: zstd, lz4, snappy, gzip, none

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
