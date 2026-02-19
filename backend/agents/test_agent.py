from __future__ import annotations

from dataclasses import dataclass, field
import logging
from pathlib import Path
import re
from typing import List

from sandbox import SandboxExecutor

logger = logging.getLogger(__name__)


@dataclass
class TestFailure:
    file: str
    line_number: int
    message: str
    error_type: str = "UnknownError"
    full_traceback: str = ""


@dataclass
class TestRunResult:
    passed: bool
    failures: List[TestFailure] = field(default_factory=list)


class TestAgent:
    def __init__(self) -> None:
        self.sandbox_executor = SandboxExecutor()

    def run_tests(self, repo_path: str) -> TestRunResult:
        logger.info(f"🔍 DEBUG: ===== TEST_AGENT.RUN_TESTS() CALLED =====")
        logger.info(f"🔍 DEBUG: repo_path parameter = {repo_path}")
        
        # Debug: Current working directory
        import os
        import shutil
        cwd = os.getcwd()
        logger.info(f"🔍 DEBUG: os.getcwd() = {cwd}")
        logger.info(f"🔍 DEBUG: os.path.abspath(repo_path) = {os.path.abspath(repo_path)}")
        logger.info(f"🔍 DEBUG: os.path.exists(repo_path) = {os.path.exists(repo_path)}")
        
        # Debug: List files in repo_path
        if os.path.exists(repo_path):
            try:
                files = os.listdir(repo_path)
                logger.info(f"🔍 DEBUG: Files in repo_path: {files}")
                
                # Check for requirements.txt
                req_path = os.path.join(repo_path, "requirements.txt")
                logger.info(f"🔍 DEBUG: requirements.txt exists: {os.path.exists(req_path)}")
                
                # Check for test files
                test_files_found = []
                for root, dirs, files_in_dir in os.walk(repo_path):
                    for f in files_in_dir:
                        if f.startswith('test_') or f.endswith('_test.py'):
                            test_files_found.append(os.path.join(root, f))
                logger.info(f"🔍 DEBUG: Test files found: {test_files_found}")
            except Exception as e:
                logger.error(f"🔍 DEBUG: Error listing repo_path: {e}")
        else:
            logger.error(f"🔍 DEBUG: repo_path does NOT exist!")
        
        # Debug: Check if pytest is available
        pytest_path = shutil.which('pytest')
        logger.info(f"🔍 DEBUG: pytest executable location: {pytest_path}")
        
        # Check if python3.11 has pytest module
        try:
            import subprocess
            result = subprocess.run(
                ['python3.11', '-m', 'pytest', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            logger.info(f"🔍 DEBUG: pytest --version output: {result.stdout}")
            logger.info(f"🔍 DEBUG: pytest --version stderr: {result.stderr}")
            logger.info(f"🔍 DEBUG: pytest --version returncode: {result.returncode}")
        except Exception as e:
            logger.error(f"🔍 DEBUG: Error checking pytest: {e}")
        
        root = Path(repo_path)
        test_files = self._discover_test_files(root)
        logger.info(f"🔍 DEBUG: _discover_test_files() returned {len(test_files)} files")
        logger.info(f"🔍 DEBUG: Test files: {test_files}")
        
        if not test_files:
            logger.error(f"No test files discovered in {repo_path}")
            raise ValueError(f"No test files found in repository {repo_path}")

        logger.info(f"🔍 DEBUG: About to call sandbox_executor.run_pytest()")
        logger.info(f"🔍 DEBUG: Passing repo_path: {str(root)}")
        
        completed = self.sandbox_executor.run_pytest(str(root))
        
        logger.info(f"🔍 DEBUG: ===== PYTEST EXECUTION COMPLETE =====")
        logger.info(f"🔍 DEBUG: Exit code: {completed.returncode}")
        logger.info(f"🔍 DEBUG: STDOUT length: {len(completed.stdout)} chars")
        logger.info(f"🔍 DEBUG: STDERR length: {len(completed.stderr)} chars")
        logger.info(f"🔍 DEBUG: ----- FULL STDOUT -----")
        logger.info(completed.stdout)
        logger.info(f"🔍 DEBUG: ----- FULL STDERR -----")
        logger.info(completed.stderr)
        logger.info(f"🔍 DEBUG: ----- END OUTPUT -----")
        
        combined_output = f"{completed.stdout}\n{completed.stderr}"
        logger.debug(f"Pytest output:\n{combined_output}")
        
        if completed.returncode == 0:
            logger.info(f"🔍 DEBUG: Tests PASSED (returncode=0)")
            return TestRunResult(passed=True, failures=[])

        logger.info(f"🔍 DEBUG: Tests FAILED (returncode={completed.returncode})")
        logger.info(f"🔍 DEBUG: About to parse pytest output")
        
        # Handle pytest exit code 4: internal error/configuration error
        if completed.returncode == 4:
            logger.info(f"🔍 DEBUG: Exit code 4 detected - pytest configuration/setup error")
            setup_failure = self._parse_setup_error(combined_output, repo_path)
            if setup_failure:
                logger.info(f"🔍 DEBUG: Parsed setup error: {setup_failure.error_type}")
                return TestRunResult(passed=False, failures=[setup_failure])
        
        failures = self._parse_pytest_output(combined_output, repo_path)
        logger.info(f"🔍 DEBUG: Parsed {len(failures)} failure(s)")
        
        if not failures:
            logger.error(f"Tests failed but no failures parsed from output:\n{combined_output}")
            raise ValueError("Tests failed but no structured failures could be extracted from pytest output")
        
        logger.info(f"Parsed {len(failures)} failure(s)")
        return TestRunResult(passed=False, failures=failures)

    def _discover_test_files(self, root: Path) -> List[Path]:
        candidates = list(root.rglob("test_*.py")) + list(root.rglob("*_test.py"))
        return [path for path in candidates if ".venv" not in path.parts and "venv" not in path.parts]

    def _parse_pytest_output(self, output: str, repo_path: str) -> List[TestFailure]:
        """Parse pytest output including full Python tracebacks.
        
        Supports multiple formats:
        1. Python traceback: File "path.py", line 123, in function_name
        2. Pytest short format: path.py:123: message
        3. Pytest error format: E   ErrorType: message
        4. Error type extraction: NameError: name 'x' is not defined
        """
        failures: List[TestFailure] = []
        seen: set[tuple[str, int]] = set()
        
        # Pattern 1: Python traceback format - File "path", line 123
        traceback_pattern = re.compile(r'File "([^"]+)", line (\d+)')
        
        # Pattern 2: Pytest short format - path.py:123: in function_name
        pytest_location_pattern = re.compile(r'^([\w./\\-]+\.py):(\d+):\s+in\s+\w+', re.MULTILINE)
        
        # Pattern 3: Pytest error line - E   ErrorType: message
        pytest_error_pattern = re.compile(r'^E\s+(\w+(?:Error|Exception|Failure)):\s*(.+)$', re.MULTILINE)
        
        # Pattern 4: Error type - ErrorType: message (general)
        error_type_pattern = re.compile(r'^(\w*(?:Error|Exception|Failure)):\s*(.+)', re.MULTILINE)
        
        lines = output.split('\n')
        
        # Parse pytest verbose output with FAILURES section
        i = 0
        current_file = None
        current_line = None
        current_error_type = "UnknownError"
        current_message = ""
        current_traceback = []
        
        while i < len(lines):
            line = lines[i]
            
            # Look for file:line: in function_name pattern
            location_match = pytest_location_pattern.search(line)
            if location_match:
                current_file = location_match.group(1)
                current_line = int(location_match.group(2))
                current_file = self._normalize_file_path(current_file, repo_path)
                current_traceback = [line]
                logger.debug(f"Found failure location: {current_file}:{current_line}")
            
            # Look for E   ErrorType: message pattern (pytest error line)
            error_match = pytest_error_pattern.search(line)
            if error_match and current_file and current_line:
                current_error_type = error_match.group(1)
                current_message = error_match.group(2).strip()
                current_traceback.append(line)
                
                # We have complete failure info - save it
                key = (current_file, current_line)
                if key not in seen:
                    seen.add(key)
                    logger.debug(f"Parsed failure: {current_file}:{current_line} - {current_error_type}: {current_message}")
                    failures.append(
                        TestFailure(
                            file=current_file,
                            line_number=current_line,
                            message=current_message,
                            error_type=current_error_type,
                            full_traceback='\n'.join(current_traceback)
                        )
                    )
                
                # Reset for next failure
                current_file = None
                current_line = None
                current_error_type = "UnknownError"
                current_message = ""
                current_traceback = []
            elif current_traceback:
                # Accumulate traceback lines
                current_traceback.append(line)
            
            # Also handle Python traceback format (fallback)
            traceback_match = traceback_pattern.search(line)
            if traceback_match:
                file_path = traceback_match.group(1)
                line_number = int(traceback_match.group(2))
                file_path = self._normalize_file_path(file_path, repo_path)
                
                # Look ahead for error type
                error_type = "UnknownError"
                message = "Test failure"
                full_traceback = line
                
                for j in range(i + 1, min(i + 5, len(lines))):
                    full_traceback += "\n" + lines[j]
                    error_match = error_type_pattern.search(lines[j])
                    if error_match:
                        error_type = error_match.group(1)
                        message = error_match.group(2).strip()
                        break
                
                key = (file_path, line_number)
                if key not in seen and file_path.endswith('.py'):
                    seen.add(key)
                    logger.debug(f"Parsed Python traceback: {file_path}:{line_number} - {error_type}: {message}")
                    failures.append(
                        TestFailure(
                            file=file_path,
                            line_number=line_number,
                            message=message,
                            error_type=error_type,
                            full_traceback=full_traceback.strip()
                        )
                    )
            
            i += 1

        return failures
    
    def _parse_setup_error(self, output: str, repo_path: str) -> TestFailure | None:
        """Parse pytest setup/configuration errors (exit code 4).
        
        These are errors that occur before any tests run, like:
        - ImportError while loading conftest
        - ModuleNotFoundError for missing dependencies
        """
        lines = output.split('\n')
        
        # Look for patterns like:
        # "ImportError while loading conftest '/workspace/tests/conftest.py'"
        # "tests/conftest.py:4: in <module>"
        # "E   ModuleNotFoundError: No module named 'xyz'"
        
        error_file = None
        error_line = 1
        error_type = "ImportError"
        error_message = "Setup/configuration error"
        full_traceback = ""
        
        for i, line in enumerate(lines):
            # Extract file path and line number from patterns like:
            # "tests/conftest.py:4: in <module>"
            match = re.search(r'([\w./]+\.py):(\d+):', line)
            if match and not error_file:
                error_file = self._normalize_file_path(match.group(1), repo_path)
                error_line = int(match.group(2))
            
            # Extract error type and message from patterns like:
            # "E   ModuleNotFoundError: No module named 'pytest_httpbin'"
            if line.strip().startswith('E   '):
                error_match = re.search(r'E\s+(\w+(?:Error|Exception)?)\s*:\s*(.+)', line)
                if error_match:
                    error_type = error_match.group(1)
                    error_message = error_match.group(2).strip()
            
            # Build full traceback
            if error_file or line.strip().startswith('E   '):
                full_traceback += line + "\n"
        
        if error_file:
            logger.info(f"🔍 DEBUG: Parsed setup error - {error_file}:{error_line} - {error_type}: {error_message}")
            return TestFailure(
                file=error_file,
                line_number=error_line,
                message=error_message,
                error_type=error_type,
                full_traceback=full_traceback.strip()
            )
        
        return None
    
    def _normalize_file_path(self, file_path: str, repo_path: str) -> str:
        """Normalize file path to be relative to repo root."""
        # Remove absolute path prefixes
        if file_path.startswith(repo_path):
            file_path = file_path[len(repo_path):].lstrip('/')
        
        # Remove leading /workspace (from Docker)
        if file_path.startswith('/workspace/'):
            file_path = file_path[len('/workspace/'):]
        
        # Remove leading ./ 
        if file_path.startswith('./'):
            file_path = file_path[2:]
        
        return file_path
