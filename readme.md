# Agents on Tracks 🚂

**Tracks** is an OpenClaw-inspired LLM agent manager and supercharger. It's designed for users who want to leverage their existing subscriptions—like **Google One AI** or **OpenAI**—to power a personal AI concierge. 

If you're looking for a way to maintain some level of privacy while maximizing your AI productivity within a tight budget, Tracks is built for you.

---

## 🚀 Getting Started

Tracks is containerized for easy deployment of both the API and the Web interface.

### Running with Docker

1.  **Build and Start**: Run the following command in the root directory:
    ```bash
    docker compose up --build -d 
    ```
    This will start:
    - **API**: [http://localhost:8540](http://localhost:8540)
    - **Web Interface**: [http://localhost:8541](http://localhost:8541)

---

## 🔑 Initialization & Authentication

Before running the agents, you need to initialize them and log in to your respective accounts using the Admin CLI.

### Using `admin.py` (Local)

1.  **Codex (OpenAI/Browser-based)**:
    ```bash
    python admin.py agent codex login
    ```
2.  **Gemini (Google One AI)**:
    ```bash
    python admin.py agent gemini login
    ```

### Using `admin.py` (Docker)

If you are running Tracks via Docker, execute the authentication command within the API container:

```bash
docker compose run --rm api python admin.py agent codex login
docker compose run --rm api python admin.py agent gemini login
```

Follow the on-screen instructions in the opened browser sessions to complete the login process.

---

## 🤖 Telegram Integration

You can interact with your agents directly through Telegram.

### Setup Steps

1.  **BotFather**: 
    - Talk to [@BotFather](https://t.me/botfather) on Telegram.
    - Create a new bot and copy the **API Token**.
2.  **Configure `vault.json`**:
    Edit the `vault.json` file in the root directory and add your token and your Telegram User ID (to restrict access):
    ```json
    {
        "TELEGRAM_BOT_TOKEN": "YOUR_BOT_TOKEN_HERE",
        "TELEGRAM_USER_IDS": "YOUR_TELEGRAM_USER_ID"
    }
    ```
3.  **Enable Telegram**:
    Ensure `"ENABLE_TELEGRAM": true` is set in your `config.json`.

---

## 🌐 Web Interface

If you prefer a visual interface, Tracks comes with a premium web UI.

1.  **Access**: Open your browser and navigate to [http://localhost:8541](http://localhost:8541).
2.  **Usage**:
    - Start new chat sessions.
    - Switch between different agent providers (Codex/Gemini).
    - Review your chat history.
