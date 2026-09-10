# AIOrbit Tools Verification Flow v6.7

The tools workflow follows this order:

1. Preserve every input column exactly; never discard source columns.
2. Check row identity. A row without both a usable tool name and website URL is retained but left unprocessed.
3. Normalize the official website URL.
4. Independently fetch the official website. HTTP reachability alone is not acceptance.
5. Crawl a bounded set of same-domain evidence pages discovered from the official site: pricing, login/sign-up, API/docs, about/company and legal pages when available.
6. Verify the product identity against the official page.
7. Verify supplied claims against independently fetched official evidence. The input dataset is never proof.
8. Enrich only when evidence exists: description, logo, pricing model/amount/frequency, account access, API docs, company, launch/release date, official social/GitHub links.
9. Generate a deterministic `canonical_id` from product name + official domain.
10. Classify the tool into a primary category and supported secondary categories from official-site evidence.
11. Preserve the original value and verification result; do not silently overwrite a contradicted claim.
12. Deduplicate and update the single master output file.

## Important truth rules

- A valid URL does not mean all fields are true.
- Missing evidence means `unsupported` / `not publicly disclosed`, not a guessed value.
- Directory metrics such as views, upvotes and ratings are not treated as official product facts.
- Pros and cons must be evidence-based summaries of documented capabilities/limitations; never fabricate them.
