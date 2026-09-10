
# AIOrbit Production Workflow

## Canonical lifecycle

**Discovery → Raw Store → Official Verification → Evidence Capture → Enrichment → Identity/Deduplication → Evidence-Backed Scoring → Curation → Export**

### 1. Discovery
Directory/feed/API results are treated as candidates only.

### 2. Raw Store
The original candidate payload is preserved before normalization.

### 3. Official Verification
The pipeline attempts to fetch the candidate's public official URL. HTTP status,
redirect target, canonical URL, title, description and text are retained.

### 4. Evidence Capture
Important claims receive field-level evidence. Unsupported claims remain
unsupported.

### 5. Enrichment
Only explicit public signals are added. The system does not infer unknown
facts.

### 6. Identity and Deduplication
Canonical URL, name and company are used before fuzzy comparison. Duplicates
are marked rather than silently discarded.

### 7. Scoring
The generic scorer is evidence-gated. Domain-specific evaluators should replace
the baseline factor generator for production-quality rankings.

### 8. Curation
High-quality verified records can be marked curated. Borderline records remain
reviewable; rejected and duplicate records are retained for auditability.

## Access-control rule

AIOrbit does not bypass CAPTCHAs, login walls, paywalls, robots restrictions,
or other access controls. When a source is unavailable, record the failure and
use an allowed RSS/API/official alternative.
