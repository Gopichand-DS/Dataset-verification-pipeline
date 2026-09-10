from app.discovery.tool_enrichment import _cross_field_duplicate, _features, _pros_cons


def test_cross_field_duplicate_detects_rephrased_copy():
    assert _cross_field_duplicate("AI image generation and editing", "Generate and edit images using AI", 0.70)


def test_features_are_field_specific():
    text = "Features: Image generation • Background removal • Upscaling. Benefits: Fast workflow for creators. Limitations: Export requires a paid plan."
    features = _features(text)
    assert any("Image generation" in x for x in features)
    assert not any("paid plan" in x.lower() for x in features)


def test_pros_cons_do_not_use_generic_description():
    pages = {"home": {"text": "Features: Image generation. Benefits: Fast workflow for creators. Limitations: Export requires a paid plan."}}
    pros, cons = _pros_cons({}, pages, {"has_free": False, "has_paid": True, "amounts": ["$10/month"]}, {"account_required": "not publicly established"})
    assert any("Fast workflow" in x for x in pros)
    assert any("paid pricing" in x.lower() or "paid plan" in x.lower() for x in cons)
    assert not any(x.lower() == "image generation" for x in pros + cons)
