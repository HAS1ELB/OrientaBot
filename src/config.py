import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class AppConfig:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama3-70b-8192")
    default_lang: str = os.getenv("APP_DEFAULT_LANG", "fr")

    @property
    def is_configured(self) -> bool:
        return bool(self.groq_api_key)