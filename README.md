# MCP Demo Server

Python-based Model Context Protocol demo that exposes resources, tools, and prompts while brokering chat requests to an LLM (real or mocked). A lightweight HTML frontend showcases the end-to-end flow.

## Features
- **FastAPI** backend with MCP-compliant REST endpoints for resources, tools, and prompts.
- **LLM bridge** supporting OpenAI Chat Completions and Google Gemini plus a deterministic mock fallback.
- **Mock mode** (`MOCK_MODE=1`) keeps the server fully runnable without external dependencies.
- **Minimal frontend** (`/`) for exploring MCP capabilities and sending chat requests.

## Requirements
- Python 3.10 or later
- Optional: OpenAI API key (`OPENAI_API_KEY`) or Google Gemini API key (`GEMINI_API_KEY`) for live LLM interaction

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate            # PowerShell
pip install -r requirements.txt
```

## Configuration
Environment variables (all optional):

| Variable          | Description                                                   | Default             |
|-------------------|---------------------------------------------------------------|---------------------|
| `MOCK_MODE`       | Force mock responses (`1`, `true`, `yes`)                      | `0`                 |
| `LLM_PROVIDER`    | `openai`, `gemini`, or any other value to defer to mock        | `openai`            |
| `OPENAI_API_KEY`  | API key for OpenAI Chat Completions                            | _unset_ (mock mode) |
| `OPENAI_MODEL`    | Chat completion model name                                     | `gpt-3.5-turbo`     |
| `GEMINI_API_KEY`  | Google Gemini Generative Language key                          | _unset_ (mock mode) |
| `GEMINI_MODEL`    | Gemini model (`gemini-2.0-flash`, `gemini-1.5-pro`, etc.)      | `gemini-1.5-flash`  |

If the chosen provider is missing credentials or `MOCK_MODE` is true, the mock LLM is used automatically. Variables can be set in your shell or inside a `.env` file at the repository root (auto-loaded via `python-dotenv`).

## Run the Server
```bash
uvicorn app.main:app --reload
```
Visit `http://127.0.0.1:8000/` to open the frontend.

### Google Gemini Setup
```powershell
$env:LLM_PROVIDER = "gemini"
$env:GEMINI_API_KEY = "<your-gemini-api-key>"
# Optional model override
$env:GEMINI_MODEL = "gemini-1.5-pro"
uvicorn app.main:app --reload
```
Gemini support uses the Google AI Studio REST endpoint, so no extra Python dependency is required.

Or, add the values to `.env`:
```
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-2.0-flash
```
Restart the server after editing `.env`.

## Frontend Walkthrough
1. Load the page to view the available MCP resources, tools, and prompts.
2. Type a message for the LLM.
3. (Optional) Select resources, fill tool arguments, and/or choose a prompt with its inputs.
4. Click **Send to LLM** to see the structured JSON response displayed on the page.

## MCP REST Endpoints
| Method | Path                   | Description                                   |
|--------|------------------------|-----------------------------------------------|
| GET    | `/health`              | Service health probe                          |
| GET    | `/mcp/resources`       | List resource metadata/content                |
| GET    | `/mcp/resources/{id}`  | Retrieve a specific resource                  |
| GET    | `/mcp/tools`           | List tool definitions                         |
| POST   | `/mcp/tools/invoke`    | Execute a tool (`tool_name`, `arguments`)     |
| GET    | `/mcp/prompts`         | List available prompts                        |
| POST   | `/mcp/prompts/render`  | Render a prompt with the supplied input map   |
| POST   | `/mcp/chat`            | Chat with the LLM via MCP context             |

### Sample Chat Payload
```json
{
  "message": "Summarise the company profile for a prospect.",
  "context_resources": ["company:outline"],
  "tool_calls": [
    {"tool_name": "time.now", "arguments": {}}
  ],
  "prompt_name": "summarize-resource",
  "prompt_inputs": {
    "resource_json": "{...}",
    "question": "What should I tell a new lead?"
  }
}
```

## Testing
The project has no automated tests yet. Basic validation: `python -m compileall app` checks syntax, and hitting the `/health` endpoint after starting the server ensures FastAPI booted successfully.

## Folder Layout
```
app/
  config.py        # Environment-driven configuration
  llm.py           # LLM provider adapters (OpenAI + mock)
  main.py          # FastAPI app and REST endpoints
  mcp.py           # MCP capability definitions and handlers
  models.py        # Pydantic models for schema validation
frontend/
  index.html       # Minimal MCP client
requirements.txt   # Python dependencies
```

## Notes
- When using real LLM credentials, keep them out of version control and set them per environment.
- Extend the MCP surface by adding resources, prompts, or tools in `app/mcp.py`.
