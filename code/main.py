import csv
import json
import re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"
OUTPUT = ROOT / "output.csv"

# The operation order is part of the challenge's output contract.
FINDING_ORDER = {
    "REPORT_REMAINING_RECORD": 0,
    "REPORT_EXPOSED_PII": 1,
    "REPORT_ACTIVE_DATA_FLOW": 2,
    "REPORT_RESTORE_RISK": 3,
}
REMEDIATION_ORDER = {
    "DISABLE_DATA_FLOW": 0,
    "BLOCK_RESTORE": 1,
    "DELETE_RECORD": 2,
    "REDACT_RECORD": 3,
    "ANONYMIZE_RECORD": 4,
}
VERIFICATION_ORDER = {
    "VERIFY_RECORD_ABSENT": 0,
    "VERIFY_RECORD_PRESENT": 1,
    "VERIFY_RECORD_REDACTED": 2,
    "VERIFY_RECORD_ANONYMIZED": 3,
    "VERIFY_DATA_FLOW_DISABLED": 4,
    "VERIFY_RESTORE_BLOCKED": 5,
}

def read_csv(name):
    with (DATASET / name).open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def parse_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def normalize_text(value):
    if value is None:
        return ""
    return str(value).strip().lower()


def normalize_phone(value):
    return re.sub(r"\D+", "", str(value or ""))


def resolve_case_identity(case, users, audit_log):
    request_email = normalize_text(case.get("email"))
    request_phone = normalize_phone(case.get("phone") or case.get("email"))

    user_map = {normalize_text(u.get("user_id")): u for u in users if u.get("user_id")}
    audit_by_user = {}
    for row in audit_log:
        user_id = (row.get("user_id") or "").strip()
        if not user_id:
            continue
        audit_by_user.setdefault(user_id, []).append(row)

    def historical_values_for(user_id):
        emails = set()
        phones = set()
        for row in audit_by_user.get(user_id, []):
            field = normalize_text(row.get("field_name"))
            for value in (row.get("old_value"), row.get("new_value")):
                if not value:
                    continue
                if field in {"email", "email_address", "new_email", "old_email"}:
                    emails.add(normalize_text(value))
                if field in {"phone", "mobile", "phone_number"}:
                    digits = normalize_phone(value)
                    if digits:
                        phones.add(digits)
        return emails, phones

    direct_match = None
    if request_email:
        direct_match = next((u for u in users if normalize_text(u.get("email")) == request_email), None)

    if direct_match is None:
        for user in users:
            uid = (user.get("user_id") or "").strip()
            emails = {normalize_text(user.get("email"))}
            phones = {normalize_phone(user.get("phone"))}
            hist_emails, hist_phones = historical_values_for(uid)
            emails |= hist_emails
            phones |= hist_phones
            if request_email in emails or request_phone in phones:
                direct_match = user
                break

    if direct_match is None:
        user = {
            "user_id": "",
            "email": case.get("email") or "",
            "phone": case.get("phone") or "",
            "email_hash": "",
            "historical_emails": [],
            "historical_phones": [],
        }
        return user

    user_id = (direct_match.get("user_id") or "").strip()
    hist_emails, hist_phones = historical_values_for(user_id)
    result = {
        "user_id": user_id,
        "email": (direct_match.get("email") or "").strip(),
        "phone": (direct_match.get("phone") or "").strip(),
        "email_hash": (direct_match.get("email_hash") or "").strip(),
        "historical_emails": sorted({normalize_text(direct_match.get("email"))} | hist_emails),
        "historical_phones": sorted({normalize_phone(direct_match.get("phone"))} | hist_phones),
    }
    result["historical_emails"] = [v for v in result["historical_emails"] if v]
    result["historical_phones"] = [v for v in result["historical_phones"] if v]
    return result


def flatten(obj):
    if isinstance(obj, dict):
        out = []
        for k, v in obj.items():
            out.append(str(k))
            out.extend(flatten(v))
        return out
    if isinstance(obj, list):
        out = []
        for v in obj:
            out.extend(flatten(v))
        return out
    if obj is None:
        return []
    return [str(obj)]

def category_for(system, collection, resource, record_type=""):
    s = (system or "").lower()
    c = (collection or "").lower()
    r = (resource or "").lower()
    t = (record_type or "").lower()
    joined = " ".join((s, c, r, t))
    if "data_flow" in joined or "integration" in s:
        return "DATA_FLOW"
    if "backup" in joined or "archive" in joined:
        return "BACKUP_ARCHIVE"
    if "tombstone" in joined or "deleted_customer_reference" in joined:
        return "ACCOUNT_TOMBSTONE"
    if "security_audit" in joined or "audit_record" in r or "security_service" in s:
        return "SECURITY_AUDIT_LOG"
    if "legal_hold" in joined:
        return "LEGAL_HOLD_RECORD"
    if "delivery" in joined or "notification" in joined or "email_delivery" in joined:
        return "EMAIL_DELIVERY_LOG"
    if "marketing" in joined:
        return "MARKETING_PROFILE"
    if "export" in joined:
        return "USER_EXPORT"
    if "support_attachment" in joined or "attachment" in joined:
        return "SUPPORT_ATTACHMENT"
    if "support" in joined or "conversation" in joined or "ticket" in joined:
        return "SUPPORT_MESSAGE"
    if "analytics" in joined:
        return "ANALYTICS_PROFILE"
    if "telemetry" in joined:
        return "PRODUCT_TELEMETRY"
    if "search" in joined or r.startswith("search_"):
        return "SEARCH_INDEX_ENTRY"
    if "cache" in joined:
        return "CACHE_ENTRY"
    if "account" in joined or "profile" in joined or r.startswith("account_"):
        return "USER_PROFILE"
    return "UNKNOWN"

def system_for(system, category):
    if system:
        s = str(system).strip()
        aliases = {
            "account": "account_service", "accounts": "account_service",
            "identity": "identity_service", "search": "search_service",
            "analytics": "analytics_platform", "support": "support_platform",
            "export": "export_service", "marketing": "marketing_platform",
            "backup": "backup_service", "integration": "integration_service",
            "security": "security_service", "cache": "cache_service",
        }
        low = s.lower()
        if low in aliases:
            return aliases[low]
        return s
    return {
        "USER_PROFILE": "account_service",
        "SECONDARY_IDENTIFIER": "identity_service",
        "SEARCH_INDEX_ENTRY": "search_service",
        "CACHE_ENTRY": "cache_service",
        "SUPPORT_MESSAGE": "support_platform",
        "SUPPORT_ATTACHMENT": "support_platform",
        "ANALYTICS_PROFILE": "analytics_platform",
        "PRODUCT_TELEMETRY": "analytics_platform",
        "USER_EXPORT": "export_service",
        "MARKETING_PROFILE": "marketing_platform",
        "EMAIL_DELIVERY_LOG": "notification_service",
        "SECURITY_AUDIT_LOG": "security_service",
        "LEGAL_HOLD_RECORD": "legal_service",
        "BACKUP_ARCHIVE": "backup_service",
        "ACCOUNT_TOMBSTONE": "identity_service",
        "DATA_FLOW": "integration_service",
    }.get(category, "unknown_service")

def pii_present(obj):
    if not isinstance(obj, dict):
        return False
    fields = ("email", "phone", "email_hash", "full_name", "name", "display_name")
    return any(obj.get(k) not in (None, "", "null") for k in fields)

def state_for(category, obj, text=""):
    text_low = (text or "").lower()
    status_vals = []
    if isinstance(obj, dict):
        status_vals = [
            str(obj.get(k, "" )).upper()
            for k in ("status", "result", "state", "account_status", "restore_status",
                      "download_available", "enabled", "active", "record_state")
        ]
    joined = " ".join(status_vals).upper() + " " + text.upper()
    if category == "DATA_FLOW":
        if "DISABLED" in joined or "INACTIVE" in joined or "ENABLED FALSE" in joined:
            return "DISABLED"
        return "ACTIVE"
    if category == "BACKUP_ARCHIVE":
        return "BLOCKED" if "BLOCKED" in joined or "RESTORE_BLOCKED" in joined else "ACTIVE"
    if category == "SECURITY_AUDIT_LOG" or category == "LEGAL_HOLD_RECORD":
        return "PRESENT"
    if category == "ACCOUNT_TOMBSTONE":
        return "REDACTED" if not pii_present(obj) else "PRESENT"
    if "NOT_FOUND" in joined or "NOT FOUND" in joined or "404" in joined or "ABSENT" in joined:
        return "ABSENT"
    if "ANONYMIZED" in joined or "ANONYMIZED" in joined:
        return "ANONYMIZED"
    if "REDACTED" in joined:
        return "REDACTED"
    if category in ("ANALYTICS_PROFILE", "PRODUCT_TELEMETRY"):
        return "PRESENT" if pii_present(obj) else "ANONYMIZED"
    if category == "USER_PROFILE" and isinstance(obj, dict):
        if str(obj.get("account_status", "")).upper() == "DELETED" and not pii_present(obj):
            return "ABSENT"
    return "PRESENT"

def read_evidence_index():
    rows = read_csv("evidence_files.csv")
    return {r["file_path"].replace("\\", "/"): r for r in rows}

def matches_identity(text, identity):
    if not identity:
        return False
    low = str(text).lower()
    email_values = []
    for key in ("email", "historical_emails"):
        value = identity.get(key)
        if isinstance(value, str):
            email_values.append(value.strip())
        elif isinstance(value, (list, set, tuple)):
            email_values.extend(str(v).strip() for v in value)
    email_hash = (identity.get("email_hash") or "").strip().lower()
    user_id = (identity.get("user_id") or "").strip()
    phone_values = []
    for key in ("phone", "historical_phones"):
        value = identity.get(key)
        if isinstance(value, str):
            phone_values.append(normalize_phone(value))
        elif isinstance(value, (list, set, tuple)):
            phone_values.extend(normalize_phone(v) for v in value)
    for email in email_values:
        if email and email.lower() in low:
            return True
    if email_hash and email_hash in low:
        return True
    if user_id and re.search(r"(?<![A-Za-z0-9_])" + re.escape(user_id) + r"(?![A-Za-z0-9_])", str(text), re.I):
        return True
    for phone in phone_values:
        if len(phone) >= 8 and phone in re.sub(r"\D", "", str(text)):
            return True
    return False

_ALL_EVIDENCE_RECORDS = None

def load_all_evidence(evidence_index):
    """Parse the evidence corpus once; matching each case against it is then inexpensive."""
    all_records = []
    evidence_root = DATASET / "evidence"
    for rel, meta in evidence_index.items():
        path = evidence_root / rel.removeprefix("evidence/")
        if not path.exists():
            continue
        captured = parse_time(meta.get("captured_at"))
        evidence_id = meta.get("file_id", "")
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        suffix = path.suffix.lower()
        if suffix == ".json":
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = None
            if data is not None:
                def walk(node, context=None):
                    context = dict(context or {})
                    if isinstance(node, dict):
                        for key in ("data_store", "system", "service", "collection", "record_type"):
                            if node.get(key):
                                context[key] = node[key]
                        resource = node.get("resource_id") or node.get("resource") or node.get("id")
                        if resource:
                            blob = json.dumps(node, ensure_ascii=False)
                            ts = next((node.get(k) for k in (
                                "observed_at", "captured_at", "recorded_at", "event_time",
                                "created_at", "updated_at", "timestamp"
                            ) if node.get(k)), None)
                            rt = parse_time(ts) or captured
                            cat = category_for(context.get("data_store") or context.get("system") or context.get("service"),
                                               context.get("collection"), str(resource), context.get("record_type"))
                            all_records.append({
                                "evidence_id": evidence_id, "resource_id": str(resource),
                                "system_id": system_for(context.get("data_store") or context.get("system") or context.get("service"), cat),
                                "category": cat, "state": state_for(cat, node, blob),
                                "observed_at": rt, "object": node, "text": blob,
                            })
                        for v in node.values():
                            walk(v, context)
                    elif isinstance(node, list):
                        for v in node:
                            walk(v, context)
                walk(data)
            continue
        # Keep only lines containing an explicit resource identifier.
        for line in raw.splitlines():
            rid_match = re.search(r"\b(resource_id|resource|target_resource|record_id)\s*[=:]\s*[\"']?([A-Za-z][A-Za-z0-9_-]+)", line, re.I)
            if not rid_match:
                rid_match = re.search(r"\b(account|search|analytics|support|export|backup|data_flow|tombstone|audit_record|cache|telemetry)_\d+\b", line, re.I)
                rid = rid_match.group(0) if rid_match else None
            else:
                rid = rid_match.group(2)
            if not rid:
                continue
            ts_match = re.search(r"\d{4}-\d\d-\d\d[T ]\d\d:\d\d:\d\d(?:\.\d+)?Z?", line)
            ts = parse_time(ts_match.group(0)) if ts_match else captured
            sysm = re.search(r"\b(service|system|target_system|data_store)\s*[=:]\s*[\"']?([A-Za-z][A-Za-z0-9_-]+)", line, re.I)
            sys = sysm.group(2) if sysm else ""
            cat = category_for(sys, "", rid, "")
            all_records.append({
                "evidence_id": evidence_id, "resource_id": rid,
                "system_id": system_for(sys, cat), "category": cat,
                "state": state_for(cat, {}, line), "observed_at": ts,
                "object": {}, "text": line,
            })
    return all_records

def evidence_records(identity, audit_at, evidence_index):
    global _ALL_EVIDENCE_RECORDS
    if _ALL_EVIDENCE_RECORDS is None:
        _ALL_EVIDENCE_RECORDS = load_all_evidence(evidence_index)
    audit_time = parse_time(audit_at)
    found = []
    for rec in _ALL_EVIDENCE_RECORDS:
        rt = rec.get("observed_at")
        if audit_time and rt and rt > audit_time:
            continue
        blob = rec.get("text", "")
        if not matches_identity(blob, identity):
            continue
        found.append(rec)
    dedup = {}
    for rec in found:
        key = (rec["evidence_id"], rec["resource_id"], rec["state"], rec["system_id"])
        if key not in dedup:
            dedup[key] = rec
        elif rec.get("observed_at") and (
            not dedup[key].get("observed_at") or rec["observed_at"] > dedup[key]["observed_at"]
        ):
            dedup[key] = rec
    return list(dedup.values())

def rule_action(category, rec):
    obj = rec.get("object") or {}
    text = (rec.get("text") or "").lower()
    if category in ("USER_PROFILE", "SECONDARY_IDENTIFIER", "SEARCH_INDEX_ENTRY",
                    "CACHE_ENTRY", "SUPPORT_ATTACHMENT", "USER_EXPORT", "MARKETING_PROFILE"):
        return "DELETE"
    if category == "SUPPORT_MESSAGE":
        return "REDACT"
    if category in ("ANALYTICS_PROFILE", "PRODUCT_TELEMETRY"):
        return "ANONYMIZE" if rec["state"] == "PRESENT" else "KEEP"
    if category == "EMAIL_DELIVERY_LOG":
        return "REDACT"
    if category in ("SECURITY_AUDIT_LOG", "LEGAL_HOLD_RECORD"):
        return "RETAIN"
    if category == "BACKUP_ARCHIVE":
        return "BLOCK_RESTORE"
    if category == "ACCOUNT_TOMBSTONE":
        return "REDACT" if rec["state"] == "PRESENT" else "KEEP"
    if category == "DATA_FLOW":
        return "DISABLE" if rec["state"] == "ACTIVE" else "KEEP"
    return "DELETE" if rec["state"] == "PRESENT" else "KEEP"

def case_sort_key(case_id):
    if not isinstance(case_id, str):
        return (0, 0)
    digits = re.search(r"(\d+)$", case_id)
    if digits:
        return (0, int(digits.group(1)))
    return (1, case_id)


def step(phase, system, resource, operation, state, evidence):
    return {
        "phase": phase, "system_id": system, "resource_id": resource,
        "operation": operation, "state": state, "evidence_id": evidence or "",
    }

def build_case(case, identity, evidence_index):
    text = (case.get("request_text") or "").lower()
    # Explicit non-deletion requests are NOT_APPLICABLE even if they mention an account.
    no_delete_intent = any(phrase in text for phrase in (
        "do not close", "don't close", "leave the account active", "leave my account active",
        "leave my profile", "without removing", "keep the account as it is",
        "continue using the service", "please keep the account", "not requesting deletion",
        "do not delete", "don't delete", "no deletion"
    ))
    if no_delete_intent:
        return "NOT_APPLICABLE", []
    # The dataset includes English, Portuguese, Spanish, French, Korean, and Japanese requests.
    requested = any(w in text for w in (
        "delet", "eras", "remove", "close my account", "close this account",
        "personal-data", "right to be forgotten", "exclus", "eliminaci",
        "suppression", "삭제", "削除", "消去"
    ))
    if not requested:
        return "NOT_APPLICABLE", []

    recs = evidence_records(identity, case.get("audit_at"), evidence_index)
    # Keep only the latest observation per system/resource. This avoids stale snapshots
    # overriding a later state while preserving independent evidence resources.
    latest = {}
    for rec in recs:
        key = (rec["system_id"], rec["resource_id"])
        prev = latest.get(key)
        if prev is None or (rec.get("observed_at") or datetime.min.replace(tzinfo=timezone.utc)) >= (
            prev.get("observed_at") or datetime.min.replace(tzinfo=timezone.utc)
        ):
            latest[key] = rec
    recs = list(latest.values())

    findings, remedies, verifications = [], [], []
    needs_work = False
    for rec in recs:
        cat, state = rec["category"], rec["state"]
        action = rule_action(cat, rec)
        rid, sys, ev = rec["resource_id"], rec["system_id"], rec["evidence_id"]

        if action == "KEEP":
            if cat in ("ANALYTICS_PROFILE", "PRODUCT_TELEMETRY") and state == "ANONYMIZED":
                verifications.append(step("VERIFICATION", sys, rid, "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED", ev))
            elif cat == "ACCOUNT_TOMBSTONE" and state == "REDACTED":
                verifications.append(step("VERIFICATION", sys, rid, "VERIFY_RECORD_REDACTED", "REDACTED", ev))
            continue
        if action == "RETAIN":
            verifications.append(step("VERIFICATION", sys, rid, "VERIFY_RECORD_PRESENT", "PRESENT", ev))
            continue
        if action == "BLOCK_RESTORE":
            if state != "BLOCKED":
                findings.append(step("FINDING", sys, rid, "REPORT_RESTORE_RISK", "ACTIVE", ev))
                remedies.append(step("REMEDIATION", sys, rid, "BLOCK_RESTORE", "BLOCKED", ""))
                verifications.append(step("VERIFICATION", sys, rid, "VERIFY_RESTORE_BLOCKED", "BLOCKED", ""))
                needs_work = True
            else:
                verifications.append(step("VERIFICATION", sys, rid, "VERIFY_RESTORE_BLOCKED", "BLOCKED", ev))
            continue
        if action == "DISABLE":
            if state != "DISABLED":
                findings.append(step("FINDING", sys, rid, "REPORT_ACTIVE_DATA_FLOW", "ACTIVE", ev))
                remedies.append(step("REMEDIATION", sys, rid, "DISABLE_DATA_FLOW", "DISABLED", ""))
                verifications.append(step("VERIFICATION", sys, rid, "VERIFY_DATA_FLOW_DISABLED", "DISABLED", ""))
                needs_work = True
            else:
                verifications.append(step("VERIFICATION", sys, rid, "VERIFY_DATA_FLOW_DISABLED", "DISABLED", ev))
            continue
        if action == "DELETE":
            if state != "ABSENT":
                op = "REPORT_REMAINING_RECORD"
                findings.append(step("FINDING", sys, rid, op, "PRESENT", ev))
                remedies.append(step("REMEDIATION", sys, rid, "DELETE_RECORD", "ABSENT", ""))
                verifications.append(step("VERIFICATION", sys, rid, "VERIFY_RECORD_ABSENT", "ABSENT", ""))
                needs_work = True
            else:
                verifications.append(step("VERIFICATION", sys, rid, "VERIFY_RECORD_ABSENT", "ABSENT", ev))
            continue
        if action == "REDACT":
            if state != "REDACTED":
                findings.append(step("FINDING", sys, rid, "REPORT_EXPOSED_PII", "PRESENT", ev))
                remedies.append(step("REMEDIATION", sys, rid, "REDACT_RECORD", "REDACTED", ""))
                verifications.append(step("VERIFICATION", sys, rid, "VERIFY_RECORD_REDACTED", "REDACTED", ""))
                needs_work = True
            else:
                verifications.append(step("VERIFICATION", sys, rid, "VERIFY_RECORD_REDACTED", "REDACTED", ev))
            continue
        if action == "ANONYMIZE":
            if state != "ANONYMIZED":
                findings.append(step("FINDING", sys, rid, "REPORT_EXPOSED_PII", "PRESENT", ev))
                remedies.append(step("REMEDIATION", sys, rid, "ANONYMIZE_RECORD", "ANONYMIZED", ""))
                verifications.append(step("VERIFICATION", sys, rid, "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED", ""))
                needs_work = True
            else:
                verifications.append(step("VERIFICATION", sys, rid, "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED", ev))

    # No evidence is not proof of deletion. Keep the result conservative.
    if not recs:
        return "INCOMPLETE", []

    # Required phase ordering; sort within phase by operation then system/resource.
    findings.sort(key=lambda s: (FINDING_ORDER.get(s["operation"], 99), s["system_id"], s["resource_id"]))
    remedies.sort(key=lambda s: (REMEDIATION_ORDER.get(s["operation"], 99), s["system_id"], s["resource_id"]))
    verifications.sort(key=lambda s: (VERIFICATION_ORDER.get(s["operation"], 99), s["system_id"], s["resource_id"]))

    steps = findings + remedies + verifications
    for i, item in enumerate(steps, start=1):
        item["step_no"] = i
    # Emit keys in the challenge's canonical field order.
    steps = [{
        "step_no": x["step_no"], "phase": x["phase"], "system_id": x["system_id"],
        "resource_id": x["resource_id"], "operation": x["operation"],
        "state": x["state"], "evidence_id": x["evidence_id"]
    } for x in steps]

    # A case is complete only if all discovered relevant resources were compliant
    # and every emitted verification is backed by evidence.
    # A retained audit record alone is insufficient to prove deletion completion.
    account_absence_proven = any(
        x["operation"] == "VERIFY_RECORD_ABSENT"
        and x["system_id"] == "account_service"
        and x["evidence_id"]
        for x in verifications
    )
    complete = account_absence_proven and bool(verifications) and not needs_work and not findings and not remedies and all(
        x["evidence_id"] for x in verifications
    )
    return ("COMPLETE" if complete else "INCOMPLETE"), steps

def main():
    cases = read_csv("deletion_requests.csv")
    identities = read_csv("user_identities.csv")
    audit_log = read_csv("user_audit_log.csv")
    evidence_index = read_evidence_index()

    rows = []
    for case in cases:
        identity = resolve_case_identity(case, identities, audit_log)
        status, steps = build_case(case, identity, evidence_index)
        rows.append({
            "case_id": case["case_id"],
            "deletion_status": status,
            "steps_json": json.dumps(steps, separators=(",", ":"), ensure_ascii=False),
        })

    rows.sort(key=lambda row: case_sort_key(row["case_id"]))
    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "deletion_status", "steps_json"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Processed {len(rows)} cases.")
    print(f"Output written to: {OUTPUT}")

if __name__ == "__main__":
    main()
