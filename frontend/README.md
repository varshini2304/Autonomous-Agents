# Autonomous AI Document Agent — Frontend

Responsive React + TypeScript workspace for the FastAPI agent. It uses the existing `POST /agent` response fields (`summary`, `plan`, `assumptions`, `steps`, `document_id`, `download_url`, `status`, `provider_mode`, and `fallback_reason`) and downloads the Word file from the returned URL or document ID.

## Requirements

- Node.js 20.19+ or 22.12+
- The FastAPI backend running locally

## Install and run

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

The local Vite URL is `http://127.0.0.1:5173`. The API base URL defaults to `http://127.0.0.1:8000`; override it in `frontend/.env.local` with `VITE_API_BASE_URL` when the backend runs elsewhere. Only public API URLs belong in Vite environment variables. Never put provider keys in frontend configuration.

Run the backend from the project root with `uvicorn app.main:app --reload`. Its default CORS allowlist includes the two local Vite origins. For deployment, set the backend's `CORS_ALLOWED_ORIGINS` to a comma-separated list of exact trusted origins. Wildcard origins are not enabled.

## Production build

```powershell
npm run build
npm run preview
```
