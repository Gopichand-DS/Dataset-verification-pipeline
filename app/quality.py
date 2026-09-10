def required_verified_fields(module):
    common = ["name", "official_url"]
    specific = {
        "tools": ["company", "description"],
        "companies": ["company"],
        "agents": ["company"],
        "mcp": ["company"],
        "robots": ["company"],
        "devices": ["company"],
        "models": ["company"],
        "news": ["title", "url", "source"],
    }
    return common + specific.get(module, [])

def missing_fields(record, module):
    return [f for f in required_verified_fields(module) if not record.get(f)]
