from __future__ import annotations

from typing import Any

MODULE_FIELDS = {
    "tools": [
        "name", "official_url", "description", "category", "pricing",
        "platform", "use_case", "api", "open_source", "company",
        "canonical_id", "accountAccess", "pricingEvidence", "crawledOfficialPages",
        "officialLinks", "officialSourceText", "releasedBy", "launchDate", "releaseDate",
        "logoUrl", "githubUrl", "linkedInUrl", "twitterUrl", "apiDocsUrl",
        "slug", "features", "pros", "cons", "pricingModel", "pricingAmount",
        "billingFrequency", "pricingTiers", "accountAccess", "compatibility",
        "isOpenSource",
        "targetUsers", "hasApi", "performanceScore", "useCases",
        "toolCategories", "recentlyUpdated", "lastVerifiedAt", "logoVerification",
        "websiteVerification", "categoryCount", "companyVerification"
    ],
    "companies": [
        "name", "official_url", "description", "country", "city", "founded",
        "ai_category", "classification", "sector", "employees", "funding",
        "latest_round", "valuation", "investors", "products"
    ],
    "agents": [
        "name", "official_url", "description", "category", "company",
        "launch", "updated", "pricing", "platform", "api", "open_source",
        "models", "integrations", "use_case", "status"
    ],
    "mcp": [
        "name", "official_url", "github", "description", "category",
        "company", "status", "use_case", "capabilities", "integrations",
        "platforms", "pricing", "open_source", "license"
    ],
    "robots": [
        "name", "official_url", "manufacturer", "type", "category",
        "description", "release", "status", "capabilities", "use_cases",
        "autonomy", "navigation", "manipulation", "sensors", "payload",
        "battery", "speed", "commercial_availability", "price"
    ],
    "devices": [
        "name", "official_url", "manufacturer", "category", "description",
        "release", "status", "ai_capability", "use_case", "features",
        "model", "technology", "connectivity", "platform", "os", "price",
        "regions"
    ],
    "models": [
        "name", "official_url", "provider", "family", "release", "updated",
        "reasoning", "tool_calling", "structured_output", "context",
        "modalities", "open_weights", "license", "benchmarks", "api",
        "pricing", "repository", "base_model"
    ],
    "news": [
        "title", "url", "source", "published_at", "description", "company",
        "entities", "event_type", "impact", "topic"
    ],
}

# Canonical primary categories for AI tools. Classification is conservative:
# if the available text does not support a category, the record stays unclassified.
TOOL_CATEGORIES = [
    "News", "Media", "Chatbots", "Search", "Research", "Writing", "Coding",
    "Developer Tools", "Image", "Video", "Audio & Music", "Design",
    "Presentations", "Productivity", "Automation", "Agents", "Data & Analytics",
    "Marketing", "Sales", "Customer Support", "Education", "Finance", "Legal",
    "Healthcare", "Security", "Translation", "3D", "Social Media", "E-commerce",
    "Human Resources", "Other/Unclassified",
]

TOOL_CATEGORY_RULES = {
    "News": ("news", "journalism", "headline", "breaking news", "newsroom", "news article"),
    "Media": ("media", "publisher", "publishing", "content media"),
    "Chatbots": ("chatbot", "chat bot", "conversational ai", "virtual assistant", "ai assistant"),
    "Search": ("search engine", "web search", "search the web", "semantic search"),
    "Research": ("research assistant", "literature review", "academic research", "research papers", "deep research"),
    "Writing": ("writing assistant", "copywriting", "rewrite", "grammar", "essay writer", "content writer"),
    "Coding": ("code generation", "coding assistant", "developer assistant", "programming assistant", "code review", "software development"),
    "Developer Tools": ("sdk", "api development", "developer tool", "developer platform", "observability", "deployment"),
    "Image": ("image generation", "image generator", "ai image", "photo editing", "image editor", "text to image"),
    "Video": ("video generation", "video editor", "text to video", "ai video", "video creation"),
    "Audio & Music": ("music generation", "music generator", "voice generation", "speech to text", "text to speech", "audio"),
    "Design": ("design tool", "graphic design", "ui design", "ux design", "logo generator"),
    "Presentations": ("presentation", "slide deck", "slides", "pitch deck"),
    "Productivity": ("productivity", "meeting notes", "note taking", "calendar", "task management"),
    "Automation": ("workflow automation", "automate", "automation platform", "no-code automation"),
    "Agents": ("ai agent", "agentic", "autonomous agent", "multi-agent"),
    "Data & Analytics": ("data analysis", "analytics", "business intelligence", "data visualization", "sql assistant"),
    "Marketing": ("marketing", "seo", "advertising", "ad copy", "campaign"),
    "Sales": ("sales", "lead generation", "sales prospecting", "crm assistant"),
    "Customer Support": ("customer support", "helpdesk", "support agent", "customer service"),
    "Education": ("education", "tutor", "teaching", "learning", "homework"),
    "Finance": ("finance", "financial", "accounting", "investment", "trading"),
    "Legal": ("legal", "law", "contract review", "legal assistant"),
    "Healthcare": ("healthcare", "medical", "clinical", "diagnosis", "patient"),
    "Security": ("cybersecurity", "security", "threat detection", "fraud detection"),
    "Translation": ("translation", "translator", "localization"),
    "3D": ("3d", "3d model", "3d generation", "three dimensional"),
    "Social Media": ("social media", "instagram", "tiktok", "social post", "social content"),
    "E-commerce": ("e-commerce", "ecommerce", "shopping", "product recommendation", "retail"),
    "Human Resources": ("human resources", "recruiting", "recruitment", "resume screening", "hr"),
}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(_text(x) for x in value)
    if isinstance(value, dict):
        return " ".join(f"{k} {_text(v)}" for k, v in value.items())
    return str(value)


def classify_tool_category(record: dict[str, Any]) -> tuple[str, list[str]]:
    """Return a conservative primary category and all supported categories."""
    explicit = _text(record.get("category"))
    text = " ".join(
        _text(record.get(k)) for k in
        ("name", "description", "use_case", "category", "subcategory", "tags", "keywords")
    ).lower()
    if not text.strip():
        return "Other/Unclassified", []

    scores: dict[str, int] = {}
    for category, terms in TOOL_CATEGORY_RULES.items():
        score = 0
        for term in terms:
            if term in text:
                score += 2 if term in explicit.lower() else 1
        if score:
            scores[category] = score

    if not scores:
        return "Other/Unclassified", []
    ordered = sorted(scores, key=lambda c: (-scores[c], TOOL_CATEGORIES.index(c)))
    return ordered[0], ordered[:5]


def ensure_module_schema(record: dict[str, Any], module: str) -> dict[str, Any]:
    """Preserve every incoming column while adding the canonical module fields.

    No incoming column is discarded. Missing canonical fields are added as blank
    values so every record conforms to one stable column contract.
    """
    row = dict(record)
    for field in MODULE_FIELDS.get(module, []):
        row.setdefault(field, "")
    if module == "tools":
        primary, categories = classify_tool_category(row)
        row.setdefault("aiorbit_category", primary)
        row.setdefault("aiorbit_categories", categories)
        row.setdefault("category_confidence", "text_match" if categories else "unclassified")
    return row


def module_columns(module: str, records: list[dict[str, Any]] | None = None) -> list[str]:
    """Stable canonical columns followed by every observed input/source column."""
    base = list(MODULE_FIELDS.get(module, []))
    if module == "tools":
        base.extend(["aiorbit_category", "aiorbit_categories", "category_confidence"])
    extras = sorted({k for r in (records or []) for k in r.keys()} - set(base))
    return base + extras


IDENTITY_FIELDS = {
    "tools": ("name", "official_url", "company"),
    "companies": ("name", "official_url"),
    "agents": ("name", "official_url", "company"),
    "mcp": ("name", "official_url", "github", "company"),
    "robots": ("name", "official_url", "manufacturer"),
    "devices": ("name", "official_url", "manufacturer", "model"),
    "models": ("name", "official_url", "provider", "family", "repository"),
    "news": ("title", "url", "source", "published_at"),
}
