from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset"
OUTPUT_PATH = ROOT / "output.csv"

app = FastAPI(title="GhostTrace", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_STATUS = {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}
VALID_PHASES = {"FINDING", "REMEDIATION", "VERIFICATION"}
VALID_OPERATIONS = {
    "REPORT_REMAINING_RECORD",
    "REPORT_EXPOSED_PII",
    "REPORT_ACTIVE_DATA_FLOW",
    "REPORT_RESTORE_RISK",
    "DISABLE_DATA_FLOW",
    "BLOCK_RESTORE",
    "DELETE_RECORD",
    "REDACT_RECORD",
    "ANONYMIZE_RECORD",
    "VERIFY_RECORD_ABSENT",
    "VERIFY_RECORD_PRESENT",
    "VERIFY_RECORD_REDACTED",
    "VERIFY_RECORD_ANONYMIZED",
    "VERIFY_DATA_FLOW_DISABLED",
    "VERIFY_RESTORE_BLOCKED",
}


def read_csv_file(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def safe_json_load(raw: str) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def mask_email(email: str) -> str:
    if not email:
        return "unknown@example.com"
    email = email.strip()
    if "@" not in email:
        return "***@unknown"
    local, domain = email.split("@", 1)
    local = local[:2] + "***" if len(local) > 2 else "**"
    return f"{local}@{domain}"


def case_sort_key(case_id: str) -> tuple[int, Any]:
    if not isinstance(case_id, str):
        return (0, 0)
    match = re.search(r"(\d+)$", case_id)
    if match:
        return (0, int(match.group(1)))
    return (1, case_id)


def build_case_records() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    request_rows = read_csv_file(DATASET / "deletion_requests.csv")
    output_rows = read_csv_file(OUTPUT_PATH)
    rules_rows = read_csv_file(DATASET / "deletion_rules.csv")
    output_by_id = {row.get("case_id", ""): row for row in output_rows if row.get("case_id")}
    request_by_id = {row.get("case_id", ""): row for row in request_rows if row.get("case_id")}

    all_cases = []
    for row in request_rows:
        case_id = row.get("case_id", "")
        output_row = output_by_id.get(case_id, {})
        steps_raw = safe_json_load(output_row.get("steps_json", "[]"))
        steps = []
        for item in steps_raw:
            if not isinstance(item, dict):
                continue
            steps.append({
                "step_no": item.get("step_no", 0),
                "phase": item.get("phase", ""),
                "system_id": item.get("system_id", ""),
                "resource_id": item.get("resource_id", ""),
                "operation": item.get("operation", ""),
                "state": item.get("state", ""),
                "evidence_id": item.get("evidence_id", ""),
            })
        case = {
            "case_id": case_id,
            "email": row.get("email", ""),
            "masked_email": mask_email(row.get("email", "")),
            "requested_at": row.get("requested_at", ""),
            "reported_status": row.get("reported_status", ""),
            "reported_at": row.get("reported_at", ""),
            "audit_at": row.get("audit_at", ""),
            "request_text": row.get("request_text", ""),
            "deletion_status": output_row.get("deletion_status", "UNKNOWN"),
            "steps": steps,
            "audit_steps_count": len(steps),
            "validation_state": validate_case_output(case_id, output_row, steps),
            "source": "generated_output",
        }
        all_cases.append(case)

    return all_cases, output_by_id, {row.get("rule_id", ""): row for row in rules_rows if row.get("rule_id")}


def validate_case_output(case_id: str, output_row: dict[str, str], steps: list[dict[str, Any]]) -> str:
    status = output_row.get("deletion_status", "")
    if status not in ALLOWED_STATUS:
        return "INVALID_STATUS"
    if not case_id:
        return "INVALID_CASE_ID"
    if not isinstance(steps, list):
        return "INVALID_JSON"
    for idx, step in enumerate(steps, start=1):
        if step.get("phase") not in VALID_PHASES:
            return "INVALID_STEP"
        if step.get("operation") not in VALID_OPERATIONS and step.get("operation") not in {"", None}:
            return "INVALID_STEP"
        if int(step.get("step_no", 0)) != idx:
            return "INVALID_STEP_ORDER"
        if step.get("phase") == "FINDING" and status == "COMPLETE":
            return "INVALID_COMPLETE_CASE"
        if step.get("evidence_id") is None:
            return "INVALID_EVIDENCE"
    return "VALID"


def get_summary_payload() -> dict[str, Any]:
    cases, _, _ = build_case_records()
    counts = Counter(case["deletion_status"] for case in cases)
    total = len(cases)
    return {
        "total_requests": total,
        "complete": counts.get("COMPLETE", 0),
        "incomplete": counts.get("INCOMPLETE", 0),
        "not_applicable": counts.get("NOT_APPLICABLE", 0),
        "status_distribution": [
            {"name": "COMPLETE", "value": counts.get("COMPLETE", 0)},
            {"name": "INCOMPLETE", "value": counts.get("INCOMPLETE", 0)},
            {"name": "NOT_APPLICABLE", "value": counts.get("NOT_APPLICABLE", 0)},
        ],
        "live_data_source": "generated_output",
        "rows_loaded": total,
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "dataset": str(DATASET), "output": str(OUTPUT_PATH)}


@app.get("/api/summary")
def summary() -> dict[str, Any]:
    return get_summary_payload()


@app.get("/api/cases")
def list_cases(
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    reported_status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    sort_by: str = Query(default="case_id"),
    sort_dir: str = Query(default="asc"),
) -> dict[str, Any]:
    cases, _, _ = build_case_records()
    filtered = []
    q = (search or "").strip().lower()
    for case in cases:
        haystack = f"{case['case_id']} {case['email']} {case['masked_email']}".lower()
        if q and q not in haystack:
            continue
        if status and case.get("deletion_status") != status:
            continue
        if reported_status and case.get("reported_status") != reported_status:
            continue
        filtered.append(case)

    allowed_sort = {"case_id", "requested_at", "reported_status", "deletion_status", "audit_steps_count"}
    if sort_by not in allowed_sort:
        sort_by = "case_id"
    reverse = sort_dir.lower() == "desc"
    if sort_by == "case_id":
        filtered.sort(key=lambda c: case_sort_key(c.get(sort_by) or ""), reverse=reverse)
    else:
        filtered.sort(key=lambda c: (c.get(sort_by) or ""), reverse=reverse)

    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = filtered[start:end]
    return {
        "items": page_items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": max(1, (total + page_size - 1) // page_size),
        "query": {"search": q, "status": status, "reported_status": reported_status, "sort_by": sort_by, "sort_dir": sort_dir},
        "data_source": "generated_output",
    }


@app.get("/api/cases/{case_id}")
def get_case(case_id: str) -> dict[str, Any]:
    cases, _, _ = build_case_records()
    target = next((case for case in cases if case["case_id"] == case_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"case": target, "data_source": "generated_output"}


@app.get("/api/evidence")
def evidence_list() -> dict[str, Any]:
    rows = read_csv_file(DATASET / "evidence_files.csv")
    evidence = []
    for row in rows:
        file_path = (DATASET / row.get("file_path", "")).resolve()
        accessible = file_path.exists() and DATASET in file_path.parents or file_path == DATASET
        evidence.append({
            "file_id": row.get("file_id", ""),
            "file_path": row.get("file_path", ""),
            "origin": row.get("origin", ""),
            "captured_at": row.get("captured_at", ""),
            "file_type": Path(row.get("file_path", "")).suffix.lower().lstrip("."),
            "accessible": accessible,
        })
    return {"items": evidence, "total": len(evidence), "data_source": "manifest"}


@app.get("/api/evidence/{evidence_id}")
def evidence_detail(evidence_id: str) -> dict[str, Any]:
    rows = read_csv_file(DATASET / "evidence_files.csv")
    row = next((r for r in rows if r.get("file_id") == evidence_id), None)
    if row is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    rel = row.get("file_path", "")
    if rel.startswith("../") or "/../" in rel or rel.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid evidence path")
    safe_path = (DATASET / rel).resolve()
    if not safe_path.exists() or DATASET not in safe_path.parents and safe_path != DATASET:
        raise HTTPException(status_code=404, detail="Evidence file is not available")
    prefix = safe_path.suffix.lower()
    preview = ""
    accessible = safe_path.exists()
    if prefix in {".json", ".csv", ".log", ".txt", ".sql"}:
        try:
            preview = safe_path.read_text(encoding="utf-8", errors="replace")[:2000]
        except OSError:
            preview = ""
    elif prefix in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        preview = f"image:{safe_path.name}"
    elif prefix in {".pdf"}:
        preview = f"pdf:{safe_path.name}"
    return {
        "evidence_id": evidence_id,
        "metadata": row,
        "safe_path": str(safe_path.relative_to(ROOT)),
        "preview": preview,
        "preview_type": "text" if prefix in {".json", ".csv", ".log", ".txt", ".sql"} else "image" if prefix in {".png", ".jpg", ".jpeg", ".webp", ".gif"} else "pdf" if prefix == ".pdf" else "unsupported",
        "accessible": accessible,
    }


@app.get("/api/rules")
def rules() -> dict[str, Any]:
    rows = read_csv_file(DATASET / "deletion_rules.csv")
    return {"items": rows, "total": len(rows)}


@app.get("/api/validation")
def validation() -> dict[str, Any]:
    cases, output_by_id, _ = build_case_records()
    invalid = []
    for case in cases:
        validation_state = validate_case_output(case["case_id"], output_by_id.get(case["case_id"], {}), case["steps"])
        if validation_state != "VALID":
            invalid.append({"case_id": case["case_id"], "error": validation_state})
    return {
        "total_cases": len(cases),
        "validated_cases": len(cases) - len(invalid),
        "invalid_cases": len(invalid),
        "errors": invalid,
        "columns": ["case_id", "deletion_status", "steps_json"],
        "source": "generated_output",
    }


@app.get("/api/export/output.csv")
def export_output() -> FileResponse:
    if not OUTPUT_PATH.exists():
        raise HTTPException(status_code=404, detail="output.csv not generated yet")
    return FileResponse(OUTPUT_PATH, media_type="text/csv", filename="output.csv")


@app.get("/api/healthcheck")
def legacy_health() -> dict[str, str]:
    return health()
