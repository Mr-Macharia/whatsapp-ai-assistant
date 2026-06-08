from agno.tools.scheduler import SchedulerTools
from app.db import whatsapp_db
from app.config import settings

scheduler_tools = SchedulerTools(
    db = whatsapp_db,
    default_timezone="Africa/Nairobi"
)