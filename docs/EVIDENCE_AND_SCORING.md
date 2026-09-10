
# Evidence-Backed Verification and Scoring

AIOrbit must not treat a discovered directory entry as proof.

## Trust flow

1. Discover a candidate from a directory/feed/search source.
2. Preserve the raw candidate unchanged.
3. Resolve an official website URL.
4. Fetch only publicly accessible pages.
5. Record HTTP status, final URL, canonical URL, title and extracted text.
6. Compare ingested claims against fetched evidence.
7. Store field-level `VerificationEvent` records.
8. Enrich only from explicit page signals.
9. Deduplicate using canonical identity signals.
10. Score only after verification/evidence collection.

## Important constraint

The current generic evaluator is a conservative baseline, not a substitute for
domain-specific judgment. Capability, usefulness, adoption, activity and
differentiation require domain-aware evidence. Production evaluators should
supply those factors from explicit signals such as product documentation,
release history, usage/adoption evidence, repository activity, or credible
third-party reporting.

Unknown facts remain unknown. Do not infer price, model, funding, employee
count, deployment status, specifications, or other fields merely because a
similar product has them.

## Auditability

Each verification should retain:

- source URL
- final URL
- HTTP status
- verification timestamp
- field
- ingested value
- verified value
- evidence snippet
- verification result
- score breakdown

This makes the curation decision inspectable and reproducible.
