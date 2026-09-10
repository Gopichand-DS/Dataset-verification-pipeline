
from app.scoring_evidence import score_with_evidence


def test_unsupported_claims_do_not_get_full_credit():
    factors = {
        "capability": 1,
        "usefulness": 1,
        "adoption": 1,
        "activity": 1,
        "technical": 1,
        "documentation": 1,
        "differentiation": 1,
        "verifiability": 1,
    }
    result = score_with_evidence(factors, [])
    assert result["overall"] == 10.0


def test_supported_capability_gets_credit():
    factors = {"capability": 1, "verifiability": 1}
    evidence = [{"field": "capability", "confidence": 1.0}]
    result = score_with_evidence(factors, evidence)
    assert result["factor_scores"]["capability"]["points"] == 30.0
