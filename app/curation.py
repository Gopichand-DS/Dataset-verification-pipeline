from app.dedupe import likely_duplicate
from app.scoring import score

def compare_and_dedupe(records):
    kept, duplicates = [], []
    for candidate in records:
        duplicate_of = None
        for existing in kept:
            if likely_duplicate(
                {"name": candidate.name, "official_url": candidate.official_url, "company": candidate.company},
                {"name": existing.name, "official_url": existing.official_url, "company": existing.company}):
                duplicate_of = existing
                break
        if duplicate_of:
            duplicates.append((candidate.id, duplicate_of.id))
        else:
            kept.append(candidate)
    return kept, duplicates

def evaluate_record(module, verification, factors):
    if not verification.get("verified"):
        return 0.0, "needs_review"
    overall, decision = score(module, factors)
    if overall < 70:
        decision = "needs_review"
    return overall, decision
