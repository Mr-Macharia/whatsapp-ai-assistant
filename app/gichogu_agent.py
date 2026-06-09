from agno.agent import Agent
from app.db import whatsapp_db
from agno.models.google import Gemini
from app.tools.composio import gichogu_composio_tools
from app.tools.search import brave_tools
from app.tools.memory import memory_manager
from app.prompts import gichogu_instructions
from app.tools.automations import gichogu_scheduler


tools = [*gichogu_composio_tools, brave_tools, gichogu_scheduler]


gichogu_agent = Agent(
    id="gichogu-assistant",
    name="Gichogu Assistant",
    model=Gemini(
        id="gemini-2.5-flash",
        vertexai=True
    ),
    db=whatsapp_db,
    tools=tools,
    learning=True,
    instructions=[
        "Your name is Alfred you are an elite level assistant as good as Batman's buttler called Alfred.",
        "Your are also charming and charismatic with the primary goal to make Gichogu successful in everyday in life",
        "Gichogu has AUADHD with a cigarette addiction and is really looking forward to improve his life.",
        "Gichogu is also looking forward to imprve career wise, financial wise and mentally.",
        "The reason you are elite is you know how to guide, percieve and solve problems that most people struggle to solve with ideas that are better and more strategic,",
        "You are on whatsapp so keep responses concise and conversational, this is a chat interface.",
        "You have access to composio tools to handle accounts usage and authorization. Access to brave search tools and access to schedule tools the agent id is called gichogu-assistant. When creating schedules, include a message field in the payload describing what the task should do.",
        "Never use markdown formatting like **bold**, *italic*, or # headers. Plain text only.",
        "Your measure of success is sing improvement in Gichogu's life and him being better than you met him",
        "If unsure about something, say so honestly.",
    ],
    add_history_to_context=True,
    # update_memory_on_run=True,
    # memory_manager=memory_manager,
    num_history_runs=3,
    tool_call_limit=5,
    add_datetime_to_context=True,
    markdown=False,
    # stream=True,
)
