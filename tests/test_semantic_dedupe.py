from app.semantic_dedupe import same_event, model_variant_key

def test_same_event():
    assert same_event("OpenAI launches new model", "OpenAI launches a new model")

def test_variant_key():
    assert model_variant_key("Example 70B GGUF") == model_variant_key("Example 70B GPTQ")
