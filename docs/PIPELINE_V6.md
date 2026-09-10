# AIOrbit v6 Pipeline

## Production path

1. Discover from configured primary/secondary sources.
2. Normalize candidates.
3. Deduplicate globally and retain discovery provenance.
4. Independently verify each official URL.
5. Cache verification evidence to avoid unnecessary repeated requests.
6. Apply acceptance gates.
7. Curate only accepted records.
8. Export records plus metrics/source health.

## Important distinction

A discovery directory can suggest that an entity exists. It cannot by itself prove
the entity's product facts. Official-source verification remains a separate stage.

## Monitoring

`PipelineMetrics` records discovered, verified, rejected, curated, source errors and
blocked/rate-limited sources.

## Data-quality report

```bash
python scripts/data_quality_report.py data/output/tools_curated.json
```

## Persistent master output

Workflow runs now use a single updatable JSON master file per module. If `--output` is supplied, that exact file is upserted on every run. If it is omitted, the default is `data/output/<module>_master.json`.

Matching uses `canonical_key`, then official URL, then name. Existing records are updated with new non-empty verified values; useful old values are not erased by blank values. Discovery/source lists are merged. Existing records are not deleted during a normal run, because a blocked or temporarily unavailable source must not erase previously verified data.

Use `--fresh-output` only when an intentionally clean snapshot is required.
