# AIOrbit Source Policy v5

## Non-negotiable data lineage

`Discovery -> Candidate -> Official-source verification -> Field evidence -> Normalize -> Deduplicate -> Score -> Curate -> Publish`

### Discovery
Directories, registries, search indexes and public lists are discovery inputs. They do not prove product facts.

### Verification
Each candidate must have an independently checked official URL where one exists. HTTP reachability is only a gate; it is not field-level proof.

### Evidence
Every material field used in curation should carry source/evidence metadata. Unknown values remain blank or `Not publicly disclosed`.

### Deduplication
Use canonical URL/domain, legal identity, model/repository identifiers and aliases. Merge provenance rather than creating multiple records for the same entity.

### Quality
Reject dead, fake, unverifiable, spammy, duplicate and meaningless entries. Quality thresholds remain module-specific and must not be relaxed to hit quotas.

### Access failures
401/403/429, robots restrictions, timeouts and server errors are recorded in source health. Do not bypass anti-bot controls. Continue with other permitted sources.

### Reproducibility
Store discovery timestamp, source, verification timestamp, evidence URL, decision/reason and pipeline version for every publishable record.
