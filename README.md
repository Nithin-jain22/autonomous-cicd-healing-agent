# Autonomous CI/CD Healing Agent

Autonomous multi-agent DevOps system that clones a GitHub repository, runs tests, classifies failures, proposes fixes, commits to a strict branch format, monitors CI status, and returns structured run analytics to a React dashboard.

## Implemented Stack

- Frontend: Vite + React 18 + TypeScript + TailwindCSS + Zustand + Axios + Recharts
- Backend: FastAPI + Python 3.11 + LangGraph-ready multi-agent layout + GitPython + httpx
- Sandbox: Docker execution support via `docker/Dockerfile.sandbox`

## Project Structure

```text
autonomous-cicd-healing-agent/
├── frontend/
├── backend/
│   ├── agents/
│   ├── sandbox/
│   ├── results/
│   ├── main.py
│   └── requirements.txt
├── docker/
│   └── Dockerfile.sandbox
├── results/
├── .env.example
└── results.json
```

## Safety Rules Enforced

- Branch format must match: `TEAM_NAME_LEADER_NAME_AI_Fix`
- Commit message must start with: `[AI-AGENT]`
- Push to `main`/`master` is blocked
- Retry limit is configurable and respected
- `results.json` is generated at the end of every run

## Backend API

### `POST /run-agent`

Request:

```json
{
  "repo_url": "https://github.com/org/repo",
  "team_name": "RIFT ORGANISERS",
  "leader_name": "Saiyam Kumar"
}
```

Response:

```json
{
  "run_id": "uuid",
  "status": "running"
}
```

### `GET /run-status/{run_id}`

Returns run state, results payload, score breakdown, and timestamps.

## Environment Variables

Copy `.env.example` to `.env` in project root and fill values:

- `GITHUB_TOKEN`: required for push + CI monitoring
- `GEMINI_API_KEY`: Gemini API key (model usage can be extended in fix generation)
- `MODEL_NAME`: default `gemini-flash-2.5`
- `RETRY_LIMIT`: default `5`
- `CORS_ALLOW_ORIGINS`: comma-separated frontend origins
- `USE_DOCKER_SANDBOX`: `true|false` (default true)
- `SANDBOX_IMAGE`: docker image tag for sandbox runtime
- `VITE_API_URL`: frontend API base URL (`frontend/.env`)

## Local Setup

### 1) Backend

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2) Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend default URL: `http://localhost:5174`
Backend default URL: `http://localhost:8000`

## Deployment (Railway + Vercel)

### Backend on Railway

1. Create a new Railway project from this repository.
2. Set root service to `autonomous-cicd-healing-agent/backend`.
3. Build command:

```bash
pip install -r requirements.txt
```

4. Start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

5. Add environment variables from `.env.example` (at minimum `GITHUB_TOKEN`, `RETRY_LIMIT`, `CORS_ALLOW_ORIGINS`).

### Frontend on Vercel

1. Set root directory to `autonomous-cicd-healing-agent/frontend`.
2. Build command: `npm run build`
3. Output directory: `dist`
4. Add `VITE_API_URL` pointing to Railway backend URL.

## Output Artifacts

- Root `results.json` is overwritten with the latest run
- Per-run snapshots are stored in `results/{run_id}.json`

## Known Limitations

- Python/pytest projects are the primary supported target
- Current fix generation is conservative and template-driven
- CI polling is implemented for GitHub Actions only
- Docker sandbox falls back to local execution if Docker build/run fails
- Advanced dependency installation inside sandbox is limited

## Quick Validation Commands

```bash
# Backend syntax check
cd backend && python3.11 -m compileall .

# Frontend production build
cd frontend && npm run build
```
