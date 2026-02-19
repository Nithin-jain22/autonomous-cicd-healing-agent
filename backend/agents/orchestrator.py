from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from uuid import uuid4

from models import CITimelineRecord, FixRecord, FixStatus, ResultsSchema, RunAgentRequest, RunState, RunStatus
from run_store import run_store
from .repo_agent import RepoAgent
from .test_agent import TestAgent
from .failure_parser_agent import FailureParserAgent
from .fix_agent import FixAgent
from .git_agent import GitAgent
from .ci_agent import CIAgent
from .score_agent import ScoreAgent

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    def __init__(self, retry_limit: int) -> None:
        self.retry_limit = retry_limit
        self.repo_agent = RepoAgent()
        self.test_agent = TestAgent()
        self.failure_parser_agent = FailureParserAgent()
        self.fix_agent = FixAgent()
        self.git_agent = GitAgent()
        self.ci_agent = CIAgent()
        self.score_agent = ScoreAgent()
        self._project_root = Path(__file__).resolve().parents[2]
        self._results_dir = self._project_root / "results"

    def start_run(self, payload: RunAgentRequest) -> RunState:
        run_id = str(uuid4())
        branch_name = self.git_agent.build_branch_name(payload.team_name, payload.leader_name)
        if not self.git_agent.validate_branch_name(branch_name):
            raise ValueError("Invalid branch format")

        results = ResultsSchema(
            repository=str(payload.repo_url),
            team_name=payload.team_name,
            leader_name=payload.leader_name,
            branch_name=branch_name,
            retry_limit=self.retry_limit,
            final_status=RunStatus.RUNNING,
        )

        run_state = RunState(
            run_id=run_id,
            status=RunStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
            results=results,
        )
        run_store.upsert(run_state)
        return run_state

    def get_run(self, run_id: str) -> RunState | None:
        return run_store.get(run_id)

    def execute_run(self, run_id: str, payload: RunAgentRequest) -> None:
        run_state = run_store.get(run_id)
        if run_state is None:
            return

        started_at = datetime.now(timezone.utc)
        logger.info(f"Starting run {run_id} for repository {payload.repo_url}")
        
        try:
            repo_info = self.repo_agent.analyze_repository(str(payload.repo_url), run_id)
            logger.info(f"Repository cloned to {repo_info.repo_path}")
            logger.info(f"🔍 DEBUG: ===== REPOSITORY CLONING COMPLETE =====")
            logger.info(f"🔍 DEBUG: repo_path = {repo_info.repo_path}")
            logger.info(f"🔍 DEBUG: language = {repo_info.language}")
            
            # List all files in repo
            import os
            try:
                all_files = []
                for root, dirs, files in os.walk(repo_info.repo_path):
                    for file in files:
                        all_files.append(os.path.join(root, file))
                logger.info(f"🔍 DEBUG: Total files in repo: {len(all_files)}")
                logger.info(f"🔍 DEBUG: First 20 files: {all_files[:20]}")
            except Exception as e:
                logger.error(f"🔍 DEBUG: Error walking repo: {e}")
            
            active_branch = self.git_agent.checkout_or_create_branch(
                repo_path=repo_info.repo_path,
                branch_name=run_state.results.branch_name,
                run_id=run_id,
            )
            run_state.results.branch_name = active_branch
            run_state.results.iterations_used = 0
            logger.info(f"Checked out branch {active_branch}")

            for iteration in range(1, self.retry_limit + 1):
                logger.info(f"=== Iteration {iteration}/{self.retry_limit} ===")
                run_state.results.iterations_used = iteration
                run_store.upsert(run_state)

                # Run tests
                test_result = self.test_agent.run_tests(repo_info.repo_path)
                
                if test_result.passed:
                    logger.info(f"All tests passed in iteration {iteration}")
                    
                    # Check if this is a local file:// URL (skip push/CI for local testing)
                    is_local_repo = str(payload.repo_url).startswith("file://")
                    
                    if is_local_repo:
                        logger.info("Local repository detected - skipping push and CI monitoring")
                        run_state.status = RunStatus.PASSED
                        run_state.results.final_status = RunStatus.PASSED
                        run_state.results.ci_timeline.append(
                            CITimelineRecord(
                                iteration=iteration,
                                status=RunStatus.PASSED,
                                timestamp=datetime.now(timezone.utc).isoformat(),
                            )
                        )
                        logger.info("All tests passed for local repo - run complete")
                        break
                    
                    # For remote repos, push and monitor CI
                    ci_status = self._push_and_monitor_ci(
                        repo_path=repo_info.repo_path,
                        repo_url=str(payload.repo_url),
                        branch_name=run_state.results.branch_name,
                    )
                    run_state.results.ci_timeline.append(
                        CITimelineRecord(
                            iteration=iteration,
                            status=RunStatus.PASSED if ci_status.status == "PASSED" else RunStatus.FAILED,
                            timestamp=ci_status.timestamp,
                        )
                    )
                    if ci_status.status == "PASSED":
                        run_state.status = RunStatus.PASSED
                        run_state.results.final_status = RunStatus.PASSED
                        logger.info("CI passed - run complete")
                        break
                    logger.warning(f"Tests passed locally but CI failed: {ci_status.details}")
                    run_store.upsert(run_state)
                    continue

                # Tests failed - parse and fix failures
                logger.info(f"Tests failed with {len(test_result.failures)} failure(s)")
                run_state.results.total_failures += len(test_result.failures)
                
                fixes_applied = 0
                for failure in test_result.failures:
                    logger.debug(f"Processing failure: {failure.file}:{failure.line_number} - {failure.error_type}")
                    
                    # Parse failure with error_type
                    parsed = self.failure_parser_agent.parse_failure(
                        file=failure.file,
                        line_number=failure.line_number,
                        message=failure.message,
                        error_type=failure.error_type,
                    )
                    
                    logger.info(f"Classified as {parsed.bug_type.value}: {failure.file}:{failure.line_number}")
                    
                    # Apply actual fix to file
                    fix_applied = self.fix_agent.apply_fix(
                        repo_path=repo_info.repo_path,
                        file=parsed.file,
                        line_number=parsed.line_number,
                        bug_type=parsed.bug_type,
                        message=parsed.raw_message,
                        error_type=parsed.error_type,
                    )
                    
                    # Generate proposal metadata for tracking
                    proposal = self.fix_agent.generate_fix(
                        file=parsed.file,
                        line_number=parsed.line_number,
                        bug_type=parsed.bug_type,
                        message=parsed.raw_message,
                    )
                    
                    self.git_agent.enforce_commit_prefix(proposal.commit_message)
                    
                    fix_status = FixStatus.FIXED if fix_applied else FixStatus.FAILED
                    if fix_applied:
                        fixes_applied += 1
                    
                    logger.info(f"Fix {'applied' if fix_applied else 'failed'} for {parsed.file}:{parsed.line_number}")
                    
                    run_state.results.fixes.append(
                        FixRecord(
                            file=proposal.file,
                            bug_type=proposal.bug_type,
                            line_number=proposal.line_number,
                            commit_message=proposal.commit_message,
                            status=fix_status,
                            strict_output=proposal.strict_output,
                        )
                    )

                # Commit changes if any fixes were applied
                if fixes_applied > 0:
                    logger.info(f"Committing {fixes_applied} fix(es)")
                    committed = self.git_agent.commit_all_changes(
                        repo_path=repo_info.repo_path,
                        commit_message=f"[AI-AGENT] Apply {fixes_applied} autonomous fix(es)",
                    )
                    if committed:
                        run_state.results.commits += 1
                        logger.debug("Changes committed successfully")
                else:
                    logger.warning("No fixes were applied successfully")

                # Push and monitor CI
                ci_status = self._push_and_monitor_ci(
                    repo_path=repo_info.repo_path,
                    repo_url=str(payload.repo_url),
                    branch_name=run_state.results.branch_name,
                )
                run_state.results.total_fixes = len(run_state.results.fixes)
                run_state.results.ci_timeline.append(
                    CITimelineRecord(
                        iteration=iteration,
                        status=RunStatus.PASSED if ci_status.status == "PASSED" else RunStatus.FAILED,
                        timestamp=ci_status.timestamp,
                    )
                )
                if ci_status.status == "PASSED":
                    run_state.status = RunStatus.PASSED
                    run_state.results.final_status = RunStatus.PASSED
                    logger.info("CI passed after fixes")
                    run_store.upsert(run_state)
                    break
                
                logger.info(f"Iteration {iteration} complete - CI status: {ci_status.status}")
                run_store.upsert(run_state)

            if run_state.status != RunStatus.PASSED:
                run_state.status = RunStatus.FAILED
                run_state.results.final_status = RunStatus.FAILED
                logger.warning(f"Run failed after {self.retry_limit} iterations")

        except Exception as e:
            logger.error(f"Run failed with exception: {e}", exc_info=True)
            run_state.status = RunStatus.FAILED
            run_state.results.final_status = RunStatus.FAILED
        finally:
            finished_at = datetime.now(timezone.utc)
            run_state.finished_at = finished_at
            run_state.results.total_fixes = len(run_state.results.fixes)
            run_state.results.execution_time_seconds = int((finished_at - started_at).total_seconds())
            score_breakdown = self.score_agent.calculate_score(
                execution_time_seconds=run_state.results.execution_time_seconds,
                commits=run_state.results.commits,
            )
            run_state.results.score_base = score_breakdown.base_score
            run_state.results.score_time_bonus = score_breakdown.time_bonus
            run_state.results.score_commit_penalty = score_breakdown.commit_penalty
            run_state.results.score = score_breakdown.final_score
            run_store.upsert(run_state)
            self._persist_results(run_state)
            logger.info(f"Run {run_id} complete - Status: {run_state.status}, Score: {run_state.results.score}")

    def _push_and_monitor_ci(self, repo_path: str, repo_url: str, branch_name: str):
        self.git_agent.push_branch(repo_path=repo_path, branch_name=branch_name)
        return self.ci_agent.poll_workflow_status(repo_url=repo_url, branch_name=branch_name)

    def _persist_results(self, run_state: RunState) -> None:
        self._results_dir.mkdir(parents=True, exist_ok=True)
        run_result_file = self._results_dir / f"{run_state.run_id}.json"
        root_result_file = self._project_root / "results.json"
        payload = run_state.results.model_dump(mode="json")
        run_result_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        root_result_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
