---
# brand-category-spec-review

## What this skill is for
  Use this skill ONLY when the category under review is a **brand category** — i.e., the
  spec set is associated with a specific brand (e.g., "Bosch Drills", "Havells Wires",
  "Asian Paints Emulsions"). Triggers include: any request to audit, validate, or improve
  specs for a brand category; any mention of "brand spec review", "brand category audit",
  or "OEM spec validation". Do NOT use for generic/unbranded category spec work — use the
  standard Option Validator skill for those.
---

# Brand Category Spec Review

## What this skill is for

This skill governs how to audit specs that belong to **brand categories** — spec sets
tied to a specific brand's product listings on the platform. Brand category specs have
two requirements beyond standard option validation:

1. **Web-confirmed removal** — Before removing any existing option, you must verify via
   web search that the value is not a real, actively used specification for products in
   this brand and category. Data signals alone are not sufficient grounds for deletion.

2. **Input type audit** — For every spec in the brand category, you must evaluate whether
   the current `input_type` (`radio_button`, `multi_select`, `text_type`) is correct given
   the nature of the spec and the options present.

---

## The data sources you have

These are the same three option-level signals used in standard option validation.

**Option Fill Rate**
Percentage of brand category listings where sellers have selected this option value.
High = commonly used. Low = rarely selected (but not automatically invalid for brand specs).

**Buyer Search Data (Impressions)**
How many times buyers filtered by this specific value when searching within this brand
category. High = buyers actively look for it. Low = low buyer-side demand.

**Buyer-Seller Call Data (Product Count)**
How many times this specific value appeared in real buyer-seller phone calls for this brand.
High = transactionally relevant. Low = not a common discussion point.

---

## Part 1 — Option Validation with Web-Confirmed Removal

### Step 1 — Screen for absurd options first (no web check needed)

Reject immediately, without a web search, if the option is clearly wrong regardless of
context:

- **Type mismatch** — a colour name under a Size spec; a weight value under a Brand spec;
  a numeric dimension under a Finish spec
- **Junk or gibberish** — `asdf`, `xxx`, `123abc`, random strings
- **Test or placeholder data** — `test`, `sample`, `demo`, `NA`, `N/A`, `nil`, `-`, `.`
- **Vague filler** — `As per requirement`, `Customized`, `Standard`, `Other`, `General`,
  `Miscellaneous`, `Any`
- **Excessively long** — more than 50 characters
- **Promotional text** — `Best Quality`, `Premium Grade`, any URL or marketing phrase

These are safe to reject without a web search because they are structurally invalid, not
just low-signal.

### Step 2 — Evaluate signal strength for all other options

For every option that passes the absurd-option screen, check its signals:

| Signal tier | Condition | Preliminary decision |
|-------------|-----------|----------------------|
| Strong | 2+ signal sources, OR fill rate ≥ 20%, OR product count ≥ 10 | KEEP — no web check needed |
| Moderate | Appears in exactly 1 signal source with any non-zero value | KEEP — no web check needed |
| Zero signal | Fill rate = 0 AND product count = 0 AND impressions = 0 | → Go to Step 3 (web check) |

### Step 3 — Web check before any removal (brand category rule)

**This step is mandatory for brand categories.** Do not remove a zero-signal option
without first performing a web search to confirm it is not a real, valid specification
for this brand and category.

**How to perform the web check:**

Search query pattern:
```
[Brand Name] [Category] [Option Value] specifications
```

Examples:
- `Havells wire 2.5 sq mm specifications`
- `Bosch drill 13mm chuck specifications`
- `Asian Paints emulsion matte finish`

**Interpreting web results:**

| Web result | Action |
|------------|--------|
| Option appears on brand's official site, product catalogue, or reputable retailer listings | KEEP — it is a real spec value, even with zero platform signal |
| Option appears only on random forums, aggregator spam, or cannot be found at all | REJECT — confirm it is not a real value for this brand |
| Results are ambiguous (partial matches, different category) | Flag as UNCERTAIN — do not remove; escalate for human review |

**Document the web check in your output** — record the search query used and what the
result confirmed.

### Step 4 — Merge duplicates

When two options represent the same real value in different formats, merge toward the
cleaner, more standardised form. Common cases:

- Unit spacing: `2.5sqmm` → `2.5 sq mm`
- Capitalisation: `matte` → `Matte`
- Spelling variants: `Aluminium` / `Aluminum` → use Indian B2B standard (`Aluminium`)
- Abbreviated vs full: `GI` vs `Galvanized Iron` → keep whichever form Indian B2B uses

After merging, the absorbed option is removed; the canonical form is kept.

### Step 5 — Add missing options from data

Check all three data sources for values that appear in the data but are absent from the
current option list. Every candidate addition must pass:

| Check | Requirement |
|-------|-------------|
| Type match | Value is appropriate for this spec in this brand category |
| Not a duplicate | Not a variant of something already in the list |
| Not junk | Not a placeholder, vague filler, or promotional text |
| Standardised form | Correct units, Title Case for text, compact numeric format |
| At least 1 signal | Evidence from at least one data source |

---

## Part 2 — Input Type Audit

For **every spec** in the brand category, evaluate whether the current `input_type` is
correct. This is independent of option validation — even a spec with healthy options can
have the wrong input type.

### The three input types

| Type | When to use |
|------|-------------|
| `radio_button` | Exactly one value applies at a time; values are mutually exclusive; typically 2–8 options |
| `multi_select` | Multiple values can apply simultaneously to the same product |
| `text_type` | Value is free-form, brand-model-specific, or has no dominant standard set of values |

### Decision rules — apply in order

**Rule A — Force `text_type` when:**
- The spec captures model numbers, serial codes, batch codes, or catalogue references
- The spec has free-form dimensions where every product has a unique value (e.g., custom
  cut lengths, exact weights that vary per SKU)
- No more than 2–3 recurring values can be identified across the entire category, and
  those values are brand-specific identifiers, not general attribute values
- Action: Set `input_type: text_type` and clear the options list to `[]`

**Rule B — Force `radio_button` when:**
- The current type is `multi_select` AND the spec's values are mutually exclusive
  (a product can only have one value at a time — e.g., Voltage Rating, Phase, Insulation
  Class)
- There are 2–8 clearly distinct values covering the real distribution
- Action: Change to `radio_button`; keep the validated option list

**Rule C — Force `multi_select` when:**
- The current type is `radio_button` AND multiple values can legitimately apply to the
  same product simultaneously (e.g., Compatible Applications, Certifications, Compatible
  Accessory Types)
- Action: Change to `multi_select`; keep the validated option list

**Rule D — Flag `radio_button` with only 1 option:**
- A `radio_button` spec with a single option provides zero filtering value
- Action: Either find and add more real values from data/web, OR change to `text_type`
  with empty options

**Rule E — Flag oversized option lists:**
- `radio_button` with more than 10 options → trim to highest-signal options only
- `multi_select` with more than 15 options → trim to highest-signal options only

**Rule F — Keep as-is when:**
- The current type is correct given the above rules
- No structural issue is present
- Action: Record `no change` in structural_changes

### Brand category input type notes

Brand categories often have specs that look like they should be `multi_select` but are
actually `radio_button` because the brand defines a fixed single value per SKU (e.g.,
a wire's voltage grade is a single fixed value, not a multi-value attribute). When in
doubt, check the brand's product catalogue or data sheet structure via web search to
determine whether a given spec is single-value or multi-value per SKU.

---

## Formatting rules for options

| What | Standard | Wrong forms |
|------|----------|-------------|
| Units | `kg`, `mm`, `sq mm`, `V`, `W`, `A`, `rpm`, `°C`, `%`, `L`, `mL`, `Hz` | `kgs`, `MM`, `Volt`, `Watts`, `sqmm` |
| Numeric format | Compact with space: `2.5 sq mm`, `12 V`, `120 GSM` | `2.5sqmm`, `12Volt`, `120GSM` |
| Text | Title Case | ALL CAPS, all lowercase |
| Numeric order | Ascending | Random |
| Categorical order | Most common in Indian B2B first | Alphabetical |
| Indian trade terms | Use `GI`, `MS`, `PP`, `HDPE`, `FR`, `ISI` | Expanded forms when abbreviated forms dominate |

---

## What your output must include

Produce the following structured output for each spec audited.

### Per option decision

For each option in the spec (existing or candidate addition):

- **option_value** — the option being decided on
- **decision** — `KEEP` / `REJECT` / `MERGE` / `ADD`
- **merge_into** — target option name (only when decision is `MERGE`)
- **web_check_performed** — `Yes` / `No` / `Not required` (only `Yes` for zero-signal options that passed the absurd-option screen)
- **web_search_query** — the exact query used (only when web_check_performed is `Yes`)
- **web_result_summary** — what the web search confirmed (only when web_check_performed is `Yes`)
- **reason** — cite specific signal values: `ProdCount:X FillRate:Y Imp:Z — short reason`

### Per spec summary

- **spec_name** — exact name, unchanged
- **input_type_before** — original input type
- **input_type_after** — corrected input type (same as before if no change)
- **input_type_change_reason** — why the type was changed, or `No change — current type is correct`
- **final_option_list** — clean list of kept and added options only, in correct order
- **structural_changes** — any unit standardisation, range consolidation, or other fixes applied

---

## Common brand category patterns and how to handle them

| Pattern | How to handle |
|---------|--------------|
| Spec has only brand-model codes as options (e.g., `FR-V-90`, `FRLS-1100`) | Change to `text_type`, empty options — model codes are free-form |
| All options have zero fill rate but are valid brand spec values per web | Keep all after web confirmation — low fill is a data gap, not invalidity |
| Spec mixes ISI grades and non-ISI values | Standardise ISI grades to official notation; web-check non-ISI values |
| `multi_select` used for a single-value spec like Voltage Rating | Change to `radio_button` |
| Option list has both `1 Phase` and `Single Phase` | Merge to whichever the brand's official literature uses (check via web) |
| All options have moderate fill but one outlier has zero fill | Web-check the zero-fill outlier before removing |

---

## What this skill does NOT cover

- Generic (non-brand) category spec audits → use the standard Option Validator knowledge
- Spec-level decisions (whether a spec should exist at all) → out of scope for this skill
- Pricing or commercial data validation → out of scope
- Creating new specs from scratch → out of scope

---
