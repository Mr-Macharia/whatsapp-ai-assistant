from agno.agent import Agent
from app.db import whatsapp_db
from agno.models.google import Gemini
from app.tools.composio import rachael_composio_tools
from app.tools.search import brave_tools
from app.tools.memory import memory_manager
from app.prompts import rachael_instructions
from app.tools.automations import rachael_scheduler
from dotenv import load_dotenv

load_dotenv()


tools = [*rachael_composio_tools, brave_tools, rachael_scheduler]


rachael_agent = Agent(
    id="rachael-assistant",
    name="Rachael's Assistant",
    model=Gemini(
        id="gemini-3-flash-preview",
        vertexai=True
    ),
    db=whatsapp_db,
    learning=True,
    tools=tools,
    instructions=rachael_instructions,
    add_history_to_context=True,
    # update_memory_on_run=True,
    # memory_manager=memory_manager,
    num_history_runs=5,
    add_datetime_to_context=True,
    markdown=False,
    # stream=True,
)
