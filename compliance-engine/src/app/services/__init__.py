"""Services package."""

from app.services.calculation import (
    CalculationResult,
    calculate_compliance_run,
    calculate_employee,
    calculate_paye,
    calculate_sdl,
    calculate_totals,
    calculate_uif,
)
from app.services.evidence import (
    IEvidenceRepository,
    EvidenceRepository,
    create_compliance_run,
    generate_results_csv,
    generate_run_id,
    get_compliance_run,
    get_evidence_repository,
    persist_compliance_run,
    retrieve_raw_file,
    set_evidence_repository,
    store_raw_file,
)
from app.services.ingestion import parse_csv, parse_csv_with_issues, RunContext
from app.services.validation import (
    is_sdl_liable,
    is_uif_applicable,
    validate_rows,
    ValidationIssue,
    filter_errors,
    has_errors,
    get_valid_row_indices,
)

__all__ = [
    # Calculation
    "CalculationResult",
    "calculate_compliance_run",
    "calculate_employee",
    "calculate_paye",
    "calculate_sdl",
    "calculate_totals",
    "calculate_uif",
    # Evidence
    "IEvidenceRepository",
    "EvidenceRepository",
    "create_compliance_run",
    "generate_results_csv",
    "generate_run_id",
    "get_compliance_run",
    "get_evidence_repository",
    "persist_compliance_run",
    "retrieve_raw_file",
    "set_evidence_repository",
    "store_raw_file",
    # Ingestion
    "parse_csv",
    "RunContext",
    # Validation
    "is_sdl_liable",
    "is_uif_applicable",
    "validate_rows",
    "ValidationIssue",
    "filter_errors",
    "has_errors",
    "get_valid_row_indices",
]

