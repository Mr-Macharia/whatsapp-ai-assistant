import os
from agno.agent import Agent
from app.db import whatsapp_db
from agno.models.google import Gemini
from app.tools.composio import rachael_composio_tools
from agno.models.openai.like import OpenAILike
from app.tools.search import brave_tools
from app.tools.memory import memory_manager
from app.prompts import rachael_instructions, get_rachael_instructions
from app.tools.automations import rachael_scheduler
from dotenv import load_dotenv

load_dotenv()

api_key=os.getenv("DIGITAL_OCEAN_MODEL_ACCESS_KEY")

tools = [*rachael_composio_tools, brave_tools, rachael_scheduler]


rachael_agent = Agent(
    id="rachael-assistant",
    name="Rachael's Assistant",
    model=OpenAILike(
        id="openai-gpt-oss-20b",
        api_key=api_key,
        base_url="https://inference.do-ai.run/v1/",
    ),
    db=whatsapp_db,
    learning=True,
    tools=tools,
    instructions=get_rachael_instructions(),
    add_history_to_context=True,
    tool_call_limit=5,
    num_history_runs=5,
    markdown=False,
)
