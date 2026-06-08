import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    ALLOWED_NUMBERS = [num.strip() for num in os.getenv("ALLOWED_NUMBERS", "").split(",") if num.strip()]
    GICHOGU_NUMBER  = os.getenv("GICHOGU_NUMBER", "")
    RACHAEL_NUMBER  = os.getenv("RACHAEL_NUMBER", "")
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
    EVO_BASE_URL   = os.getenv("EVO_BASE_URL", "http://localhost:8080")
    EVO_API_KEY    = os.getenv("EVO_API_KEY", "")
    EVO_INSTANCE   = os.getenv("EVO_INSTANCE", "my-agent")
    XAI_API_KEY    = os.getenv("XAI_API_KEY", "")
    DATABASE_URL   = os.getenv("DATABASE_URL", "")
    SERVER_URL     = os.getenv("SERVER_URL", "")


settings = Settings()
