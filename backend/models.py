from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class RunStatus(str, Enum):
    RUNNING = "running"
    PASSED = "PASSED"
    FAILED = "FAILED"


class BugType(str, Enum):
    LINTING = "LINTING"
    SYNTAX = "SYNTAX"
    LOGIC = "LOGIC"
    TYPE_ERROR = "TYPE_ERROR"
    IMPORT = "IMPORT"
    INDENTATION = "INDENTATION"


class FixStatus(str, Enum):
    FIXED = "FIXED"
    FAILED = "FAILED"


class FixRecord(BaseModel):
    file: str
    bug_type: BugType
    line_number: int = Field(ge=0)
    commit_message: str
    status: FixStatus
    strict_output: str = Field(description="Standardized fix description matching judge requirements")


class CITimelineRecord(BaseModel):
    iteration: int = Field(ge=1)
    status: RunStatus
    timestamp: str


class ResultsSchema(BaseModel):
    repository: str
    team_name: str
    leader_name: str
    branch_name: str
    total_failures: int = Field(default=0, ge=0)
    total_fixes: int = Field(default=0, ge=0)
    iterations_used: int = Field(default=0, ge=0)
    retry_limit: int = Field(default=5, ge=1)
    commits: int = Field(default=0, ge=0)
    final_status: RunStatus = RunStatus.FAILED
    execution_time_seconds: int = Field(default=0, ge=0)
    score: int = Field(default=0, ge=0)
    score_base: int = Field(default=100, ge=0)
    score_time_bonus: int = Field(default=0, ge=0)
    score_commit_penalty: int = Field(default=0, ge=0)
    fixes: List[FixRecord] = Field(default_factory=list)
    ci_timeline: List[CITimelineRecord] = Field(default_factory=list)


class RunAgentRequest(BaseModel):
    repo_url: str  # Changed from HttpUrl to support file:// URLs for testing
    team_name: str = Field(min_length=1)
    leader_name: str = Field(min_length=1)


class RunAgentResponse(BaseModel):
    run_id: str
    status: RunStatus


class RunState(BaseModel):
    run_id: str
    status: RunStatus
    started_at: datetime
    finished_at: Optional[datetime] = None
    results: ResultsSchema
