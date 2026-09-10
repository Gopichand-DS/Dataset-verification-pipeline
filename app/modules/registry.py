
from __future__ import annotations

from .schemas import MODULE_FIELDS, IDENTITY_FIELDS
from .evaluators import build_domain_factors


def module_fields(module: str) -> list[str]:
    return MODULE_FIELDS.get(module, [])


def identity_fields(module: str) -> tuple[str, ...]:
    return IDENTITY_FIELDS.get(module, ("name", "official_url"))


def evaluate(module: str, data: dict, evidence: list[dict]) -> dict[str, float]:
    return build_domain_factors(module, data, evidence)
