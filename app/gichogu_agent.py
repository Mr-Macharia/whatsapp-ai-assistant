from agno.agent import Agent
from app.db import whatsapp_db
from agno.models.google import Gemini
from app.tools.composio import gichogu_composio_tools
from app.tools.search import brave_tools
from app.tools.search import serper_tools
from app.tools.memory import memory_manager
from app.prompts import gichogu_instructions, get_gichogu_instructions
from app.tools.automations import gichogu_scheduler

tools = [*gichogu_composio_tools, serper_tools, gichogu_scheduler]


gichogu_agent = Agent(
    id="gichogu-assistant",
    name="Gichogu Assistant",
    model=Gemini(
        id="gemini-3.5-flash"
    ),
    db=whatsapp_db,
    tools=tools,
    learning=True,
    instructions=get_gichogu_instructions(),
    add_history_to_context=True,
    num_history_runs=5,
    tool_call_limit=5,
    markdown=False,
)
