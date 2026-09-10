
from __future__ import annotations

from typing import Any

# Domain-aware, still conservative. Values are evidence requirements rather
# than claims about the candidate.
REQUIRED_EVIDENCE = {
    "tools": {
        "capability": ["description", "use_case"],
        "usefulness": ["description", "use_case"],
        "documentation": ["official_url", "api"],
        "differentiation": ["description"],
    },
    "companies": {
        "capability": ["description", "ai_category"],
        "usefulness": ["description", "products"],
        "documentation": ["official_url"],
        "differentiation": ["description", "ai_category"],
    },
    "agents": {
        "capability": ["description", "use_case", "integrations"],
        "usefulness": ["use_case"],
        "documentation": ["official_url", "api"],
        "differentiation": ["description", "integrations"],
    },
    "mcp": {
        "capability": ["description", "capabilities"],
        "usefulness": ["use_case", "integrations"],
        "documentation": ["official_url", "github"],
        "differentiation": ["capabilities"],
    },
    "robots": {
        "capability": ["description", "capabilities"],
        "usefulness": ["use_cases"],
        "documentation": ["official_url", "sensors"],
        "differentiation": ["capabilities"],
    },
    "devices": {
        "capability": ["description", "ai_capability", "features"],
        "usefulness": ["use_case"],
        "documentation": ["official_url", "model"],
        "differentiation": ["ai_capability", "features"],
    },
    "models": {
        "capability": ["name", "family", "modalities"],
        "usefulness": ["description", "use_case"],
        "documentation": ["official_url", "repository", "license"],
        "differentiation": ["family", "modalities"],
    },
    "news": {
        "capability": ["title", "description"],
        "usefulness": ["company", "topic"],
        "documentation": ["url", "source"],
        "differentiation": ["event_type", "entities"],
    },
}


def _present(data: dict[str, Any], fields: list[str]) -> bool:
    return any(str(data.get(field, "")).strip() for field in fields)


def build_domain_factors(module: str, data: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, float]:
    rules = REQUIRED_EVIDENCE.get(module, {})
    evidence_fields = {e.get("field") for e in evidence if e.get("confidence", 0) > 0}

    def supported(factor: str) -> float:
        fields = rules.get(factor, [])
        if not fields:
            return 0.0
        observed = sum(1 for f in fields if f in evidence_fields or _present(data, [f]))
        return min(1.0, observed / len(fields))

    # Conservative defaults: adoption/activity are never inferred from a
    # directory listing. They remain zero until a real signal is supplied.
    return {
        "capability": supported("capability"),
        "usefulness": supported("usefulness"),
        "adoption": 0.0,
        "activity": 0.0,
        "technical": supported("documentation"),
        "documentation": supported("documentation"),
        "differentiation": supported("differentiation"),
        "verifiability": 1.0 if evidence_fields else 0.0,
    }
