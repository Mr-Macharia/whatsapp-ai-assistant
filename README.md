# 💬 WhatsApp AI Assistant

Welcome! This is a production-grade WhatsApp AI Assistant designed to process chat messages, think through answers, and run actions on external tools. 

It is powered by the **Agno** agentic framework (using **xAI's Grok** model as the brain), connects to WhatsApp via **Evolution API**, manages web message events using **FastAPI**, and connects to third-party services using **Composio**.

---

## 🧭 How It Works (The Simple Version)

```mermaid
graph TD
    A[User sends WhatsApp Message] -->|Received by| B[Evolution API (WhatsApp Gateway)]
    B -->|Triggers Alert| C[FastAPI Webhook Server]
    C -->|Launches Background Task| D[Agno AI Agent (Grok Brain)]
    D -->|Restores History| E[(SQLite Database)]
    D -->|Executes Actions| F[Tools / Actions]
    F -->|Brave Search| G[Search the Web]
    F -->|Composio Tools| H[GitHub, Calendly, etc.]
    D -->|Sends Response| C
    C -->|Replies to| B
    B -->|Sends to User| A
```

1. **You send a message** to a dedicated WhatsApp number.
2. **Evolution API** (running in a Docker container) detects the message and sends a real-time alert (Webhook) to my local Python backend.
3. My **FastAPI** server receives it and hands it over to **Agno** (the AI Agent framework).
4. **Agno** uses **xAI's Grok** to read the message, check past history stored in a local SQLite file, and decide if it needs to search the web (Brave) or run actions (Composio).
5. The final message is sent back to your phone instantly!

---

## 💡 Key Concepts Made Simple

### 🧠 1. The Agno Agent Framework (The Brain)
Agno (formerly Phidata) is the framework that manages the AI's instructions, its context memory (SQLite database), and its tools. It allows me to set exact rules for the AI (e.g., *"Keep responses conversational, never use bold headers, don't use sign-offs"*).

### 🤖 2. xAI's Grok (`grok-4.20-0309-reasoning`)
The agent uses the high-reasoning **Grok** model from xAI. It acts as the decision-maker that evaluates user intents and determines when and how to call external tools.

### 🛠️ 3. Fully Custom local Tools (Built for Customization!)
Apart from **Brave Search** (which is a standard external search helper), **almost all tools in this codebase are 100% custom-made**. 
* This includes my custom **Evolution API wrappers** and sending interfaces.
* **Why this is awesome**: Because they are written directly in the codebase as standard Python callables, they are fully under your control! You can expand, modify, or improve them to support custom attachments, contacts, media types, or complex routing logic anytime.

### 🔌 4. The Custom Composio-Agno Bridge (My Improvisation)
[Composio](https://composio.dev) allows the AI to log in and interact with external applications (like GitHub, Calendar, Gmail, etc.). 
* **The Problem**: The native Composio toolkit integration shipped with Agno wasn't working correctly due to Pydantic parameter annotation lookups and type signature mismatches (which would cause the server to output warnings or tool execution to fail).
* **My Solution (Improvisation)**: To bypass these framework limitations, I built a **completely custom, dynamic provider module** from scratch (`app/composio_agno/provider.py`). It intercepts tool schemas, matches Python signature requirements perfectly, and registers them dynamically—making the integration 100% stable and completely error-free!

### 📱 5. Evolution API & Docker (The WhatsApp Gateway)
To connect Python to WhatsApp, you use **Evolution API**. 
* You will need a **separate WhatsApp number** (like a spare SIM card or Business number) to act as the agent's account.
* This gateway runs in a **Docker container** on your local machine or server. You scan a QR code once to link the WhatsApp number, and Docker keeps it running in the background.

### 🔔 6. Webhooks (Real-Time Alerts)
A webhook is like a post-box. Instead of my code continuously asking WhatsApp *"Do I have new messages?"* (which is slow and wastes resources), the Evolution API immediately posts a message alert to my FastAPI server (`POST /webhook/whatsapp`) the millisecond a message is received.

---

## 📂 Project Directory Structure

```bash
whatsapp-agent/
├── app/
│   ├── composio_agno/        # Custom Composio-Agno bridging layer (error-free)
│   │   ├── __init__.py
│   │   └── provider.py       # Auto-patches tool schemas for Agno
│   ├── tools/                # Capabilities given to the Grok brain
│   │   ├── __init__.py
│   │   ├── composio.py       # Activates external account actions
│   │   ├── search.py         # Brave Search tool setup
│   │   └── whatsapp.py       # Direct message sending callable
│   ├── agent.py              # Main Agno/Grok Agent rules & prompt instructions
│   ├── config.py             # Settings manager that reads your secret keys
│   └── webhook.py            # FastAPI webhook endpoints & background tasks
├── scripts/
│   └── setup_webhook.py      # Registers your backend URL with the WhatsApp gateway
├── main.py                   # Server starter script
├── pyproject.toml            # Project libraries list
├── uv.lock                   # Reusable packages lock file
└── .env.example              # Template for API keys and configurations
```

---

## 🚀 Step-by-Step Setup Guide

### Step 1: Start your Virtual Environment
This project includes a Python virtual environment (`.venv`) to isolate all libraries and prevent clashes with your computer's global packages.

Open your terminal in this directory and activate it:
```bash
# On Linux / macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

If you need to install or update project libraries:
```bash
uv pip install -e .
```

---

### Step 2: Configure your Secrets & Link WhatsApp

1. **Create your Local Env File**:
   In the root folder, create a file named `.env` by copying my template:
   ```bash
   cp .env.example .env
   ```

2. **Link your WhatsApp Phone Number**:
   * Ensure your Evolution API Docker container is started and running (default port is `8080`).
   * In your browser, navigate to **`http://localhost:8080/manager`**.
   * Create an instance and scan the generated **QR code** using your dedicated WhatsApp phone number (exactly like you would link a new device on WhatsApp Web).
   * Once successfully linked, the Evolution API manager panel will show your unique **instance token / API key**.

3. **Fill in the `.env` File**:
   Open `.env` in any text editor and paste your secrets:
   - **`XAI_API_KEY`**: Your API key from xAI console to power the Grok brain.
   - **`EVO_BASE_URL`**: The URL where your Evolution API is running (e.g., `http://localhost:8080`).
   - **`EVO_API_KEY`**: The unique API key you copied from the manager panel at `http://localhost:8080/manager`.
   - **`ALLOWED_NUMBER`**: The phone number you will use to talk to the agent (forces the agent to ignore messages from strangers).
   - **`COMPOSIO_API_KEY` & `BRAVE_API_KEY`**: For running external actions and web searches.

---

### Step 3: Run the FastAPI Webhook Server
Start the server that listens for incoming WhatsApp messages. You have three simple options to run it:

* **Recommended / Production option:**
  ```bash
  python -m main
  ```
* **Development option (automatically updates as you edit code):**
  ```bash
  fastapi dev main.py
  ```
* **Standard Uvicorn command:**
  ```bash
  uvicorn app.webhook:app --host 0.0.0.0 --port 7777 --reload
  ```

Your server is now live and waiting on port **`7777`**!

---

### Step 4: Register your Server with the WhatsApp Gateway
For Evolution API to know where to send incoming messages, you must register your server's URL.

While your server is running in one terminal, open a **second terminal window**, activate the environment, and run the setup script:
```bash
source .venv/bin/activate
python scripts/setup_webhook.py
```
*You will see a success message: `Webhook registered successfully!`*

Now, whenever you text your dedicated WhatsApp number, it will forward it to your running backend!

---

## 🔮 What's Next? (Roadmap)
I am actively developing the next advanced features for this assistant:
1. **Self-Learning Loop**: Letting the agent analyze past conversations and automatically update its own system instructions to serve you better.
2. **Memory Validation**: A script to evaluate, score, and prune old conversation memories so the brain stays fast and accurate.
3. **Chat Retrieval**: Advanced historical search so the AI remembers things you told it weeks ago.
