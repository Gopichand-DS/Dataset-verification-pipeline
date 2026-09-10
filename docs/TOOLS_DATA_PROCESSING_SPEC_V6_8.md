# AIOrbit Tools Data Processing Specification v6.8

## Required output contract

For every usable tool row, AIOrbit preserves every input column and adds/maintains these canonical fields:

- `canonical_id`
- `slug`
- `name`
- `logoUrl` + `logoVerification`
- `description`
- `official_url` / `websiteUrl` + `websiteVerification`
- `features`
- `pros`
- `cons`
- `releaseDate`
- `launchDate`
- `recentlyUpdated`
- `pricingModel`
- `pricingAmount`
- `billingFrequency`
- `pricingTiers`
- `accountAccess`
- `isOpenSource`
- `compatibility`
- `targetUsers`
- `hasApi`
- `apiDocsUrl`
- `performanceScore`
- `useCases`
- `toolCategories`
- `categoryCount`
- `releasedBy` / `company` + `companyVerification`
- `lastVerifiedAt`

## Verification order

1. Validate row structure and preserve all source columns.
2. If the identity pair (`name` + usable website URL) is missing, retain the row but mark it `left_unprocessed`; do not guess.
3. Normalize and independently fetch the website.
4. Follow bounded same-domain links for pricing, login/sign-up, API/docs, company/about and legal evidence.
5. Confirm the page represents the claimed tool.
6. Validate the website URL and redirect target; use the canonical domain/product identity for duplicate detection.
7. Validate the logo URL and confirm that it is referenced by official-page metadata. A URL check is not presented as visual logo recognition.
8. Build a concise official-source description and evidence-backed features/pros/cons.
9. Determine account access from official login/sign-up/product-flow evidence; otherwise leave it undisclosed.
10. Determine free/paid/freemium pricing, visible amounts, billing frequency and pricing tiers from official pricing evidence.
11. Determine open-source status only from explicit evidence; do not infer it merely from a GitHub link.
12. Determine compatibility, target users and use cases only where official evidence supports them.
13. Determine company, launch/release date and most recent update only from explicit evidence; otherwise leave blank / not publicly disclosed.
14. Determine primary and supported categories from official product evidence and record `categoryCount`.
15. Generate deterministic `canonical_id` from normalized official domain + normalized tool name.
16. Compare non-empty input claims against independent evidence and preserve the original claim plus verification status/evidence.
17. Update the persistent master dataset instead of creating a new snapshot.

## Truth rules

- Input data is candidate data, never proof.
- HTTP 200/valid URL is necessary but not sufficient for tool verification.
- Missing evidence is not permission to guess.
- Third-party metrics such as views, upvotes, review counts and ratings remain external claims unless independently supported by an appropriate source.
- `performanceScore` is an AIOrbit evidence/quality assessment, not a fabricated benchmark score. A true performance benchmark requires benchmark evidence.
- Logo validation confirms URL/official-page reference; visual logo identity is not claimed without image-level inspection.
