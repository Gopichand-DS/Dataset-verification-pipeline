from app.modules.schemas import ensure_module_schema, module_columns, classify_tool_category


def test_tools_preserve_input_columns_and_add_category():
    row = {
        "name": "Example News AI",
        "official_url": "https://example.com",
        "description": "AI tool for news article summaries",
        "my_original_column": "keep-me",
    }
    out = ensure_module_schema(row, "tools")
    assert out["my_original_column"] == "keep-me"
    assert out["pricing"] == ""
    assert out["aiorbit_category"] == "News"
    assert "News" in out["aiorbit_categories"]


def test_category_examples():
    assert classify_tool_category({"name": "Chat Helper", "description": "conversational AI chatbot"})[0] == "Chatbots"
    assert classify_tool_category({"name": "News Writer", "description": "newsroom article generation"})[0] == "News"
    assert classify_tool_category({"name": "Video Maker", "description": "text to video generation"})[0] == "Video"


def test_master_columns_are_union_of_schema_and_source_columns():
    rows = [
        ensure_module_schema({"name": "A", "official_url": "https://a.example", "column_a": "1"}, "tools"),
        ensure_module_schema({"name": "B", "official_url": "https://b.example", "column_b": "2"}, "tools"),
    ]
    cols = module_columns("tools", rows)
    assert "column_a" in cols and "column_b" in cols
    assert "description" in cols and "aiorbit_category" in cols
