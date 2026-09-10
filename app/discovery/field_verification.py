from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from rapidfuzz.fuzz import token_set_ratio

# These fields are normally directory/analytics metadata. They may be useful,
# but the official product site cannot be treated as proof of their values.
EXTERNAL_CLAIM_FIELDS = {
    "views", "avgRating", "reviewCount", "upvoteCount", "alternativeIds",
    "companyId", "createdAt", "updatedAt", "isTrending", "performanceScore",
}

FIELD_ALIASES = {
    "websiteUrl": "official_url",
    "website": "official_url",
    "url": "official_url",
    "tool_name": "name",
    "pricingModel": "pricing",
    "pricingAmount": "pricing_amount",
    "billingFrequency": "billing_frequency",
    "isOpenSource": "open_source",
    "hasApi": "api",
    "apiDocsUrl": "api_docs_url",
    "releasedBy": "company",
    "launchDate": "release_date",
    "releaseDate": "release_date",
    "useCases": "use_cases",
    "toolCategories": "category",
}

BOOLEAN_TERMS = {
    "isOpenSource": ("open source", "open-source", "source available"),
    "hasApi": ("api", "developer api", "api access", "api documentation"),
    "isTrending": (),  # not safely verifiable from an official product page
}

CATEGORY_TERMS = {
    "News": ("news", "journalism", "headlines", "breaking news", "news article"),
    "Media": ("media", "publishing", "publisher", "content media"),
    "Chatbots": ("chatbot", "chat bot", "conversational ai", "virtual assistant", "ai assistant"),
    "Search": ("search engine", "web search", "search the web", "semantic search"),
    "Research": ("research assistant", "literature review", "academic research", "research papers", "deep research"),
    "Writing": ("writing assistant", "copywriting", "rewrite", "grammar", "essay writer", "content writer"),
    "Coding": ("code generation", "coding assistant", "developer assistant", "programming assistant", "code review"),
    "Developer Tools": ("sdk", "api development", "developer tool", "developer platform", "deployment"),
    "Image": ("image generation", "image generator", "ai image", "photo editing", "image editor", "text to image"),
    "Video": ("video generation", "video editor", "text to video", "ai video", "video creation"),
    "Audio & Music": ("music generation", "music generator", "voice generation", "speech to text", "text to speech", "audio"),
    "Design": ("design tool", "graphic design", "ui design", "ux design", "logo generator"),
    "Presentations": ("presentation", "slide deck", "slides", "pitch deck"),
    "Productivity": ("productivity", "meeting notes", "note taking", "calendar", "task management"),
    "Automation": ("workflow automation", "automation platform", "no-code automation"),
    "Agents": ("ai agent", "agentic", "autonomous agent", "multi-agent"),
    "Data & Analytics": ("data analysis", "analytics", "business intelligence", "data visualization", "sql assistant"),
    "Marketing": ("marketing", "seo", "advertising", "ad copy", "campaign"),
    "Sales": ("sales", "lead generation", "sales prospecting", "crm assistant"),
    "Customer Support": ("customer support", "helpdesk", "support agent", "customer service"),
    "Education": ("education", "tutor", "teaching", "learning", "homework"),
    "Finance": ("finance", "financial", "accounting", "investment", "trading"),
    "Legal": ("legal", "law", "contract review", "legal assistant"),
    "Healthcare": ("healthcare", "medical", "clinical", "diagnosis", "patient"),
    "Security": ("cybersecurity", "threat detection", "fraud detection"),
    "Translation": ("translation", "translator", "localization"),
    "3D": ("3d", "3d model", "3d generation"),
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


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", _text(value)).strip()


def _snippet(value: str, corpus: str, radius: int = 220) -> str:
    value = _norm(value)
    if not value:
        return ""
    low = corpus.lower()
    idx = low.find(value.lower())
    if idx < 0:
        return ""
    return corpus[max(0, idx-radius): idx+len(value)+radius]


def _status_for_value(field: str, value: Any, corpus: str, source_url: str, links: list[str]) -> dict[str, Any]:
    value_text = _norm(value)
    if not value_text:
        return {"status": "empty", "value": value, "confidence": 0.0, "source_url": source_url, "evidence": ""}
    if field in EXTERNAL_CLAIM_FIELDS:
        return {"status": "unverified_external_claim", "value": value, "confidence": 0.0, "source_url": source_url, "evidence": "Official product page is not sufficient proof for this directory/analytics field."}
    if field in {"logoUrl", "videoUrl", "linkedInUrl", "twitterUrl", "githubUrl", "apiDocsUrl"}:
        value_low = value_text.lower().rstrip("/")
        if value_low and any(value_low == str(link).lower().rstrip("/") for link in links):
            return {"status": "verified", "value": value, "confidence": 1.0, "source_url": source_url, "evidence": value_text}
        if value_low and value_low in corpus.lower():
            return {"status": "verified", "value": value, "confidence": 0.95, "source_url": source_url, "evidence": _snippet(value_text, corpus)}
        return {"status": "unsupported", "value": value, "confidence": 0.0, "source_url": source_url, "evidence": "URL was not found on the fetched official page."}
    if field in BOOLEAN_TERMS and BOOLEAN_TERMS[field]:
        terms = BOOLEAN_TERMS[field]
        low = corpus.lower()
        supplied = str(value).strip().lower() in {"true", "1", "yes", "y", "open"}
        negative_patterns = {
            "hasApi": ("does not provide an api", "no api", "without an api", "api is not available", "no api access"),
            "isOpenSource": ("not open source", "not open-source", "closed source", "proprietary software"),
        }
        explicit_negative = any(term in low for term in negative_patterns.get(field, ()))
        observed = any(term in low for term in terms)
        if supplied and explicit_negative:
            return {"status": "contradicted", "value": value, "confidence": 0.0, "source_url": source_url, "evidence": next(term for term in negative_patterns[field] if term in low)}
        if observed and supplied:
            return {"status": "verified", "value": value, "confidence": 0.9, "source_url": source_url, "evidence": next((term for term in terms if term in low), "")}
        if observed and not supplied:
            return {"status": "contradicted", "value": value, "confidence": 0.0, "source_url": source_url, "evidence": "Official page contains evidence supporting the opposite boolean value."}
        if not observed and not supplied:
            # Absence of positive evidence is not proof of a negative claim.
            return {"status": "unsupported", "value": value, "confidence": 0.0, "source_url": source_url, "evidence": "Official page did not provide positive evidence for this negative boolean claim."}
        return {"status": "unsupported", "value": value, "confidence": 0.0, "source_url": source_url, "evidence": "Official page did not provide positive evidence for the supplied boolean claim."}
    if value_text.lower() in corpus.lower():
        return {"status": "verified", "value": value, "confidence": 1.0, "source_url": source_url, "evidence": _snippet(value_text, corpus)}
    ratio = token_set_ratio(value_text, corpus[:100000]) / 100.0
    if ratio >= 0.86:
        return {"status": "verified", "value": value, "confidence": round(ratio, 3), "source_url": source_url, "evidence": corpus[:500]}
    return {"status": "unsupported", "value": value, "confidence": 0.0, "source_url": source_url, "evidence": "Supplied value could not be supported by the fetched official page."}


def classify_from_official_page(corpus: str) -> tuple[str, list[str], float]:
    low = corpus.lower()
    scores = {}
    for category, terms in CATEGORY_TERMS.items():
        score = sum(1 for term in terms if term in low)
        if score:
            scores[category] = score
    if not scores:
        return "Other/Unclassified", [], 0.0
    ordered = sorted(scores, key=lambda c: (-scores[c], c))
    primary = ordered[0]
    confidence = min(1.0, scores[primary] / 3.0)
    return primary, ordered[:5], round(confidence, 3)


def verify_ingested_fields(record: dict[str, Any], page: dict[str, Any]) -> dict[str, Any]:
    """Verify every non-empty ingested column without silently trusting input data."""
    source_url = page.get("final_url") or page.get("source_url") or record.get("official_url") or ""
    title = _norm(page.get("title"))
    description = _norm(page.get("description"))
    text = _norm(page.get("text"))
    corpus = " ".join(x for x in (title, description, text) if x)
    links = page.get("links") or []

    fields: dict[str, Any] = {}
    # Only verify fields that existed in the incoming dataset/discovery record.
    # Enrichment fields are outputs, not claims supplied by the source.
    input_fields = record.get("_input_fields")
    if not isinstance(input_fields, list):
        input_fields = [
            k for k, v in record.items()
            if v not in (None, "", [], {})
            and not k.startswith("aiorbit_")
            and k not in {"canonical_key", "input_source", "discovery_sources", "verification_evidence", "verification_status", "verification_scope", "verified_at", "field_verification", "_input_fields"}
        ]
    for field in input_fields:
        value = record.get(field)
        fields[field] = _status_for_value(field, value, corpus, source_url, links)

    name = _norm(record.get("name") or record.get("tool_name"))
    name_tokens = [x for x in re.findall(r"[a-z0-9]+", name.lower()) if len(x) > 2]
    identity_score = 1.0 if name and (name.lower() in corpus.lower() or (name_tokens and sum(t in corpus.lower() for t in name_tokens) / len(name_tokens) >= 0.6)) else 0.0
    if not identity_score:
        fields["name"] = {"status": "contradicted", "value": record.get("name"), "confidence": 0.0, "source_url": source_url, "evidence": "Product name could not be matched to the official page."}

    category, categories, category_confidence = classify_from_official_page(corpus)
    supplied_category = record.get("toolCategories") or record.get("category")
    category_check = _status_for_value("category", supplied_category, corpus, source_url, links) if supplied_category else {"status": "empty", "value": "", "confidence": 0.0, "source_url": source_url, "evidence": ""}

    counts = {"verified": 0, "contradicted": 0, "unsupported": 0, "unverified_external_claim": 0, "empty": 0}
    for result in fields.values():
        counts[result["status"]] = counts.get(result["status"], 0) + 1

    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "source_url": source_url,
        "source_domain": urlparse(source_url).netloc.lower(),
        "identity": {"status": "verified" if identity_score else "contradicted", "confidence": identity_score, "evidence": title or description},
        "official_category": {
            "primary": category,
            "categories": categories,
            "confidence": category_confidence,
            "source": source_url,
            "method": "official_page_text",
        },
        "input_category_check": category_check,
        "fields": fields,
        "summary": counts,
        "all_non_empty_fields_checked": True,
    }
