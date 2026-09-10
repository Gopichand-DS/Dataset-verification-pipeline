from app.modules.schemas import ensure_module_schema, module_columns
from app.discovery.tool_enrichment import canonical_tool_id


def test_tools_schema_contains_requested_and_audit_fields():
    fields = set(module_columns("tools", [{"custom_1000": "x"}]))
    required = {
        "canonical_id", "slug", "name", "logoUrl", "description", "official_url",
        "features", "pros", "cons", "releaseDate", "pricingModel", "pricingAmount",
        "billingFrequency", "isOpenSource", "compatibility", "targetUsers", "hasApi",
        "apiDocsUrl", "performanceScore", "useCases", "toolCategories", "launchDate",
        "recentlyUpdated", "lastVerifiedAt", "logoVerification", "websiteVerification",
        "categoryCount", "companyVerification", "pricingTiers", "accountAccess", "custom_1000"
    }
    assert required.issubset(fields)


def test_canonical_id_is_stable():
    assert canonical_tool_id("Example Tool", "https://www.example.com/") == canonical_tool_id("Example Tool", "https://example.com")
