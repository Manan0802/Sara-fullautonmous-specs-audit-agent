# custom_spec_analysis


## What this skill is for


When you need to identify spec gaps from seller-submitted custom specs — read this
document. It tells you how to interpret the custom spec data you have received,
how to classify each signal, and what to do with the findings. You apply this
reasoning yourself directly from the custom spec data in your context.


---


## Why custom specs matter


Custom specs are a direct market signal from the supply side. Sellers add custom
specs when the standardised spec system doesn't cover an attribute they need to
communicate to buyers. When a single seller adds a custom spec, it may be an edge
case. When 5, 10, or 20 sellers independently add the same spec under slightly
different names, it is a platform gap — the market is telling you something is
missing.


---


## The data you have (Custom Spec Data)


Your custom spec data contains seller-submitted specs filtered for this category.
Each row tells you:
- `spec_name` — what the seller called the spec (may be messy, abbreviated, variant)
- `option_value` — what value the seller entered
- `count` — how many sellers submitted this spec name


The raw data is always messy. `WEIGHT`, `weight`, `Wt.`, `wt (kg)` may all be the
same attribute submitted by different sellers. Before using the data, mentally
normalise it:
- Unify casing to Title Case
- Expand abbreviations (`Qty` → `Quantity`, `Temp` → `Temperature`)
- Merge obvious variants (`Size`, `Dimensions`, `Product Size` → `Size`)
- Remove duplicates of existing platform specs


---


## The count threshold — your primary filter


**Count < 5 products:** Treat as noise. Too idiosyncratic to standardise. Classify
as `INSUFFICIENT_SIGNAL` and skip.

**Count 5–14 products:** Meaningful gap signal. Worth investigating further against
other data sources Buyer-Seller Call Data and Search Impressions before acting.

**Count 15–29 products:** Strong signal. High probability of a genuine platform gap.

**Count 30+ products with convergent option values:** Very strong — near-certain
standardisation candidate. Pass to missing spec reasoning with high confidence.


---


## How to classify each custom spec signal

Before acting on any custom spec, classify it:


**`VALID_SPEC`**
A distinct, filterable product attribute. Count ≥ 5. Not semantically covered by
any existing platform spec. Has discrete, real option values.
→ Strong addition candidate. Cross-reference with Buyer-Seller Call Data and Search Impressions before proposing.


**`DUPLICATE`**
Semantically the same as an existing platform spec despite a different name.
Examples: `Product Brand` when `Brand` already exists. `Colour` when `Color` exists.
→ Do not add. Note the naming inconsistency as an option to fix on the existing spec.


**`NOT_A_PRODUCT_SPEC`**
Business or logistics attributes — not physical product properties.
Examples: MOQ, Packaging Type, Delivery Time, Payment Terms, Warranty Period.
→ Ignore entirely. Do not pass to missing spec reasoning.


**`INSUFFICIENT_SIGNAL`**
Count < 5, or options are all blank, vague, or single-value.
→ Do not add. Note as weak signal in Skipped Gaps.


**`COMPOSITE`**
A single name that bundles multiple distinct attributes.
Example: `Size & Weight` combining dimensions and mass.
→ Break into component specs. Evaluate each component separately.


---


## How to use the option values sellers submitted


Seller-submitted option values are real market values — they show what actually
exists in the market for this attribute. But they are starting material, not a
final option list. They may be:
- Inconsistent in units (`kg`, `kgs`, `Kilogram`)
- Mixed in granularity (`3mm`, `3.0 mm`, `3 millimeter`)
- Contain some noise (vague entries, test data)


When you use these values to propose options for a new spec, apply the option
formatting rules from the Option Validator knowledge document. Clean them before
including them in your proposed spec.


---

## What your custom spec analysis must produce


After reading Custom Spec Data for this category, produce:


For each spec that passes the count threshold (≥ 5):
- spec_name — your normalised canonical name
- classification — VALID_SPEC / DUPLICATE / NOT_A_PRODUCT_SPEC / COMPOSITE / INSUFFICIENT_SIGNAL
- action — what to do: investigate further / pass to missing spec reasoning / ignore / note naming gap


For the overall Custom Spec Data summary:
- How many unique custom specs were found above threshold
- Which are strongest candidates (count ≥ 15)
- Which overlap with Buyer-Seller Call Data and Search Impressions signals (multi-source confirmation)


---


## What custom spec analysis does NOT determine


- Tier placement — count is not a sequencing signal. All new specs start at Tertiary;
  sequencing reasoning determines the final tier using fill rate, impressions, and
  product count
- Final option lists — seller-submitted values are starting material only; apply
  option validator reasoning before finalising
- Whether to add the spec — classification here is a recommendation; the missing
  spec addition reasoning makes the final add/reject decision

