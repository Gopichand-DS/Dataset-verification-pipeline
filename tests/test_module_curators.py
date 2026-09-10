
from app.modules.registry import module_fields, identity_fields, evaluate


def test_all_modules_have_fields():
    for module in ("tools", "companies", "agents", "mcp", "robots", "devices", "models", "news"):
        assert module_fields(module)
        assert identity_fields(module)


def test_agents_require_real_agentic_evidence():
    factors = evaluate(
        "agents",
        {"name": "Example", "description": "An agent", "use_case": "research"},
        []
    )
    assert factors["verifiability"] == 0.0


def test_models_have_model_specific_schema():
    assert "open_weights" in module_fields("models")
    assert "base_model" in module_fields("models")
