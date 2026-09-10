# Architecture

## Data layers

### 1. Raw
Exactly what came from an uploaded dataset or discovery source.

### 2. Normalized
Canonical names, URLs, domains and identifiers.

### 3. Verification
Independent checks against official websites, official documentation, repositories or other authoritative sources.

### 4. Enrichment
Additional metadata from appropriate secondary sources.

### 5. Curation
Deduplication, quality scoring, comparison against alternatives and accept/reject decisions.

### 6. Published
Only records that satisfy the configured quality threshold and verification policy.

## Critical control

An imported record can never become trusted merely because it appeared in an input CSV/JSON/XLSX. It must have verification evidence.

## Recommended production extension

Add:
- async crawlers
- source-specific adapters
- robots.txt and terms-aware fetching
- official-source extraction
- semantic embeddings for event/product deduplication
- LLM-assisted structured extraction with schema validation
- human review queue
- audit logs
- retry/dead-letter queues
- scheduled jobs
- monitoring/metrics
- PostgreSQL
- object storage for raw snapshots
- secrets management
