"""
Evidence Service

Handles storage and retrieval of audit evidence for compliance runs.
Ensures all inputs, outputs, and metadata are persisted for auditability.

Uses repository pattern for storage abstraction - can be replaced with Postgres later.
"""

import csv
import io
import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from app.domain.models import (
    ComplianceRun,
    EmployeeResult,
    RunStatus,
    RunTotals,
)
from app.services.ingestion import RunContext
from app.services.validation import ValidationIssue


# ============================================================================
# Storage Interface (Abstract Base Class for Repository Pattern)
# ============================================================================


class IEvidenceRepository(ABC):
    """
    Abstract interface for evidence storage.

    This allows the storage implementation to be swapped out
    (e.g., SQLite → PostgreSQL) without changing business logic.
    """

    @abstractmethod
    async def store_raw_file(self, content: bytes, filename: str) -> str:
        """
        Store raw uploaded CSV file.

        Args:
            content: File content as bytes.
            filename: Original filename.

        Returns:
            File identifier for retrieval.
        """
        pass

    @abstractmethod
    async def retrieve_raw_file(self, file_id: str) -> Optional[bytes]:
        """
        Retrieve stored raw file.

        Args:
            file_id: The file identifier.

        Returns:
            File content as bytes, or None if not found.
        """
        pass

    @abstractmethod
    async def store_compliance_run(self, run: ComplianceRun) -> None:
        """
        Store a complete compliance run with all evidence.

        Args:
            run: The compliance run to store.
        """
        pass

    @abstractmethod
    async def get_compliance_run(self, run_id: str) -> Optional[ComplianceRun]:
        """
        Retrieve a compliance run by ID.

        Args:
            run_id: The run identifier.

        Returns:
            ComplianceRun if found, None otherwise.
        """
        pass

    @abstractmethod
    async def get_run_results(self, run_id: str) -> List[EmployeeResult]:
        """
        Retrieve results for a compliance run.

        Args:
            run_id: The run identifier.

        Returns:
            List of EmployeeResult.
        """
        pass

    @abstractmethod
    async def get_run_issues(self, run_id: str) -> List[ValidationIssue]:
        """
        Retrieve validation issues for a compliance run.

        Args:
            run_id: The run identifier.

        Returns:
            List of ValidationIssue.
        """
        pass


# ============================================================================
# Concrete Implementation Using Current Storage Layer
# ============================================================================


class EvidenceRepository(IEvidenceRepository):
    """
    Concrete implementation of evidence storage using current repositories.

    This wraps the existing storage layer (repo_files, repo_runs) to provide
    the evidence interface. Can be replaced with PostgresEvidenceRepository later.
    """

    def __init__(self):
        """Initialize with storage dependencies."""
        from app.storage.repo_files import get_file_store
        from app.storage.repo_runs import RunRepository
        from app.storage.db import async_session_maker

        self._file_store = get_file_store()
        self._session_maker = async_session_maker

    async def store_raw_file(self, content: bytes, filename: str) -> str:
        """Store raw uploaded CSV file."""
        return await self._file_store.store(content, filename, "text/csv")

    async def retrieve_raw_file(self, file_id: str) -> Optional[bytes]:
        """Retrieve stored raw file."""
        return await self._file_store.retrieve(file_id)

    async def store_compliance_run(self, run: ComplianceRun) -> None:
        """Store a complete compliance run with all evidence."""
        async with self._session_maker() as session:
            from app.storage.repo_runs import RunRepository

            repo = RunRepository(session)
            await repo.create_run(run)
            await session.commit()

    async def get_compliance_run(self, run_id: str) -> Optional[ComplianceRun]:
        """Retrieve a compliance run by ID."""
        async with self._session_maker() as session:
            from app.storage.repo_runs import RunRepository

            repo = RunRepository(session)
            return await repo.get_run(run_id)

    async def get_run_results(self, run_id: str) -> List[EmployeeResult]:
        """Retrieve results for a compliance run."""
        async with self._session_maker() as session:
            from app.storage.repo_runs import RunRepository

            repo = RunRepository(session)
            return await repo.get_run_results(run_id)

    async def get_run_issues(self, run_id: str) -> List[ValidationIssue]:
        """Retrieve validation issues for a compliance run."""
        async with self._session_maker() as session:
            from app.storage.repo_runs import RunRepository

            repo = RunRepository(session)
            # Note: This returns domain.models.ValidationIssue, not services.validation.ValidationIssue
            # May need conversion
            return await repo.get_run_issues(run_id)


# ============================================================================
# Evidence Service Functions
# ============================================================================


def generate_run_id() -> str:
    """
    Generate a unique run identifier.

    Returns:
        Unique run ID with timestamp and random component.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_part = uuid.uuid4().hex[:8]
    return f"run_{timestamp}_{unique_part}"


def create_compliance_run(
    run_id: str,
    run_context: RunContext,
    results: List[EmployeeResult],
    issues: List[ValidationIssue],
    totals: RunTotals,
    ruleset_version_used: str,
    raw_file_id: Optional[str] = None,
) -> ComplianceRun:
    """
    Create a ComplianceRun object with all evidence.

    This creates an immutable record of the compliance run including:
    - Run metadata (from RunContext)
    - Calculated results (per-employee)
    - Validation issues (errors/warnings)
    - Aggregated totals
    - Ruleset version used
    - Reference to raw file
    - Timestamps

    Args:
        run_id: Unique run identifier.
        run_context: Context extracted from CSV (shared run-level fields).
        results: Calculated employee results.
        issues: Validation issues (converted from services.validation.ValidationIssue).
        totals: Aggregated totals.
        ruleset_version_used: Ruleset version ID used for calculations.
        raw_file_id: Reference to stored raw CSV file.

    Returns:
        ComplianceRun object ready for persistence.
    """
    # Convert services.validation.ValidationIssue to domain.models.ValidationIssue
    from app.domain.models import ValidationIssue as DomainValidationIssue, IssueSeverity

    domain_issues = []
    for issue in issues:
        # Map string severity to enum
        severity_map = {
            "error": IssueSeverity.ERROR,
            "warn": IssueSeverity.WARNING,
            "info": IssueSeverity.WARNING,  # Map info to warning for now
        }

        domain_issues.append(
            DomainValidationIssue(
                row_number=issue.row_index + 2 if issue.row_index >= 0 else None,  # Convert 0-based to 1-based (header is row 1)
                employee_id=issue.employee_id,
                severity=severity_map.get(issue.severity, IssueSeverity.WARNING),
                code=issue.code,
                message=issue.message,
                field=issue.field,
            )
        )

    return ComplianceRun(
        run_id=run_id,
        payroll_run_id=run_context.payroll_run_id,  # From CSV - external audit reference
        company_id=run_context.company_id,
        pay_date=run_context.pay_date,
        tax_year=run_context.tax_year,
        payroll_frequency=run_context.payroll_frequency,
        ruleset_version_used=ruleset_version_used,
        status=RunStatus.COMPLETED,
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        results=results,
        issues=domain_issues,
        totals=totals,
        raw_file_id=raw_file_id,
    )


async def persist_compliance_run(
    run: ComplianceRun,
    repository: Optional[IEvidenceRepository] = None,
) -> None:
    """
    Persist a compliance run using the evidence repository.

    This stores all evidence:
    - Run metadata
    - Employee results
    - Validation issues
    - Aggregated totals
    - Timestamps
    - Ruleset version

    The raw file should be stored separately before calling this.

    Args:
        run: The compliance run to persist.
        repository: Evidence repository (uses default if not provided).
    """
    if repository is None:
        repository = EvidenceRepository()

    await repository.store_compliance_run(run)


async def store_raw_file(
    content: bytes,
    filename: str,
    repository: Optional[IEvidenceRepository] = None,
) -> str:
    """
    Store the raw uploaded CSV file.

    Args:
        content: File content as bytes.
        filename: Original filename.
        repository: Evidence repository (uses default if not provided).

    Returns:
        File identifier for retrieval.
    """
    if repository is None:
        repository = EvidenceRepository()

    return await repository.store_raw_file(content, filename)


async def retrieve_raw_file(
    file_id: str,
    repository: Optional[IEvidenceRepository] = None,
) -> Optional[bytes]:
    """
    Retrieve a stored raw CSV file.

    Args:
        file_id: The file identifier.
        repository: Evidence repository (uses default if not provided).

    Returns:
        File content as bytes, or None if not found.
    """
    if repository is None:
        repository = EvidenceRepository()

    return await repository.retrieve_raw_file(file_id)


async def get_compliance_run(
    run_id: str,
    repository: Optional[IEvidenceRepository] = None,
) -> Optional[ComplianceRun]:
    """
    Retrieve a complete compliance run.

    Args:
        run_id: The run identifier.
        repository: Evidence repository (uses default if not provided).

    Returns:
        ComplianceRun if found, None otherwise.
    """
    if repository is None:
        repository = EvidenceRepository()

    return await repository.get_compliance_run(run_id)


def generate_results_csv(results: List[EmployeeResult]) -> bytes:
    """
    Generate a CSV export of employee results.

    Args:
        results: List of employee results.

    Returns:
        CSV content as bytes.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "employee_id",
        "gross_income",
        "taxable_income",
        "paye",
        "uif_employee",
        "uif_employer",
        "sdl",
        "net_pay",
        "total_employer_cost",
    ])

    # Data rows
    for result in results:
        writer.writerow([
            result.employee_id,
            str(result.gross_income),
            str(result.taxable_income),
            str(result.paye),
            str(result.uif_employee),
            str(result.uif_employer),
            str(result.sdl),
            str(result.net_pay),
            str(result.total_employer_cost),
        ])

    return output.getvalue().encode("utf-8")


# ============================================================================
# Default Repository Instance
# ============================================================================

_default_repository: Optional[IEvidenceRepository] = None


def get_evidence_repository() -> IEvidenceRepository:
    """
    Get the default evidence repository instance.

    This uses a singleton pattern. Can be replaced with dependency injection
    in production (e.g., FastAPI Depends).

    Returns:
        Evidence repository instance.
    """
    global _default_repository
    if _default_repository is None:
        _default_repository = EvidenceRepository()
    return _default_repository


def set_evidence_repository(repository: IEvidenceRepository) -> None:
    """
    Set a custom evidence repository (useful for testing or swapping implementations).

    Args:
        repository: The repository to use.
    """
    global _default_repository
    _default_repository = repository

