"""
Generate expected outputs from Excel (oracle mode, Windows only).

Requires Excel and xlwings installed.
Writes CSV to data/samples/expected_from_excel.csv.
"""

from __future__ import annotations

import csv
from pathlib import Path


def _normalize_header(value: str) -> str:
    return (
        value.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("(", "")
        .replace(")", "")
    )


def generate_expected_from_excel(workbook_path: Path, output_path: Path) -> None:
    try:
        import xlwings as xw
    except ImportError as exc:
        raise RuntimeError("xlwings is required for EXCEL_ORACLE mode") from exc

    app = xw.App(visible=False)
    try:
        book = app.books.open(str(workbook_path))
        book.app.calculate()
        ws = book.sheets["Outputs"]

        used = ws.used_range.value
        if not used or not isinstance(used, list):
            raise ValueError("Outputs sheet is empty.")

        header_row = None
        for idx, row in enumerate(used, start=1):
            if not row:
                continue
            if any(str(v).strip().lower() == "employee id" for v in row if v is not None):
                header_row = idx
                break

        if header_row is None:
            raise ValueError("Outputs header row not found (expected 'Employee ID').")

        headers = [
            _normalize_header(str(v)) if v is not None and str(v).strip() else ""
            for v in used[header_row - 1]
        ]

        col_map = {
            "employee_id": headers.index("employee_id"),
            "gross_income": headers.index("gross_pay_monthly") if "gross_pay_monthly" in headers else headers.index("gross_income"),
            "paye": headers.index("paye"),
            "uif_employee": headers.index("uif_employee"),
            "uif_employer": headers.index("uif_employer"),
            "sdl": headers.index("sdl"),
            "net_pay": headers.index("net_pay"),
            "total_employer_cost": headers.index("employer_cost") if "employer_cost" in headers else headers.index("total_employer_cost"),
        }

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

            for row in used[header_row:]:
                if not row or not row[col_map["employee_id"]]:
                    break
                emp_id = str(row[col_map["employee_id"]])
                if emp_id.upper() == "TOTALS":
                    break
                writer.writerow(
                    {
                        "employee_id": emp_id,
                        "gross_income": f"{row[col_map['gross_income']]:.2f}",
                        "taxable_income": "",
                        "paye": f"{row[col_map['paye']]:.2f}",
                        "uif_employee": f"{row[col_map['uif_employee']]:.2f}",
                        "uif_employer": f"{row[col_map['uif_employer']]:.2f}",
                        "sdl": f"{row[col_map['sdl']]:.2f}",
                        "net_pay": f"{row[col_map['net_pay']]:.2f}",
                        "total_employer_cost": f"{row[col_map['total_employer_cost']]:.2f}",
                    }
                )
    finally:
        app.kill()


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    workbook_path = repo_root / "data" / "sa_payroll_workbook.xlsx"
    output_path = repo_root / "data" / "samples" / "expected_from_excel.csv"

    generate_expected_from_excel(workbook_path, output_path)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
