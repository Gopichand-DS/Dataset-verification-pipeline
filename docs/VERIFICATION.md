# Verification Protocol

For every dataset ingestion:

1. Preserve the raw record.
2. Normalize identifiers.
3. Determine the authoritative verification source.
4. Fetch/check the official source where technically and legally permitted.
5. Extract evidence.
6. Compare ingested fields against verified fields.
7. Mark each field as verified, conflicting, missing, or unverifiable.
8. Store verification timestamp and source.
9. Only then score and curate.
10. Keep rejected/needs-review records for auditability.

Never invent a value. Use `Not publicly disclosed` or leave blank when appropriate.

For companies and products, domain + official URL + repository/model ID are strong canonical identifiers.
