from agno.db.postgres import PostgresDb
from app.config import settings


whatsapp_db = PostgresDb(
    db_url=settings.DATABASE_URL,
    session_table="whatsapp_sessions",
    memory_table="whatsapp_memories",
)




