from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
import time
from urllib.parse import urlparse

import httpx


@dataclass
class CIStatus:
    status: str
    timestamp: str
    details: str = ""


class CIAgent:
    def __init__(self) -> None:
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.poll_interval = int(os.getenv("CI_POLL_INTERVAL_SECONDS", "5"))
        self.poll_timeout = int(os.getenv("CI_POLL_TIMEOUT_SECONDS", "180"))

    def poll_workflow_status(self, repo_url: str, branch_name: str) -> CIStatus:
        owner_repo = self._extract_owner_repo(repo_url)
        if owner_repo is None:
            return CIStatus(status="FAILED", timestamp=self._utc_now(), details="Invalid GitHub repository URL")

        if not self.github_token:
            return CIStatus(status="FAILED", timestamp=self._utc_now(), details="Missing GITHUB_TOKEN")

        owner, repo = owner_repo
        deadline = time.monotonic() + self.poll_timeout

        with httpx.Client(timeout=20.0) as client:
            while time.monotonic() < deadline:
                run_status = self._fetch_latest_workflow_run(client, owner, repo, branch_name)
                if run_status is None:
                    time.sleep(self.poll_interval)
                    continue

                status, conclusion = run_status
                if status in {"queued", "in_progress", "waiting", "requested", "pending"}:
                    time.sleep(self.poll_interval)
                    continue

                if status == "completed" and conclusion == "success":
                    return CIStatus(status="PASSED", timestamp=self._utc_now(), details="GitHub Actions workflow completed successfully")

                return CIStatus(
                    status="FAILED",
                    timestamp=self._utc_now(),
                    details=f"GitHub Actions workflow completed with conclusion={conclusion or 'unknown'}",
                )

        return CIStatus(status="FAILED", timestamp=self._utc_now(), details="CI polling timeout")

    def _fetch_latest_workflow_run(
        self,
        client: httpx.Client,
        owner: str,
        repo: str,
        branch_name: str,
    ) -> tuple[str, str | None] | None:
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.github_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
        response = client.get(url, headers=headers, params={"branch": branch_name, "per_page": 1})
        if response.status_code >= 400:
            return None

        data = response.json()
        runs = data.get("workflow_runs", [])
        if not runs:
            return None

        latest = runs[0]
        return latest.get("status", ""), latest.get("conclusion")

    def _extract_owner_repo(self, repo_url: str) -> tuple[str, str] | None:
        parsed = urlparse(repo_url)
        if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
            return None

        segments = [segment for segment in parsed.path.split("/") if segment]
        if len(segments) < 2:
            return None

        owner = segments[0]
        repo = segments[1].removesuffix(".git")
        if not owner or not repo:
            return None
        return owner, repo

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
