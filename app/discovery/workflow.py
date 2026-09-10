from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from hashlib import sha256

import pandas as pd

from app.discovery.engine import DiscoveryEngine
from app.discovery.verification_cache import VerificationCache
from app.discovery.verification_gate import verify_official_url
from app.discovery.field_verification import verify_ingested_fields
from app.discovery.acceptance import acceptance_report
from app.modules.schemas import ensure_module_schema
from app.monitoring.metrics import PipelineMetrics
from app.normalize import canonical_key, normalize_url
from app.discovery.tool_enrichment import enrich_tool


def read_input_records(path: str | Path) -> list[dict[str, Any]]:
    """Read a dataset without dropping any source columns."""
    p = Path(path)
    if p.suffix.lower() == ".csv":
        df = pd.read_csv(p, dtype=object)
    elif p.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(p, dtype=object)
    elif p.suffix.lower() == ".json":
        payload = json.loads(p.read_text(encoding="utf-8"))
        rows = payload if isinstance(payload, list) else payload.get("records", [])
        df = pd.DataFrame(rows)
    else:
        raise ValueError("Supported input formats: CSV, XLSX, JSON")
    return df.fillna("").to_dict("records")


class DiscoveryWorkflow:
    """Quality-first discovery/verification workflow.

    A workflow can start from live discovery sources or from an existing dataset.
    In both cases every incoming field is preserved, canonical module fields are
    added when absent, and candidates are independently checked against their
    official URL before acceptance.
    """

    def __init__(self, cache=None):
        self.discovery = DiscoveryEngine()
        self.cache = cache or VerificationCache()

    def _verify_candidate(self, candidate: dict[str, Any]) -> dict[str, Any]:
        url = candidate.get("official_url", "")
        cached = self.cache.get(url) if url else None
        if cached is None:
            result = verify_official_url(url)
            evidence = result.to_dict()
            if url:
                self.cache.put(url, evidence)
        else:
            evidence = cached

        candidate["verification_evidence"] = evidence
        page_ok = evidence.get("status") == "verified"
        # The dataset itself is NEVER treated as proof. Every non-empty input
        # field is checked against independently fetched official-page evidence.
        page = {
            "final_url": evidence.get("final_url") or url,
            "source_url": evidence.get("url") or url,
            "title": evidence.get("title", ""),
            "description": evidence.get("description", ""),
            "text": evidence.get("text", ""),
            "links": evidence.get("links", []),
            "status_code": evidence.get("http_status"),
        }
        field_verification = verify_ingested_fields(candidate, page) if page_ok else {
            "checked_at": evidence.get("checked_at", ""),
            "source_url": url,
            "identity": {"status": "unverified", "confidence": 0.0, "evidence": "Official page was not independently accessible."},
            "official_category": {"primary": "Other/Unclassified", "categories": [], "confidence": 0.0, "source": url, "method": "not_available"},
            "input_category_check": {"status": "unsupported", "value": candidate.get("toolCategories", candidate.get("category", "")), "confidence": 0.0, "source_url": url, "evidence": "Official page unavailable."},
            "fields": {k: {"status": "unsupported", "value": v, "confidence": 0.0, "source_url": url, "evidence": "Official page unavailable."} for k, v in candidate.items() if v not in (None, "", [], {}) and not k.startswith("aiorbit_")},
            "summary": {},
            "all_non_empty_fields_checked": False,
        }
        candidate["field_verification"] = field_verification
        candidate["verification_status"] = (
            "verified" if page_ok and field_verification.get("identity", {}).get("status") == "verified" else "unverified"
        )
        candidate["verification_scope"] = "official_page_plus_field_level_claim_checks"
        candidate["verified_at"] = evidence.get("checked_at", "")

        if candidate.get("module") == "tools" or "toolCategories" in candidate or "aiorbit_category" in candidate:
            official_category = field_verification.get("official_category", {})
            candidate["aiorbit_category"] = official_category.get("primary", "Other/Unclassified")
            candidate["aiorbit_categories"] = official_category.get("categories", [])
            candidate["category_confidence"] = official_category.get("confidence", 0.0)
            candidate["category_source"] = "official_page"
        return candidate

    def _prepare(self, records: list[dict[str, Any]], module: str, source_name: str) -> list[dict[str, Any]]:
        prepared = []
        seen = {}
        skipped = []
        for raw in records:
            raw = dict(raw)
            # Normalize common dataset header variants BEFORE the identity gate.
            # The original columns are still preserved; canonical fields are aliases,
            # not replacements. This prevents valid datasets such as toolName/site/homepage
            # from being classified as "missing identity".
            aliases = {
                "name": ("name", "title", "tool_name", "toolName", "tool", "product_name", "productName", "appName", "app_name"),
                "official_url": ("official_url", "websiteUrl", "website_url", "website", "url", "officialUrl", "officialURL", "site", "homepage", "homePage", "productUrl", "product_url", "link"),
                "company": ("company", "company_name", "companyName", "vendor", "provider", "publisher", "organization"),
            }
            canonical = dict(raw)
            for target, keys in aliases.items():
                if not canonical.get(target):
                    for key in keys:
                        value = raw.get(key)
                        if value not in (None, "", [], {}):
                            canonical[target] = value
                            break
            candidate = ensure_module_schema(canonical, module)
            candidate["module"] = module
            name = candidate.get("name") or candidate.get("title") or candidate.get("tool_name")
            url = candidate.get("official_url") or candidate.get("website") or candidate.get("url") or candidate.get("websiteUrl") or ""
            # Rows missing the identity pair are retained in the dataset but are
            # deliberately left unprocessed; they cannot be truthfully verified.
            if not name or not url:
                candidate["record_status"] = "left_unprocessed"
                candidate["verification_status"] = "not_checked_missing_identity"
                candidate["ingest_row_key"] = "row_" + sha256(json.dumps(candidate, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:20]
                candidate["acceptance"] = {"accepted": False, "reasons": ["missing_required:name_or_website"], "warnings": []}
                skipped.append(candidate)
                continue
            if url:
                candidate["official_url"] = normalize_url(str(url))
            candidate["canonical_key"] = canonical_key(
                str(name), candidate.get("official_url") or candidate.get("url"),
                candidate.get("company") or candidate.get("manufacturer") or candidate.get("provider")
            )
            candidate["name"] = str(name)
            # Snapshot the fields that actually came from the input/discovery source.
            # Enrichment fields added later must not be mistaken for user-supplied claims.
            # Snapshot only actual source claims. Canonical fields added by the schema
            # (including category_confidence) are not treated as ingested evidence.
            source_fields = [
                k for k, v in raw.items()
                if v not in (None, "", [], {})
                and k not in {"aiorbit_category", "aiorbit_categories", "category_confidence"}
            ]
            # Also verify canonical identity/product claims that were supplied through
            # a non-canonical header alias.
            for key in ("name", "official_url", "company"):
                if key not in source_fields and candidate.get(key) not in (None, "", [], {}):
                    source_fields.append(key)
            candidate["_input_fields"] = source_fields
            candidate["input_source"] = source_name
            prior = candidate.get("discovery_sources") or []
            if isinstance(prior, str):
                prior = [prior]
            candidate["discovery_sources"] = list(dict.fromkeys([*prior, source_name]))
            k = candidate["canonical_key"]
            if k in seen:
                # Merge source columns and non-empty values before verification.
                old = seen[k]
                for key, value in candidate.items():
                    if value not in (None, "", [], {}):
                        if key in {"discovery_sources", "sources"}:
                            old[key] = list(dict.fromkeys([*(old.get(key) or []), *(value or [])]))
                        elif old.get(key) in (None, "", [], {}):
                            old[key] = value
            else:
                seen[k] = candidate
        return skipped + list(seen.values())

    def run(
        self,
        module: str,
        limit: int = 0,
        include_secondary: bool = True,
        input_records: list[dict[str, Any]] | None = None,
        input_source: str = "input_dataset",
    ):
        metrics = PipelineMetrics(module=module)
        if input_records is None:
            discovered = self.discovery.discover_module(module, include_secondary)
            candidates = discovered.candidates[:limit] if limit else discovered.candidates
            source_health = discovered.sources
        else:
            candidates = self._prepare(input_records, module, input_source)
            candidates = candidates[:limit] if limit else candidates
            source_health = [{
                "name": input_source,
                "url": input_source,
                "status": "dataset_input",
                "candidate_count": len(candidates),
            }]

        metrics.discovered = len(candidates)
        verified = []
        processed = []
        # `ingested` means candidates that have enough identity information to
        # enter independent verification. It must not be confused with accepted.
        metrics.ingested = sum(1 for c in candidates if c.get("record_status") != "left_unprocessed")
        missing_identity_count = sum(1 for c in candidates if c.get("record_status") == "left_unprocessed")
        for candidate in candidates:
            if candidate.get("record_status") == "left_unprocessed":
                processed.append(candidate)
                metrics.rejected += 1
                continue
            # Verify the original candidate BEFORE enrichment. This prevents fields
            # generated by the enrichment stage from being treated as if they were
            # supplied claims that now need to be proved against the same page.
            candidate = self._verify_candidate(candidate)
            if module == "tools" and candidate.get("verification_status") == "verified":
                try:
                    candidate = enrich_tool(candidate)
                except Exception as exc:
                    candidate["enrichment_error"] = str(exc)
            report = acceptance_report(module, candidate)
            candidate["acceptance"] = report
            candidate["record_status"] = "accepted" if report["accepted"] else "rejected"
            # Red = rejected because independent evidence contradicts/fails the
            # identity/URL gate. Yellow/reviewable = valid identity but some
            # non-critical fields are unsupported.
            if report["accepted"]:
                candidate["quality_filter"] = "green"
                verified.append(candidate)
            elif candidate.get("verification_status") == "verified" and "contradicted_input_fields" not in report.get("reasons", []):
                candidate["quality_filter"] = "yellow"
            else:
                candidate["quality_filter"] = "red"
            processed.append(candidate)
            if not report["accepted"]:
                metrics.rejected += 1

        # `verified` measures independent identity verification; `curated`
        # measures records that passed the acceptance gate. These are distinct.
        metrics.verified = sum(1 for c in processed if c.get("verification_status") == "verified")
        metrics.curated = len(verified)
        metrics.source_errors = sum(x.get("status") == "error" for x in source_health)
        metrics.source_blocked = sum(x.get("status") == "blocked_or_rate_limited" for x in source_health)

        return {
            "module": module,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics.to_dict(),
            "source_health": source_health,
            # records contains every processed input so a failed verification is
            # visible instead of silently disappearing. accepted_records is the
            # clean curated subset for downstream publication.
            "records": processed,
            "accepted_records": verified,
            "diagnostics": {
                "missing_identity_count": missing_identity_count,
                "identity_gate_note": "Rows with recognizable name/website aliases are normalized before verification; original source columns remain preserved.",
            },
        }
