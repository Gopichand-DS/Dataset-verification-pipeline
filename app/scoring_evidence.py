
from __future__ import annotations

from typing import Any

WEIGHTS = {
    "capability": 30,
    "usefulness": 20,
    "adoption": 15,
    "activity": 10,
    "technical": 5,
    "documentation": 5,
    "differentiation": 5,
    "verifiability": 10,
}


def _pct(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def score_with_evidence(factors: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    evidence_by_field = {}
    for item in evidence or []:
        evidence_by_field.setdefault(item.get("field"), []).append(item)

    factor_scores = {}
    weighted_total = 0.0
    max_total = sum(WEIGHTS.values())

    for factor, weight in WEIGHTS.items():
        raw = _pct(factors.get(factor, 0))

        if factor == "verifiability":
            support = _pct(factors.get("verifiability", 0))
        else:
            related = evidence_by_field.get(factor, [])
            support = max(
                (_pct(item.get("confidence")) for item in related),
                default=0.0,
            )

        effective = raw * support
        points = effective * weight
        factor_scores[factor] = {
            "raw": round(raw, 4),
            "evidence_support": round(support, 4),
            "weight": weight,
            "points": round(points, 3),
        }
        weighted_total += points

    overall = round(weighted_total / max_total * 100, 2) if max_total else 0.0
    return {
        "overall": overall,
        "factor_scores": factor_scores,
        "evidence_count": len(evidence or []),
        "decision": (
            "curate" if overall >= 70
            else "review" if overall >= 60
            else "reject"
        ),
    }
