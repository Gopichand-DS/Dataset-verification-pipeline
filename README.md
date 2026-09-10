# AIOrbit Curator

A quality-first ingestion, verification, enrichment, deduplication, scoring and curation pipeline for the AIOrbit ecosystem.

## Modules

- tools
- companies
- agents
- mcp
- robots
- devices
- models
- news

## Core rule

`Discovery/Input → Normalize → Verify → Enrich → Deduplicate → Score → Curate → Export`

Imported datasets are **not trusted automatically**. Every ingested record enters a raw layer and must pass verification before becoming curated/trusted data.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

python -m app.cli init-db
python -m app.cli ingest --module tools --file data/input/tools.csv
python -m app.cli verify --module tools
python -m app.cli curate --module tools
python -m app.cli export --module tools --output data/output/tools_curated.csv
```

For web verification, configure `.env` and run the verification workers. The project intentionally separates discovery sources from authoritative verification sources.

## Design principles

1. Quality over quantity.
2. Official sources are preferred for product facts.
3. Do not guess missing fields.
4. Canonical URL/domain/repository identifiers drive deduplication.
5. Similar products are compared instead of blindly bulk-added.
6. Scores are module-specific and transparent.
7. Verification evidence is stored separately from ingested data.
8. Personal data is not collected unless strictly relevant to product/company attribution.
9. News is event-grouped and ranked; the target is 20–30 stories/day, not maximum volume.
10. Batch targets are ceilings/targets, never reasons to lower the quality bar.


## New operational layer

The project now includes:
- pluggable source adapters;
- RSS discovery infrastructure;
- source health records;
- field provenance;
- semantic duplicate scoring;
- news event clustering;
- scheduler configuration;
- acceptance criteria;
- production implementation checklist.

The system intentionally does **not** pretend that a directory was crawled when no live adapter/access was executed. Real source adapters must be implemented and run with permitted access methods.
## Latest production-hardening layer

- Public HTML source adapter with retries and canonical URL capture
- Field-level verification evidence and audit events
- Evidence-gated scoring instead of unconditional baseline credit
- Conservative public-page enrichment
- Production pipeline runner and tests


## Interpreting workflow limits

`--limit 100` means at most 100 discovered candidates enter the verification workflow. The final `records` count can be lower because duplicates, unreachable official URLs, blocked sources, and acceptance failures are removed. A 100-candidate run producing 80 records is therefore expected and should be investigated through `metrics`, `source_health`, and the data-quality report rather than treated as a failure.

## v7.0 input-dataset verification fixes

- Normalizes common source headers (`toolName`, `tool_name`, `title`, `websiteUrl`, `website_url`, `site`, `homepage`, `productUrl`, etc.) before the identity gate.
- Preserves all original source columns while adding canonical `name`, `official_url`, and `company` fields.
- Separates source claims from schema-generated/enrichment fields so generated values are never treated as input evidence.
- Keeps unsupported non-critical claims as reviewable warnings rather than automatic rejection.
- Treats explicit boolean contradictions as hard failures; absence of evidence for a negative claim remains unsupported.
- Adds diagnostics for missing-identity rows.
- Adds a pytest bootstrap so tests run consistently with `python -m pytest -q`.
