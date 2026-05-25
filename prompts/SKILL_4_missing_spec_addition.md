# missing_spec_addition

## What this skill is for

When candidate missing specs have been surfaced by the Buyer-Seller Call, Custom Spec,
or Buyer Search skills — read this document. It gives you the framework to
validate whether each candidate is a genuine new spec or a false positive, and
if genuine, define it completely and correctly for the Indian B2B marketplace.

---

## Step 1 — Validate: Is this a genuine new spec?

A candidate missing spec is genuine only if all three of the following are true:

**1. It captures a real-world property not already covered**
The test is semantic, not textual. "Wattage" and "Power Rating" cover the same
property. "End Use" and "Application" cover the same property. "Make" and "Brand"
cover the same property. Do not compare names — compare what the spec is actually
measuring or describing. If any existing platform spec captures the same
real-world attribute, even approximately, the candidate is not a gap.

**2. It gives buyers information they cannot express using existing specs**
Ask whether a buyer could communicate the same product requirement using specs
that already exist. If yes, the candidate is not adding new information.

**3. It is atomic — not derivable from or decomposable into existing specs**
A spec that combines existing specs (e.g. "Size: 10×20×5mm" when Length, Width,
Height already exist separately) is not a gap. A spec that is a component of a
broader existing spec is not a gap.

If any of the three conditions is not clearly met, do not add the spec.

---

## Common false positives — check these before acting

**Naming variation across sources**
Data sources use different terminology for the same underlying attribute. Before
treating something as a gap, check whether it already exists under any common
synonym.

Common equivalences in Indian B2B:

| These terms often mean the same thing |
|---------------------------------------|
| Application / Usage / End Use / Purpose / Use Case |
| Finish / Coating / Treatment / Surface Treatment / Plating |
| Size / Dimensions / Measurement / Specification |
| Speed / RPM / Rotation Speed / Operating Speed |
| Power / Wattage / HP / KW / Rated Power |
| Colour / Color / Shade / Tint |
| Grade / IS Grade / ASTM Grade / Quality Grade |

**Composite attributes**
Some candidates are natural-language composites. "10mm HDPE pipe" → "10mm" is
not a new Diameter spec if Dimensions already exists.

**Category-implied attributes**
If the category name contains the attribute value, the spec has no differentiation
value. In "HDPE Tarpaulin", Material = HDPE is implied. High signal on such specs
is a data artifact.

**Multiple candidates meaning the same thing**
Before deciding how many specs to add, consolidate candidates that share the
same meaning. "Usage" from custom specs + "Application" from call data + "End Use"
from search → one spec, not three. Pick the most standard name and add once.

One underlying real-world property = one spec. Different names in different
sources is a normalisation artifact, not evidence of multiple gaps.

---

## Step 2 — Define: Build the spec completely

Once a candidate passes validation, define it fully across four elements.

### Spec Name
- Title Case, singular form, no trailing punctuation
- Use industry-standard terminology for this category
- Match the most common name from data sources
- Prefer the term a seller in this category would naturally use

### Input Type

**Platform rule for Primary and Secondary specs:**
On this platform, sellers can add their own custom option values on Primary and
Secondary specs beyond the list you define. This means you only need to define
the top market options — the platform handles edge cases. Do not choose
`text_type` for a Primary or Secondary spec just because the full universe of
values is large. If the top 10 market options are known, define them as
`radio_button`.

**`text_type` (options = []):**
Use only when no standard commercial values exist for this spec — meaning there
is no enumerable set of options that would cover the market, even partially.

- Model numbers, SKU codes, part numbers, serial numbers
- Free-form numerical values with no standard set — values that are unique per
  SKU with no market standard (e.g. exact protein per serving in grams, a
  precise torque value, a custom dimension)
- Specs where values are entirely seller-specific with no recognisable pattern
  across products

Do not use `text_type` simply because the option list is long or feels
incomplete. If the top options are known, use `radio_button`. If a spec has
well-known standard commercial values in the Indian B2B market, it should be
`radio_button` even if the data shows variation — variation is often data noise,
not evidence of infinite valid values.

**`radio_button`:**
- Single-choice attributes where a product has exactly one value
- Attributes with a known, enumerable set of market options
- Mutually exclusive states (Indoor / Outdoor)
- Single numeric ratings with standard market values (Voltage, Power, Speed)
- Boolean attributes: Yes / No. Options: `["Yes", "No"]`
- Use for Primary and Secondary specs wherever the top options can be defined —
  the platform's custom option entry handles values outside your list

**`multi_select`:**
- Attributes where one product can simultaneously have multiple values at the
  same time
- Test: can one product genuinely have more than one value simultaneously?
  If yes → `multi_select`
- Examples: Certifications (a product can hold ISO AND BIS AND CE at the same
  time), Dietary Features (Vegan AND Gluten-Free AND Sugar-Free simultaneously),
  Compatible With (a fitting compatible with multiple pipe types at the same time)
- Do not use `multi_select` for specs where a product has exactly one value,
  even if the universe of possible values is large. A protein powder has one
  protein source. A wire has one conductor material. These are `radio_button`.

---

### Options — How to Generate Them

Draw from example values in call data, custom spec submissions, and search
option values. When data values are sparse, inconsistent, or absent, generate
the full option set from Indian B2B market knowledge for this category and spec.

**Understanding option values from data sources:**

Option values surfaced by the data source skills vary significantly in quality.
Here is what each quality level looks like and what it tells you:

| Data Quality | What it looks like |
|---|---|
| Clean and consistent | Values are specific, formatted, and repeated across sources — reliable signal for what the real market options are |
| Mixed quality | Some specific values mixed with vague or inconsistently formatted ones — the specific values are the signal; the rest is noise |
| 1–2 values only | Too sparse to define the full option set — useful for confirming what the spec means, but market knowledge is needed to complete the list |
| Completely messy | No usable signal — generate entirely from Indian B2B market knowledge |
| Empty | No data at all — generate entirely from Indian B2B market knowledge |
| Contains NA / Other / Custom | These are non-values — ignore them and treat the remaining data at its actual quality level |

**Quality rules:**
1. No duplicates — "10 kg", "10kg", "10 Kg" are the same. One canonical form only
2. No vague fillers — never use: Other, Custom, NA, Various, As Required, Any,
   Miscellaneous, General Purpose
3. Under 30 characters per option
4. Standardised units — use: kg, mm, V, W, A, rpm, °C, %, L, mL, Hz.
   Never use: kgs, MM, Volt, Watts, Amps, Celsius
5. Limit to the 10 most common options for the Indian market

**Formatting rules:**
1. Compact numeric format — "12V" not "12 Volt"; "50Hz" not "50 cycles per second"
2. Title Case for text — "Stainless Steel" not "stainless steel" or "STAINLESS STEEL"
3. Numeric options in ascending order — 5mm, 10mm, 15mm, 20mm
4. Categorical options by frequency — most common in Indian market first
5. Use ISI/BIS standards where applicable
6. Use local trade terminology — "GI" for Galvanized Iron, "MS" for Mild Steel
7. Do not use range options unless they are the market standard for this spec

---

### Tier Placement

All new specs are added as Tertiary. Sequencing reasoning determines the final
tier based on actual signal data.

---
