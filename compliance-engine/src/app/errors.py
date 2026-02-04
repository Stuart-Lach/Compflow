"""
Custom exception classes for the Compliance Engine.
"""

from typing import Any, Dict, List, Optional


class ComplianceEngineError(Exception):
    """Base exception for all compliance engine errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(ComplianceEngineError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        errors: Optional[List[Dict[str, Any]]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.errors = errors or []


class SchemaValidationError(ValidationError):
    """Raised when CSV schema validation fails (missing columns, invalid types)."""

    pass


class RowValidationError(ValidationError):
    """Raised when row-level validation fails."""

    pass


class RulesetNotFoundError(ComplianceEngineError):
    """Raised when a requested ruleset cannot be found."""

    pass


class RunNotFoundError(ComplianceEngineError):
    """Raised when a compliance run cannot be found."""

    pass


class CalculationError(ComplianceEngineError):
    """Raised when a calculation fails."""

    pass


class StorageError(ComplianceEngineError):
    """Raised when storage operations fail."""

    pass


class FileStorageError(StorageError):
    """Raised when file storage operations fail."""

    pass

