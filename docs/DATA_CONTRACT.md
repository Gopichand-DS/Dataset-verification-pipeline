# AIOrbit Data Contract

Every module record should carry these control fields in addition to domain fields:

- `canonical_key`
- `status`
- `discovery_source`
- `verification_source`
- `last_verified_at`
- `verification_status`
- `verification_evidence`
- `field_provenance`
- `quality_score`
- `curation_decision`
- `curation_notes`

## Field states

Each important field should ultimately be one of:

- `verified`
- `conflict`
- `missing`
- `unverifiable`

Do not turn `missing` or `unverifiable` into guessed values.

## Dataset ingestion rule

Input values remain in `raw_json`. Verified values and evidence are stored separately. This preserves an audit trail and allows the team to identify exactly where an imported dataset was wrong or incomplete.
