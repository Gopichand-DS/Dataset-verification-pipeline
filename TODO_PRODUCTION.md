
# Production Roadmap

## Completed in current layer

- [x] Public webpage adapter with bounded retries
- [x] RSS adapter
- [x] Canonical URL capture
- [x] Field-level verification evidence
- [x] Audit trail for verification
- [x] Conservative public-page enrichment
- [x] Evidence-gated scoring
- [x] High-level Pipeline API
- [x] CSV/XLSX/JSON input
- [x] JSON/CSV output
- [x] Unit/integration tests

## Next P0

- [ ] Implement source-specific parsers for each allowed public directory
- [ ] Build module-specific schemas for tools/companies/agents/MCP/robots/devices/models/news
- [ ] Add official-source URL discovery and redirect/domain validation
- [ ] Add field conflict resolution with source hierarchy
- [ ] Add domain-specific scoring evaluators using explicit evidence
- [ ] Add source-level rate limits, cache and conditional requests
- [ ] Add robust news event clustering and best-source selection

## P1

- [ ] Entity resolution across aliases/domains
- [ ] Embedding-based semantic deduplication where justified
- [ ] Human-review queue with reason codes
- [ ] Source health dashboard
- [ ] Incremental updates instead of repeated full ingestion

## P2

- [ ] PostgreSQL
- [ ] Queue/worker execution
- [ ] Scheduler integration
- [ ] Metrics/alerts
- [ ] Versioned exports and data lineage
