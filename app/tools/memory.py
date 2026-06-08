import os
from agno.memory import MemoryManager
from agno.models.openai.like import OpenAILike
from app.db import whatsapp_db

api_key=os.getenv("DIGITAL_OCEAN_MODEL_ACCESS_KEY")

memory_manager = MemoryManager(
    db = whatsapp_db,
    model=OpenAILike(
        id="openai-gpt-oss-20b",
        api_key=api_key,
        base_url="https://inference.do-ai.run/v1/",
    ),
    additional_instructions="Keep the memory short and simple"
)