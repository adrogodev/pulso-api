from pydantic_settings import BaseSettings

class EnvSettings(BaseSettings):
    # System
    MUSIC_SOURCE_LINK: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = EnvSettings()