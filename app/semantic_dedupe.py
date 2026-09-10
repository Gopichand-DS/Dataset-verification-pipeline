from rapidfuzz.fuzz import ratio
import re


def _norm(value):
    return " ".join(str(value or "").lower().split())


def text_similarity(a, b):
    return ratio(_norm(a), _norm(b)) / 100.0


def duplicate_score(a, b):
    url_a = (a.get("official_url") or a.get("url") or "").split("?")[0].rstrip("/")
    url_b = (b.get("official_url") or b.get("url") or "").split("?")[0].rstrip("/")
    if url_a and url_b and url_a == url_b:
        return 1.0
    name = text_similarity(a.get("name"), b.get("name"))
    company = text_similarity(a.get("company"), b.get("company"))
    return 0.75 * name + 0.25 * company


def is_duplicate(a, b, threshold=0.92):
    return duplicate_score(a, b) >= threshold


def same_event(a, b, threshold=0.88):
    return text_similarity(a, b) >= threshold


def model_variant_key(name):
    s = _norm(name)
    s = re.sub(r"\b(gguf|gptq|awq|quantized|quantization|instruct|chat|base|fine[- ]?tune|finetuned)\b", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()
