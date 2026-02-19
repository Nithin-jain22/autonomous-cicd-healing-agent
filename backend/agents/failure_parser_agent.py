from __future__ import annotations

from dataclasses import dataclass
import logging

from models import BugType

logger = logging.getLogger(__name__)


@dataclass
class ParsedFailure:
    file: str
    line_number: int
    bug_type: BugType
    raw_message: str
    error_type: str = "UnknownError"


class FailureParserAgent:
    def parse_failure(self, file: str, line_number: int, message: str, error_type: str = "UnknownError") -> ParsedFailure:
        """Parse failure and classify bug type based on error type and message.
        
        NO DEFAULTS - bug_type must be derived from actual error information.
        """
        bug_type = self._classify_bug_type(error_type, message)
        logger.debug(f"Classified {error_type} as {bug_type.value}: {message[:50]}")
        
        return ParsedFailure(
            file=file,
            line_number=line_number,
            bug_type=bug_type,
            raw_message=message,
            error_type=error_type,
        )
    
    def _classify_bug_type(self, error_type: str, message: str) -> BugType:
        """Classify bug type based on Python error type and message.
        
        Priority:
        1. Error type name (NameError, ImportError, etc.)
        2. Message keywords
        3. Only default to LOGIC if truly ambiguous
        """
        error_lower = error_type.lower()
        message_lower = message.lower()
        
        # Import errors
        if "importerror" in error_lower or "modulenotfounderror" in error_lower:
            return BugType.IMPORT
        if "import" in message_lower and ("cannot" in message_lower or "no module" in message_lower):
            return BugType.IMPORT
        # NameError for undefined names - often missing imports
        if "nameerror" in error_lower and "is not defined" in message_lower:
            return BugType.IMPORT
        
        # Syntax errors
        if "syntaxerror" in error_lower or "invalidsyntax" in error_lower:
            return BugType.SYNTAX
        if "syntax" in message_lower:
            return BugType.SYNTAX
        
        # Indentation errors
        if "indentationerror" in error_lower or "taberror" in error_lower:
            return BugType.INDENTATION
        if "indent" in message_lower or "unexpected indent" in message_lower:
            return BugType.INDENTATION
        
        # Type errors
        if "typeerror" in error_lower or "attributeerror" in error_lower:
            return BugType.TYPE_ERROR
        if "type" in message_lower and ("expected" in message_lower or "got" in message_lower):
            return BugType.TYPE_ERROR
        
        # Linting (if caught by linter or style checker)
        if "lint" in message_lower or "flake8" in message_lower or "pylint" in message_lower:
            return BugType.LINTING
        
        # Default to LOGIC for assertion errors, value errors, name errors, etc.
        return BugType.LOGIC
