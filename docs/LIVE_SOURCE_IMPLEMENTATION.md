
# Live Source Implementation

The project now supports public HTML fetching through `WebPageAdapter` and RSS
through `RSSAdapter`.

## Safe operating rules

- Respect robots.txt, terms, rate limits and access restrictions.
- Do not bypass CAPTCHAs, login walls, paywalls or anti-bot controls.
- Prefer RSS/API/official feeds where available.
- Cache fetched pages and avoid unnecessary repeated requests.
- Record failures as reviewable events rather than silently dropping records.
- Keep discovery evidence separate from official-source verification.

## Example

```bash
python scripts/run_production_pipeline.py \
  --module tools \
  --url https://example.com/public-tools-page
```

The command is intentionally source-agnostic. Source-specific parsers should be
added only after the page structure and licensing/access conditions are known.
