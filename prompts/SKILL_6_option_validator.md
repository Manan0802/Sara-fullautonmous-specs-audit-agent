# option_validator

## What this skill is for

Read this when you need to audit and correct the option list for any spec in a B2B category.
It tells you how to first check whether the spec belongs in this category,
then evaluate each existing option (keep, reject, or merge), identify new
options to add, and apply structural fixes. You produce the validation output
yourself using this reasoning framework.

---

## Step 0 — Check spec relevance before touching options

Before auditing any option, ask: **does this spec belong in this category at all?**

A spec can have filled options while being fundamentally wrong for the category.
Cleaning its options would waste effort and leave a bad spec in place.

Ask these two questions:

**1. Does this spec describe a real property of products in this category?**
- A `Color` spec on Perfume Oils is valid — oil color is a real property.
- A `Gender` spec on Perfume Oils raw material is not — the formulator decides gender targeting for the finished product, not the oil supplier.
- An `Application` spec on a raw chemical ingredient is valid — buyers need to know what the ingredient is for.

**2. Do the options make sense for this specific spec in this category?**
- `Form: Liquid` on Perfume Oils is absurd — every product in the category is a liquid. The option is implied by the category itself.
- `Color: Red` on a Color spec for fabric is correct.
- `Motor Type: Servo` on a Protein Powder spec is a type mismatch — wrong category entirely.

**How to measure Step 0:**
Use fill rate data as the primary signal here, since impressions and call data are only reliable once you are inside the spec. Calculate what share of filled listings use the most common single value. If 95%+ of products share the same value, or if all options show fill rate below 5%, the spec is a gate-fail candidate.

**If spec relevance is in doubt:**
- Flag it explicitly: *"Spec relevance questionable — [reason]. Recommend reviewing whether this spec should exist before auditing its options."*
- Apply the `domain_expert` skill to validate relevance.
- Use `[WEB_SEARCH]` if you cannot resolve doubt from domain knowledge alone.
- Do not silently proceed with option cleaning on a potentially invalid spec.

**Spec failure conditions — flag and stop if any apply:**
- 95%+ of filled listings share the same value
- All options have fill rate below 5% (sellers do not recognise the spec)
- No impressions and no buyer call data across all options
- Options fail category-spec fit across the board

If any condition above is met, output: *"Spec structurally weak — recommend removal or redesign."* Do not proceed with option cleaning.

**If spec is relevant:** proceed to Step 1.

---

## Step 1 — The three option-level signals you have

These are one level deeper than spec-level signals. A spec can have healthy overall
fill rate while individual options within it are completely unused.

**Option Fill Rate (from Option Fill Rate Data)**
Percentage of listings using this specific option value. High means sellers actually
select this option. Low means sellers ignore it or cannot find it. This signal is
noisy — low fill can reflect a bad UI or a missing option, not irrelevance.

**Option Impressions (from Buyer Search Data)**
How many times buyers filtered by this specific value in search. High means buyers
actively look for this value. Low means buyers do not care about or cannot find it.

**Option Product Count (from Buyer-Seller Call Data)**
How many times this specific value appeared in real buyer-seller phone calls.
High means discussed in actual transactions. This is the most reliable signal.

**Signal priority when signals conflict: Buyer Calls > Search Impressions > Fill Rate.**

**Signal thresholds:**

| Signal        | Strong | Moderate | Weak |
| ------------- | ------ | -------- | ---- |
| Fill Rate     | ≥20%   | 5%–19%   | <5%  |
| Impressions   | ≥5     | 3–4      | <3   |
| Product Count | ≥10    | 3–9      | <3   |

---

## Step 2 — Audit existing options

Apply these rules in strict priority order. Stop at the first matching rule.

### Rule 1 — CATEGORY-SPEC MISMATCH (highest priority, no exceptions)

Reject immediately if the option value does not make sense for this spec in
this category — regardless of fill rate or any signal data.

Signal data cannot rehabilitate a mismatched option. High fill rate on a wrong
option only means sellers are selecting it because no correct option exists.
Remove it and add the correct value instead.

Reject if the option is:
- **Type mismatch** — a numeric value (e.g. `25 mm`, `120 GSM`) under a Color spec; a color value (e.g. `Red`) under a Size spec; a weight under a Brand spec; a brand name under a Color spec
- **Implied by category** — the option describes what every product in the category already is (e.g. `Form: Liquid` in Perfume Oils; `Type: Servo` in AC Servo Motor). Reject only when 95%+ of products share this value AND it is inherent to the category definition, not a coincidental majority.
- **Wrong category entirely** — the option belongs to a different category (e.g. `Motor Type: Servo` appearing under a Protein Powder spec)
- **Brand leakage** — a brand name appearing under a non-Brand spec (e.g. `Tata Steel` under Material; `Bosch Blue` under Color)

### Rule 2 — ABSURD OPTIONS

Reject immediately regardless of signals:
- Junk or gibberish — `asdf`, `xxx`, `123abc`, `multimedia speaker`
- Test or placeholder data — `test`, `sample`, `demo`, `NA`, `N/A`, `nil`, `-`, `.`
- Vague filler — `As per requirement`, `Customized`, `Standard`, `Other`, `General`, `Miscellaneous`, `Any`
- Excessively long — more than 50 characters
- Promotional text — `Best Quality`, `Premium Grade`, any URL

### Rule 3 — STRONG SIGNAL → KEEP

Keep the option if any of these are true:
- It appears in 2 or more independent signal sources (call data + fill rate + search)
- Option fill rate is 20% or higher
- Product count is 10 or higher (came up in 10+ buyer calls)

### Rule 4 — MODERATE SINGLE SIGNAL → KEEP

Keep if the option appears in exactly one signal source AND the value is clearly
valid for this spec and category. Any non-zero impression count is sufficient for
a clearly valid option.

**When signals are ambiguous** — fill rate 5%–19% with no impressions and no call
data, or impressions of 3–4 with no other signal — do not auto-keep or auto-reject.
Flag the option for human review: *"Uncertain — insufficient signal, requires review."*

### Rule 5 — SEMANTIC OVERLAP

When two options represent the same concept in different words, keep the most
standard B2B industry term and reject the vague or marketing variant.

Examples:
- `Heavy Duty` / `Industrial` / `Commercial` → keep `Industrial` (most standard B2B term)
- `Food Grade` / `Food Safe` / `FSSAI Approved` → keep `FSSAI Approved` (regulatory standard)

Document which term was kept and why so the decision is auditable.

### Rule 6 — MERGE DUPLICATES

When two options represent the same real value in different formats, merge them
into one canonical form.

Common merge situations:
- Unit spacing: `3mm` → `3 mm`
- Capitalisation: `blue` → `Blue`
- Spelling variants: `Aluminium` / `Aluminum` → use Indian B2B standard form
- Abbreviated vs full: `GI` vs `Galvanized Iron` → keep whichever Indian B2B uses

Merge rules:
- Always merge toward the cleaner, more standardised form
- If two formats have equal standing, prefer the one with the higher product count
- The merge target must already exist in the option list or be created as a new canonical option
- After merging, the absorbed option is removed; the canonical form is kept

---

## Step 3 — Add new options from your data

Beyond auditing existing options, identify values from your data that should be
added but are missing from the current option list.

Sources to check for new option candidates:
- Buyer call example values (Buyer-Seller Call Data) not present in current options
- Buyer search filter values with meaningful impressions (Buyer Search Data) not in current options
- Custom spec option values sellers submitted (Custom Seller Specs) not in current options

Every candidate new option must pass all of these before you add it:

| Check | Requirement |
|-------|-------------|
| Category-spec fit | Value makes sense for this spec in this specific category |
| Type match | Value is the correct type for this spec (not a mismatch) |
| Not a duplicate | Not a variant of something already in the list |
| Not junk | Not a placeholder, vague filler, or promotional text |
| Standardised form | Correct units, Title Case for text, compact numeric format |
| At least 1 signal | Evidence from at least one data source |

**When uncertain about a candidate option:**
Use domain knowledge first. If still unresolved, validate against a trusted external
source — BIS (Bureau of Indian Standards) for Indian market standards, ISO for
internationally standardised specs, or industry trade catalogs such as IndiaMart
category listings or manufacturer datasheets. Use `[WEB_SEARCH]` to reach these
sources. Apply the `domain_expert` skill to interpret what you find. Do not add an
option you cannot validate.

---

## Step 4 — Fix structural problems

**Mixed units in one list**
Options mixing `mm` and `inches` for the same spec. Standardise to Indian B2B
convention — metric for most categories. Convert or remove non-standard units.

**Numeric explosion**
More than 15 distinct numeric options. Convert to ranges for continuous values,
or change the spec to `text_type` if values are too varied to band cleanly.

**Overlapping ranges**
Options like `< 1 kg`, `0.5–1 kg`, `< 500g` create ambiguity. Consolidate into
clean, non-overlapping ranges that cover the real distribution.
Example: `< 0.5 kg`, `0.5–1 kg`, `1–5 kg`, `> 5 kg`.

**Too many options**
More than 25 options after cleaning. Consolidate into groups or convert to ranges
or `text_type`.

**Wrong input type — fix this:**
- Spec has only 2–3 mutually exclusive values using `multi_select` → change to `radio_button`
- Spec has values that can apply simultaneously using `radio_button` → change to `multi_select`
- Spec has model numbers, free-form dimensions, or brand names with no dominant standard values → change to `text_type` with empty options list

**Too few options**
A `radio_button` spec with only 1 option is useless as a filter. Find more real
values from your data or change to `text_type`.

---

## What low option fill rate actually means — do not auto-reject

Low fill rate on an option does not automatically mean remove it. Diagnose first:

| Situation | What it means | Correct action |
|-----------|--------------|----------------|
| Option is niche but valid | Rare but legitimate product variant | Keep if any product count or impressions support it |
| Option type is wrong | Sellers can't map their product to it | Remove — add correct version |
| Option is vague filler | Sellers skip it because it's meaningless | Remove |
| Option was recently added | Not enough time for fill data | Keep — flag for future review |
| ALL options have low fill | The spec itself may be broken | Flag as a spec-level issue — do not silently empty the option list |

To distinguish a niche-but-valid option from a wrong one: if the option represents
a real product property that exists in the Indian B2B market and can be verified
through domain knowledge or an external source, keep it. If it is vague, cannot
be verified, or does not describe a real product attribute, reject it.

---

## Formatting rules — apply when adding or correcting options

| What | Standard | Wrong forms |
|------|----------|-------------|
| Units | `kg`, `mm`, `V`, `W`, `A`, `rpm`, `°C`, `%`, `L`, `mL`, `Hz` | `kgs`, `MM`, `Volt`, `Watts`, `Amps` |
| Numeric format | Compact with space: `12 V`, `120 GSM`, `3 mm` | `12Volt`, `120GSM`, `3mm` |
| Text | Title Case | ALL CAPS, all lowercase |
| Numeric order | Ascending | Random |
| Categorical order | Most common in Indian B2B first, then alphabetical | Alphabetical only |
| Indian trade terms | Use `GI`, `MS`, `PP`, `HDPE`, `ISI` | Expanded forms when abbreviated forms dominate |

---