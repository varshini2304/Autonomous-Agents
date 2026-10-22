# Autonomous AI Document Agent

FastAPI service that plans and executes a bounded workflow to create a polished Word business document. xAI Grok is the preferred live provider; the existing Groq adapter remains available when an xAI key is not configured. Without a usable live provider, the service uses a visible deterministic planner and drafter. Python controls tool execution, validation, file storage, and DOCX generation.

## Install and run

Requires Python 3.11+.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the API. Set `XAI_API_KEY` in `.env` to enable xAI; `XAI_MODEL` defaults to `grok-4.7`. If xAI is not configured, an existing `GROQ_API_KEY` can still enable the previous Groq provider. `GET /health` reports `live_llm` only after a successful provider call; otherwise it reports `fallback`, along with the configured provider name and a boolean that never reveals the key.

Run a non-generation xAI authentication/model availability check with `python -m app.llm.connectivity`. It calls xAI's `/v1/models` endpoint and never prints the key. Provider authentication, billing, model, and network errors appear as safely redacted fallback reasons. Fallback mode needs no API key or network; its deterministic templates cannot research external facts and should be reviewed for request-specific nuance.

## API

- `POST /agent` with `{"request":"..."}` plans and creates a DOCX.
- `GET /documents/{document_id}` downloads the generated file.
- `GET /health` reports service/provider status.

Settings: `XAI_API_KEY`, `XAI_MODEL`, `GROQ_API_KEY`, `GROQ_MODEL`, `OUTPUT_DIR`, `MAX_REQUEST_LENGTH`, `MAX_PLAN_STEPS`, and `LLM_TIMEOUT_SECONDS`.

## Demonstrations

Use the request bodies from the challenge through `POST /agent`; the standard proposal and complex recovery plan each have dedicated deterministic fallback content.

## Tests

Run `pytest`. Tests use local fake providers and do not need API credentials or network access.
