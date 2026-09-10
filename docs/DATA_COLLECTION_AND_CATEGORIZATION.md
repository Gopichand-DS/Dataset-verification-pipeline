# Data collection, verification, and categorization

## Intended use

The `tools` workflow is designed for an existing dataset of roughly 1,000 tool records (or larger). It is **not** a snapshot exporter. The same master file is updated on every run.

The pipeline does four things:

1. **Preserve the input** — every incoming column is retained; no source column is silently discarded.
2. **Normalize the contract** — canonical tool fields are added when absent, with blank values rather than guessed values.
3. **Independently verify** — `official_url` is checked against the public official page. `verification_status=verified` means the official URL/page passed the reachability/content gate; it does not mean every column has been proven.
4. **Categorize** — a conservative `aiorbit_category` and `aiorbit_categories` are derived from explicit text signals. Existing source `category` data is retained unchanged.

## Stable master file

Use one file, for example:

```text
data/output/tools_master.json
```

Each run upserts into that file:

```text
existing master
      +
new dataset/discovery results
      ↓
canonical deduplication
      ↓
official-source verification
      ↓
category classification
      ↓
master upsert
```

A temporary source failure does not delete existing records.

## All columns

The master file contains a top-level `columns` array. It is the union of:

- canonical module fields;
- AIOrbit verification/category fields;
- every source/input column observed across runs.

Every record receives every column in the master contract. Missing values are blank. New columns introduced by a later dataset are added to the contract and backfilled as blank for older records.

## Tool categories

Primary categories include:

`News`, `Media`, `Chatbots`, `Search`, `Research`, `Writing`, `Coding`, `Developer Tools`, `Image`, `Video`, `Audio & Music`, `Design`, `Presentations`, `Productivity`, `Automation`, `Agents`, `Data & Analytics`, `Marketing`, `Sales`, `Customer Support`, `Education`, `Finance`, `Legal`, `Healthcare`, `Security`, `Translation`, `3D`, `Social Media`, `E-commerce`, `Human Resources`, and `Other/Unclassified`.

The classifier is deliberately conservative. It uses the tool's name, description, use case, source category/tags and similar explicit text. It does not invent a category when there is insufficient evidence.

## Recommended command for an existing dataset

```powershell
python run.py --module tools --workflow --input data\input\tools.csv --output data\output\tools_master.json --limit 1000
```

Run the **same command again** when you have more data. It updates `tools_master.json` instead of creating a new snapshot.

For live directory discovery instead:

```powershell
python run.py --module tools --workflow --output data\output\tools_master.json --limit 100
```

Use `--fresh-output` only when you intentionally want to replace the master file.

## Important verification distinction

The current workflow has two layers:

- **Official URL/page verification:** proves that the supplied official URL is reachable and has public page evidence.
- **Field-level verification:** must be added/expanded when a specific field (pricing, API, platform, model, etc.) needs proof from the official page.

Therefore the pipeline never claims that all 1,000 records' individual fields are verified merely because their URLs are reachable.
