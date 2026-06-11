# Multi-Agent WhatsApp AI Assistant

This repository contains a production-grade, multi-agent WhatsApp AI Assistant designed to process incoming chat messages, execute context-aware reasoning, call external APIs and search engines, and run autonomous scheduled automations.

The system is built using the Agno agentic framework, FastAPI for webhook handling and routing, PostgreSQL for long-term agent session and memory storage, and the Evolution API for WhatsApp gateway connectivity.

---

## System Architecture and Flow

```mermaid
graph TD
    A[User Phone] -->|WhatsApp Message| B[Evolution API Gateway]
    B -->|HTTP POST Webhook| C[FastAPI Server]
    C -->|Background Task| D[Agent Router]
    D -->|Instantiates Agent Profile| E[Agno Agent]
    E -->|Fetch History / Facts| F[(PostgreSQL Database)]
    E -->|Execute Web Queries| G[Brave / Serper Search]
    E -->|Invoke Third-Party APIs| H[Composio OAuth Gateway]
    E -->|Return Reply Text| C
    C -->|HTTP POST Send| B
    B -->|WhatsApp Message| A
```

### The Message Lifecycle

1. **Ingress**: A user sends a text message to one of the WhatsApp accounts managed by the Evolution API gateway.
2. **Webhook Dispatch**: The gateway intercepts the message and posts a JSON payload to the FastAPI backend's `/webhook/whatsapp` endpoint.
3. **Validation & Filtering**: FastAPI verifies the sender using `ALLOWED_NUMBERS` config filters and validates the incoming signature using a webhook secret key.
4. **Background Hand-Off**: FastAPI offloads processing to a background task so it can return an immediate `200 OK` HTTP status response back to the gateway.
5. **Agent Routing**: The server resolves which agent profile to load based on the destination phone number.
6. **Context Enrichment**: The app stamps the system instructions dynamically with the current Kenya local time (East Africa Time, EAT) using `Africa/Nairobi`.
7. **Execution and Tool Usage**: Agno loads the short-term conversation thread from PostgreSQL, passes the prompt to the language model, and handles intermediate tool executions (web searches or Composio API integrations).
8. **Egress**: The generated response is posted back to the Evolution API via an asynchronous HTTP client (`httpx`) and delivered to the user.

---

## Key Core Modules and Features

### 1. Non-Blocking Async Network I/O
The system uses `httpx.AsyncClient` inside `_evo_send_text_async` for WhatsApp outgoing messages. Because FastAPI operates on a single-threaded event loop, using standard synchronous libraries (such as `requests`) would freeze the entire server thread during the duration of network calls. Async operations ensure the server remains responsive to multiple simultaneous webhooks or automated triggers.

### 2. Timezone-Aware Context Injection
Large Language Models (LLMs) lack an internal clock and do not track local time changes. To ensure scheduling and chronological references remain accurate, the instructions are dynamically updated at execution time with a current Kenya local time stamp:
```python
now = datetime.now(ZoneInfo("Africa/Nairobi"))
```
This forces the model to reason using Kenyan time boundaries, regardless of where the application container or cloud service is deployed.

### 3. Custom Composio Bridge
The application integrates with [Composio](https://composio.dev) to manage API authorizations with external systems (such as GitHub or Google Workspace). To solve Pydantic schema validation mismatches within the default Agno toolkit wrappers, a custom provider wrapper is implemented in `app/composio_agno/provider.py`. It dynamically intercepts, corrects, and maps the schemas to make them fully compatible with the model's tool calls.

### 4. Database Memory Management
Persistent memory is divided into two distinct scopes managed in PostgreSQL:
* **Short-Term Session Memory**: Standard message histories stored in the `whatsapp_sessions` table. This keeps the immediate context of the conversation active.
* **Long-Term Memory**: The `whatsapp_memories` table stores structured, synthesized facts learned over time (e.g., user preferences or goals).

### 5. Automated Task Scheduler
The system subclass `WhatsAppSchedulerTools` overrides standard Agno scheduling behavior. Instead of triggering local developer prompts, it maps schedules directly to a secure endpoint on the FastAPI app (`/scheduled-run/{agent_id}`). When a scheduled task fires:
1. The FastAPI endpoint is hit.
2. The server loads the correct agent configuration and constructs a task-execution prompt.
3. The agent executes the goal in the background.
4. The result is pushed directly to the user's WhatsApp.

---

## Project Directory Structure

```bash
whatsapp-agent/
├── app/
│   ├── composio_agno/        # Dynamic schema patches for Composio toolsets
│   │   ├── __init__.py
│   │   └── provider.py       # Custom provider class matching Agno signature logic
│   ├── tools/                # Extensible tool modules for agents
│   │   ├── __init__.py
│   │   ├── automations.py    # Custom scheduler wrapper pointing to FastAPI
│   │   ├── composio.py       # Composio clients and session creators
│   │   ├── memory.py         # Memory manager client declarations
│   │   ├── search.py         # Google Serper (Kenya-focused) and Brave search tools
│   │   └── whatsapp.py       # Synchronous and asynchronous message sending logic
│   ├── agent_profile_1.py    # Configuration, models, and tools for Agent 1
│   ├── agent_profile_2.py    # Configuration, models, and tools for Agent 2
│   ├── config.py             # Settings manager loading variables from environment
│   ├── db.py                 # PostgreSQL database session configurations
│   ├── prompts.py            # Instruction builders and timezone handlers
│   └── webhook.py            # FastAPI route handlers, webhooks, and scheduler APIs
├── scripts/
│   └── setup_webhook.py      # Script to register webhook routes with Evolution API
├── main.py                   # Entry point for production execution
├── pyproject.toml            # Package dependency declarations
├── uv.lock                   # Lock file for environment reproducibility
└── .env.example              # Template configuration file
```

---

## Installation and Setup

### Prerequisites
* Python 3.13 or newer
* PostgreSQL Database
* Evolution API (running inside Docker/Cloud)
* uv (recommended python environment manager)

### Step 1: Clone and Environment Setup
Clone the repository and create your Python virtual environment:
```bash
# Initialize and activate the virtual environment using uv
uv venv
source .venv/bin/activate
```

Install the project dependencies in editable mode:
```bash
uv pip install -e .
```

### Step 2: Configure Environment Variables
Copy the configuration template:
```bash
cp .env.example .env
```
Open the `.env` file and configure the settings:
* `EVO_BASE_URL`: The URL where your Evolution API instance is hosted.
* `EVO_API_KEY`: The API authorization key generated by the Evolution manager panel.
* `ALLOWED_NUMBERS`: Comma-separated list of WhatsApp phone numbers allowed to chat with the agents.
* `AGENT_1_NUMBER` / `AGENT_2_NUMBER`: The specific numbers designated for each agent identity.
* `DATABASE_URL`: PostgreSQL connection string (`postgresql://username:password@host:port/database`).
* `SERVER_URL`: The public URL where this FastAPI application is reachable.

### Step 3: Register Webhooks
Run the server:
```bash
python -m main
```
In a separate terminal, execute the webhook registration helper:
```bash
source .venv/bin/activate
python scripts/setup_webhook.py
```

---

Do not commit your active `.env` file to git.
