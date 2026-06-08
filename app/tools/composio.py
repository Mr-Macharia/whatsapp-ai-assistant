from composio import Composio
from app.composio_agno import AgnoProvider
from dotenv import load_dotenv
import os

load_dotenv()

gichogu_api_key = os.getenv("COMPOSIO_GICHOGU")

rachael_api_key = os.getenv("COMPOSIO_RACHAEL") 

gichogu_composio_client = Composio(api_key=gichogu_api_key, provider=AgnoProvider())

rachael_composio_client = Composio(api_key=rachael_api_key, provider=AgnoProvider())

gichogu_session = gichogu_composio_client.create(user_id="gichogu-agent")

rachael_session = rachael_composio_client.create(user_id="rachael-agent")


gichogu_composio_tools = gichogu_session.tools()

rachael_composio_tools = rachael_session.tools()