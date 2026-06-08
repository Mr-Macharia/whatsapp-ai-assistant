from agno.agent import Agent
from app.db import whatsapp_db
from agno.models.google import Gemini
from app.tools.composio import gichogu_composio_tools
from app.tools.search import brave_tools
from app.tools.memory import memory_manager
from app.prompts import gichogu_instructions
from app.tools.automations import scheduler_tools


tools = [*gichogu_composio_tools, brave_tools, scheduler_tools]


gichogu_agent = Agent(
    id="gichogu-assistant",
    name="Gichogu Assistant",
    model=Gemini(
        id="gemini-3.5-flash",
        vertexai=True
    ),
    db=whatsapp_db,
    tools=tools,
    learning=True,
    instructions=gichogu_instructions,
    add_history_to_context=True,
    # update_memory_on_run=True,
    # memory_manager=memory_manager,
    num_history_runs=3,
    tool_call_limit=5,
    add_datetime_to_context=True,
    markdown=False,
    # stream=True,
)
