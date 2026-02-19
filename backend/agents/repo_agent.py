from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
from shutil import rmtree
from urllib.parse import urlparse, urlunparse

from git import Repo

logger = logging.getLogger(__name__)


@dataclass
class RepoAgentResult:
    language: str
    repo_path: str


class RepoAgent:
    def __init__(self) -> None:
        self._sandbox_root = Path(__file__).resolve().parents[1] / "sandbox"
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise Exception("GITHUB_TOKEN is required for autonomous execution.")
        logger.info(f"🔍 DEBUG: RepoAgent sandbox_root = {self._sandbox_root}")
        logger.info(f"🔍 DEBUG: Absolute sandbox_root = {self._sandbox_root.absolute()}")
        logger.info(f"✅ GITHUB_TOKEN configured for autonomous operations")

    def analyze_repository(self, repo_url: str, run_id: str) -> RepoAgentResult:
        run_path = self._sandbox_root / run_id
        logger.info(f"🔍 DEBUG: Cloning to run_path = {run_path}")
        logger.info(f"🔍 DEBUG: Absolute run_path = {run_path.absolute()}")
        
        if run_path.exists():
            logger.info(f"🔍 DEBUG: Removing existing run_path")
            rmtree(run_path)

        run_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Inject GitHub token for authenticated clone if available
        clone_url = self._inject_token_if_github(repo_url)
        logger.info(f"🔍 DEBUG: Starting clone from {repo_url}")
        Repo.clone_from(clone_url, str(run_path))
        logger.info(f"🔍 DEBUG: Clone complete")
        
        # List files in cloned repo
        try:
            files = list(os.listdir(run_path))
            logger.info(f"🔍 DEBUG: Files in cloned repo: {files}")
        except Exception as e:
            logger.error(f"🔍 DEBUG: Error listing files: {e}")
        
        language = self._detect_language(run_path)
        logger.info(f"🔍 DEBUG: Detected language: {language}")
        logger.info(f"🔍 DEBUG: Returning repo_path: {str(run_path)}")
        return RepoAgentResult(language=language, repo_path=str(run_path))

    def _inject_token_if_github(self, repo_url: str) -> str:
        """Inject GitHub token into HTTPS URL for authenticated operations."""
        # Only inject token for GitHub URLs
        if not repo_url.startswith(("https://github.com/", "http://github.com/")):
            return repo_url
        
        # GITHUB_TOKEN is mandatory (checked in __init__)
        if not self.github_token:
            raise Exception("GITHUB_TOKEN is required for autonomous execution.")
        
        # Parse and inject token
        parsed = urlparse(repo_url)
        # Format: https://<token>@github.com/owner/repo.git
        netloc = f"{self.github_token}@{parsed.netloc}"
        authenticated_url = urlunparse(parsed._replace(netloc=netloc))
        logger.info(f"✅ Injected token into clone URL for authenticated access")
        return authenticated_url

    def _detect_language(self, repo_path: Path) -> str:
        if any(repo_path.rglob("pyproject.toml")) or any(repo_path.rglob("requirements.txt")):
            return "python"
        if any(repo_path.rglob("package.json")):
            return "javascript"
        return "unknown"
