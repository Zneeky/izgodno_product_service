from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    GROQ_API_KEY: str
    GROQ_API_URL: str
    GROQ_MODEL: str

    class Config:
        env_file = ".env"

settings = Settings()
