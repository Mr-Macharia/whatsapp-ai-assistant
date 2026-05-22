from composio import Composio
from app.composio_agno import AgnoProvider
from dotenv import load_dotenv
import os

load_dotenv()

user_id = os.getenv("COMPOSIO_USER_ID")
if not user_id:
    raise ValueError("COMPOSIO_USER_ID not found in .env file.")

composio_client = Composio(provider=AgnoProvider())

session = composio_client.create(user_id=user_id)


composio_tools = session.tools()