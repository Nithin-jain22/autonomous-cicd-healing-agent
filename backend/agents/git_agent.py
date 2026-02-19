from __future__ import annotations

import logging
import os
import re

from git import Repo

logger = logging.getLogger(__name__)


class GitAgent:
    BRANCH_PATTERN = re.compile(r"^[A-Z_]+_AI_Fix$")
    COMMIT_PREFIX = "[AI-AGENT]"
    PROTECTED_BRANCHES = {"main", "master"}
    
    def __init__(self) -> None:
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise Exception("GITHUB_TOKEN is required for autonomous execution.")
        logger.info("✅ GITHUB_TOKEN configured for autonomous git operations")

    def build_branch_name(self, team_name: str, leader_name: str) -> str:
        normalized_team = self._normalize(team_name)
        normalized_leader = self._normalize(leader_name)
        return f"{normalized_team}_{normalized_leader}_AI_Fix"

    def validate_branch_name(self, branch_name: str) -> bool:
        return bool(self.BRANCH_PATTERN.fullmatch(branch_name)) and branch_name.endswith("_AI_Fix")

    def validate_commit_prefix(self, commit_message: str) -> bool:
        return commit_message.startswith(self.COMMIT_PREFIX)

    def ensure_not_main_branch(self, branch_name: str) -> None:
        if branch_name.lower() in self.PROTECTED_BRANCHES:
            raise ValueError("Push to protected branch is not allowed")

    def enforce_branch_name(self, branch_name: str) -> None:
        if not self.validate_branch_name(branch_name):
            raise ValueError("Branch name must match TEAM_NAME_LEADER_NAME_AI_Fix format")

    def enforce_commit_prefix(self, commit_message: str) -> None:
        if not self.validate_commit_prefix(commit_message):
            raise ValueError("Commit message must start with [AI-AGENT]")

    def checkout_or_create_branch(self, repo_path: str, branch_name: str, run_id: str) -> str:
        self.enforce_branch_name(branch_name)
        self.ensure_not_main_branch(branch_name)

        repo = Repo(repo_path)
        
        # Check if branch exists locally or remotely
        existing_local = {head.name for head in repo.heads}
        existing_remote = {ref.name.split("origin/")[-1] for ref in repo.remote().refs} if repo.remotes else set()
        
        if branch_name in existing_local or branch_name in existing_remote:
            logger.error(f"❌ STRICT ENFORCEMENT: Branch '{branch_name}' already exists. Cannot modify branch name.")
            raise ValueError(f"Branch '{branch_name}' already exists. Strict naming requires exact TEAM_NAME_LEADER_NAME_AI_Fix format with NO modifications.")
        
        # Create branch with exact name (strict mode)
        if branch_name in [head.name for head in repo.heads]:
            repo.git.checkout(branch_name)
        else:
            repo.git.checkout("-b", branch_name)

        logger.info(f"✅ Branch created with strict name: {branch_name}")
        return branch_name

    def commit_all_changes(self, repo_path: str, commit_message: str) -> bool:
        self.enforce_commit_prefix(commit_message)
        repo = Repo(repo_path)
        repo.git.add(A=True)
        if not repo.is_dirty(untracked_files=True):
            return False
        repo.index.commit(commit_message)
        return True

    def push_branch(self, repo_path: str, branch_name: str) -> None:
        self.ensure_not_main_branch(branch_name)
        
        # GITHUB_TOKEN is mandatory (checked in __init__)
        if not self.github_token:
            raise Exception("GITHUB_TOKEN is required for autonomous execution.")
        
        repo = Repo(repo_path)
        repo.git.push("origin", branch_name)

    def _normalize(self, value: str) -> str:
        uppercase = value.upper().replace(" ", "_")
        normalized = re.sub(r"[^A-Z_]", "", uppercase)
        return re.sub(r"_+", "_", normalized).strip("_")
