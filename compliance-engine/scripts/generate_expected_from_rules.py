"""
Generate expected outputs from workbook-derived rules (deterministic mode).

Reads inputs_from_workbook.csv and produces expected_from_rules.csv.
"""

from __future__ import annotations

import csv
import json
from decimal import Decimal
from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

from app.services.ingestion import parse_csv_with_issues
from app.services.validation import validate_rows
from app.reference.reference_calculator import (
    calculate_reference_results,
    load_ruleset_from_json,
)


def generate_expected_from_rules(
    inputs_path: Path,
    output_path: Path,
) -> None:
    csv_bytes = inputs_path.read_bytes()
    rows, run_context, parse_issues = parse_csv_with_issues(csv_bytes)

    if parse_issues:
        errors = [i for i in parse_issues if i.severity == "error"]
        if errors:
            raise ValueError(f"Parse errors found: {len(errors)}")

    ruleset_json = json.loads((repo_root / "data" / "samples" / "ruleset_from_workbook.json").read_text(encoding="utf-8"))
    reference_ruleset = load_ruleset_from_json(ruleset_json)

    reference_results = calculate_reference_results(rows, reference_ruleset)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "employee_id",
                "gross_income",
                "taxable_income",
                "paye",
                "uif_employee",
                "uif_employer",
                "sdl",
                "net_pay",
                "total_employer_cost",
            ],
        )
        writer.writeheader()
        for row in reference_results:
            writer.writerow(
                {
                    "employee_id": row.employee_id,
                    "gross_income": f"{row.gross_income:.2f}",
                    "taxable_income": f"{row.taxable_income:.2f}",
                    "paye": f"{row.paye:.2f}",
                    "uif_employee": f"{row.uif_employee:.2f}",
                    "uif_employer": f"{row.uif_employer:.2f}",
                    "sdl": f"{row.sdl:.2f}",
                    "net_pay": f"{row.net_pay:.2f}",
                    "total_employer_cost": f"{row.total_employer_cost:.2f}",
                }
            )


def main() -> None:
    inputs_path = repo_root / "data" / "samples" / "inputs_from_workbook.csv"
    output_path = repo_root / "data" / "samples" / "expected_from_rules.csv"

    generate_expected_from_rules(inputs_path, output_path)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
