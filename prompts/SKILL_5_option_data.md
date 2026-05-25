---
name: option-data-fetcher
description: >
  Use this skill whenever the master orchestration agent needs option-level fill
  rate data for a given mcat_id — showing which specific option values within each
  spec are actually being used by sellers in their listings. This is a DATA SOURCE
  skill (DS-5). Its output is used primarily by Skill 6 (Option Validator Agent)
  to make KEEP/REJECT/MERGE decisions on individual option values. Also use when
  a spec has suspiciously few or many options and the master agent needs to
  understand real option adoption before deciding what to keep or remove.
  Do NOT use this skill alone to make option decisions — always route findings
  through Skill 6 for final validation.
---

# DS-5: Option Fill Rate Data Fetcher

## What this skill does

Fetches option-level fill rate data — for each spec in the category, which specific
option values are being used by sellers and how frequently. This reveals which options
are real market values vs noise, duplicates, or placeholder entries.

---

## Data Source — DS-5

**Google Sheet (CSV export):**
```
https://docs.google.com/spreadsheets/d/1bTB2AXhoydP282fWPxoFt9nZ8rj5iI3DSzpKQ9Cu194/export?format=csv
```

**Filter by:** `mcat_id` column matches current mcat_id

**Expected columns:**

| Column | Description |
|--------|-------------|
| `mcat_id` | MCAT ID — use for filtering |
| `spec_name` | Spec name |
| `spec_option_name` | The specific option value |
| `option_fill_rate` | Percentage of listings using this option (0–100) |

---

## Processing

Fetch all rows from DS-5 CSV. Filter where `mcat_id` matches current.

Group by `spec_name`, then list options with their fill rates:

```json
{
  "spec_name": "Grade",
  "options": [
    { "option_value": "IS 2062 E250", "fill_rate": 45.2 },
    { "option_value": "IS 2062 E350", "fill_rate": 31.8 },
    { "option_value": "Custom", "fill_rate": 0.1 }
  ]
}
```

Sort options by `fill_rate` descending within each spec.

---

## Output returned to master agent

```json
{
  "source": "DS-5_option_fill_rate",
  "specs": [
    {
      "spec_name": "Grade",
      "options": [
        { "option_value": "IS 2062 E250", "fill_rate": 45.2 },
        { "option_value": "IS 2062 E350", "fill_rate": 31.8 },
        { "option_value": "Custom", "fill_rate": 0.1 }
      ]
    }
  ],
  "data_availability": "RICH | SPARSE | EMPTY"
}
```

**Data availability thresholds:**
- `RICH` — 3+ specs with option-level data, multiple options per spec
- `SPARSE` — 1–2 specs or very few options per spec
- `EMPTY` — no rows for this mcat_id

---

## How master agent uses DS-5

This data is primarily passed to **Skill 6 (Option Validator Agent)** for decisions.

Quick signals the master agent can read directly:

| Signal pattern | Likely meaning |
|---------------|----------------|
| Option fill_rate = 0 across the board | No sellers have used this option — candidate for removal |
| One option has >80% of all fill rate for a spec | Single-option dominance — spec may not be differentiating |
| Many options with fill_rate < 1% | Option list is bloated with noise — Skill 6 needed |
| Option values that look like placeholder text (`"Other"`, `"Custom"`, `"As per requirement"`) with any fill rate | Junk options filling by default — remove |
| Two options with near-identical names but different fill rates | Likely formatting duplicate — Skill 6 will MERGE |

---

## Important caveats

- **Always combine with DS-1 and DS-3.** An option with low fill rate but high
  buyer search impressions may still be valid — buyers want it but sellers aren't
  offering it. Skill 6 handles this cross-signal logic.
- **Do not remove options based on DS-5 alone.** Route all removal decisions
  through Skill 6 which applies the full KEEP/REJECT/MERGE framework.
- **Fill rate of 0 ≠ invalid.** A newly added option may have zero fill rate
  simply because it was added recently. Cross-check with DS-1 and DS-3 signals.
