---
name: fill-rate-data-fetcher
description: >
  Use this skill whenever the master orchestration agent needs spec-level fill rate
  data for a given mcat_id — the percentage of product listings where each spec is
  filled by sellers. This is a DATA SOURCE skill (DS-4). Its output is used by
  Skill 5 (Spec Sequence Agent) for tier ranking decisions, and by Skill 6
  (Option Validator) for validating whether low-fill specs need option fixes.
  Also use when a Primary spec has suspiciously low fill rate and the master agent
  needs to understand why. Do NOT use this skill alone to make tier decisions —
  always combine with DS-1 and DS-3 signals via Skill 5.
---

# DS-4: Fill Rate Data Fetcher

## What this skill does

Fetches spec-level fill rate data for the current mcat_id — showing what percentage
of product listings have each spec filled. This is the seller-side adoption signal:
high fill rate = sellers consider this spec essential; low fill rate on a Primary
spec = something is wrong.

---

## Data Source — DS-4

**Google Sheet (CSV export):**
```
https://docs.google.com/spreadsheets/d/1JF7Hh7DDCx9XieL4U4EoJLPQtdDxctl7wZYbfvAwb5I/export?format=csv
```

**Filter by:** `mcat_id` column matches current mcat_id

**Expected columns:**

| Column | Description |
|--------|-------------|
| `mcat_id` | MCAT ID — use for filtering |
| `spec_name` | Spec name |
| `spec_fill_rate` | Fill rate as a decimal or percentage (0–100) |
| `product_count` | Number of products evaluated |

---

## Processing

Fetch all rows from DS-4 CSV. Filter where `mcat_id` matches current.

Normalize fill rate values:
- If values are 0–1 range → multiply by 100 to get percentage
- If values are 0–100 range → use as-is

Output per spec:
```json
{
  "spec_name": "Grade",
  "fill_rate": 87.5,
  "product_count": 240
}
```

Sort by `fill_rate` descending.

---

## Output returned to master agent

```json
{
  "source": "DS-4_fill_rate",
  "specs": [
    {
      "spec_name": "Grade",
      "fill_rate": 87.5,
      "product_count": 240
    },
    {
      "spec_name": "Color",
      "fill_rate": 12.3,
      "product_count": 240
    }
  ],
  "data_availability": "RICH | SPARSE | EMPTY"
}
```

**Data availability thresholds:**
- `RICH` — 5+ specs with fill rate data, product_count > 20
- `SPARSE` — 1–4 specs, or product_count < 20
- `EMPTY` — no rows for this mcat_id

---

## How master agent uses DS-4

| Signal pattern | What it means | Action |
|---------------|---------------|--------|
| High fill rate (>80%) on a spec | Sellers treat this as essential | Strong candidate for Primary/Secondary |
| Low fill rate (<25%) on a PRIMARY spec | Critical problem — spec is wrong tier, confusing, or has bad options | Investigate with Skill 6; consider Skill 5 to demote |
| Low fill rate (<25%) on Tertiary spec | Expected — sellers skip completeness specs | No action needed |
| Very low fill rate (<10%) + no DS-1/DS-3 signal | Likely useless spec | Flag for removal |
| High fill rate but all values are "N/A" / "As per requirement" | Habit-filling — spec may be mandatory field, not real engagement | Sanity check via World Knowledge skill |

---

## Important caveats

- **Mandatory fields inflate fill rate.** Some specs may be required by the platform,
  making fill rate artificially high regardless of seller intent.
- **Habit-filling.** High fill rate with mostly placeholder values is not true engagement.
  Always check example values from DS-1 alongside fill rate from DS-4.
- **Never use DS-4 alone for tier decisions.** Always combine with DS-1 product_count
  and DS-3 impressions. A spec with high fill rate but zero buyer discussion may be
  a habit spec — correct for Secondary or Tertiary, not Primary.
