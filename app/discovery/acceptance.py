from __future__ import annotations

from typing import Any

REQUIRED_COMMON = ("name", "official_url")


def _has_value(v: Any) -> bool:
    if v is None: return False
    if isinstance(v, str): return bool(v.strip())
    return True


def acceptance_report(module: str, record: dict[str, Any]) -> dict[str, Any]:
    """Return explicit acceptance/rejection reasons; never invent missing data."""
    reasons = []
    warnings = []

    for field in REQUIRED_COMMON:
        if not _has_value(record.get(field)):
            reasons.append(f"missing_required:{field}")

    if record.get("verification_status") != "verified":
        reasons.append("not_independently_verified")

    fv = record.get("field_verification")
    if fv is not None:
        if fv.get("all_non_empty_fields_checked") is not True:
            reasons.append("field_verification_incomplete")
        if (fv.get("identity") or {}).get("status") != "verified":
            reasons.append("official_identity_not_verified")
        summary = fv.get("summary") or {}
        # A contradiction means the submitted data conflicts with independent
        # evidence and is a hard red/rejection. Unsupported claims are not
        # automatically false; they remain yellow/reviewable.
        if summary.get("contradicted", 0) > 0:
            reasons.append("contradicted_input_fields")
        if summary.get("unsupported", 0) > 0 or summary.get("unverified_external_claim", 0) > 0:
            warnings.append("some_input_fields_not_independently_proven")

    if record.get("dead") is True or str(record.get("status","")).lower() in {
        "dead","shutdown","abandoned","discontinued"
    }:
        reasons.append("inactive_or_dead")

    if not record.get("discovery_sources"):
        warnings.append("no_discovery_provenance")

    return {
        "accepted": not reasons,
        "module": module,
        "reasons": reasons,
        "warnings": warnings,
    }
