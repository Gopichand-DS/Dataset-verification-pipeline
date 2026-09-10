# Tools Dataset Processing Specification

## Required order

1. **Schema/row check** — preserve all incoming columns. Rows missing the tool identity pair (`name` and a website URL) are retained but marked `left_unprocessed`; they are not guessed or silently deleted.
2. **Official URL verification** — normalize the URL and independently fetch it. A reachable URL alone is not enough.
3. **Official-site link expansion** — follow a bounded set of same-domain evidence links for pricing, login/sign-up, API/docs, about/company and legal pages when present.
4. **Product identity verification** — confirm the page represents the claimed tool.
5. **Tool description** — use official product evidence; do not copy unsupported directory claims.
6. **Pros/cons** — produce conservative evidence-based summaries. Do not invent limitations or advantages.
7. **Account access** — determine whether login/sign-up is required or whether the official pages leave this unclear.
8. **Pricing** — determine free/paid/freemium where explicitly evidenced, collect visible price amounts and billing frequency, and count/record pricing tiers when the pricing page exposes them.
9. **Company** — identify the owning/releasing company from official evidence when possible.
10. **Launch/release** — record a date only when an explicit official date/year is found; otherwise leave blank / not publicly disclosed.
11. **Category** — classify from official-site evidence and retain the number of supported categories.
12. **Identity** — retain the original tool name and generate a deterministic `canonical_id` from normalized official domain + tool name.
13. **Field verification** — compare each non-empty input value against independently fetched evidence. Keep the original value and record `verified`, `contradicted`, `unsupported`, or `unverified_external_claim`.
14. **Master update** — merge into one persistent master file; never create a new snapshot for each run unless `--fresh-output` is explicitly used.

## Truth rule

The supplied dataset is **candidate data, not evidence**. If official evidence does not establish a value, AIOrbit must not guess it.
