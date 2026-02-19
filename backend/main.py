from __future__ import annotations

import logging
import os
import re

from dotenv import load_dotenv
from fastapi import BackgroundTasks
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agents import OrchestratorAgent
from models import RunAgentRequest, RunAgentResponse, RunStatus

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG", "false").lower() == "true" else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Autonomous CI/CD Healing Agent API", version="0.1.0")

RETRY_LIMIT = int(os.getenv("RETRY_LIMIT", "5"))
CORS_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "*")
CORS_ORIGIN_LIST = [origin.strip() for origin in CORS_ORIGINS.split(",") if origin.strip()]
orchestrator = OrchestratorAgent(retry_limit=RETRY_LIMIT)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGIN_LIST or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _is_valid_name(value: str) -> bool:
    """Validate name for branch format - only alphanumeric and spaces."""
    return bool(re.match(r"^[a-zA-Z0-9\s]+$", value))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run-agent", response_model=RunAgentResponse)
def run_agent(payload: RunAgentRequest, background_tasks: BackgroundTasks) -> RunAgentResponse:
    # Validate input
    if not payload.repo_url or not payload.team_name or not payload.leader_name:
        raise HTTPException(status_code=400, detail="Missing required fields: repo_url, team_name, leader_name")
    
    # Validate team_name and leader_name format
    if not _is_valid_name(payload.team_name):
        raise HTTPException(status_code=400, detail="team_name contains invalid characters")
    if not _is_valid_name(payload.leader_name):
        raise HTTPException(status_code=400, detail="leader_name contains invalid characters")
    
    try:
        run_state = orchestrator.start_run(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    background_tasks.add_task(orchestrator.execute_run, run_state.run_id, payload)

    return RunAgentResponse(run_id=run_state.run_id, status=RunStatus.RUNNING)


@app.get("/run-status/{run_id}")
def run_status(run_id: str) -> dict:
    run_state = orchestrator.get_run(run_id)
    if run_state is None:
        raise HTTPException(status_code=404, detail="run_id not found")

    return {
        "run_id": run_state.run_id,
        "status": run_state.status,
        "results": run_state.results.model_dump(),
        "score_breakdown": {
            "base": run_state.results.score_base,
            "time_bonus": run_state.results.score_time_bonus,
            "commit_penalty": run_state.results.score_commit_penalty,
            "final": run_state.results.score,
        },
        "started_at": run_state.started_at.isoformat(),
        "finished_at": run_state.finished_at.isoformat() if run_state.finished_at else None,
    }
