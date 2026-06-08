from agno.agent import Agent
from agno.os import AgentOS
from agno.db.sqlite import SqliteDb
from agno.models.google import Gemini
import os
from app.tools.composio import composio_tools
from app.tools.search import brave_tools
from dotenv import load_dotenv

load_dotenv()


tools = [*composio_tools, brave_tools]


agent_db = SqliteDb(
    session_table="test_sessions",
    db_file="tmp/test_agent.db",
)

test_agent = Agent(
    name="WhatsApp Assistant",
    model=Gemini(
        id="gemini-3.5-flash",
        vertexai=True
    ),
    db=agent_db,
    tools=tools,
    instructions=[
        "You are a helpful WhatsApp assistant.",
        "Keep responses concise and conversational, this is a chat interface.",
        "You have access to composio tools to handle accounts usage and authorization.",
        "Never use markdown formatting like **bold**, *italic*, or # headers. Plain text only.",
        "Do not add sign-offs or your name at the end of messages.",
        "If unsure about something, say so honestly.",
    ],
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=False,
    # stream=True,
)

test_agent_os = AgentOS(agents=[test_agent])
test_app = test_agent_os.get_app()

if __name__ == "__main__":
    test_agent_os.serve(app="test:test_app", reload=True)

