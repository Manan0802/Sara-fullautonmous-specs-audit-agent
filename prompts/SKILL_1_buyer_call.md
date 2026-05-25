# buyer_call_analysis


## What this skill is for


When you read the Buyer-Seller Call Data (Buyer-Seller Call Data) output — use this document to
understand what the data means, how to interpret each field, what signals are
reliable vs misleading, and how to use the findings in your audit decisions.
You apply this interpretation yourself — no separate process runs.


---


## What this data source is


Buyer call data contains spec-value pairs extracted from real phone conversations
between buyers and sellers on the marketplace. When a buyer calls a seller and says
"I need 3mm thickness, powder coated finish, 6 metre length" — those three
attributes get logged as spec-value pairs for that product.


This is your highest-confidence signal. It captures what people actually negotiate
on, not what they search for on a screen or what sellers bother filling in a form.
If something comes up repeatedly in buyer calls, it is genuinely important to the
transaction.


---


## What the fields mean


**spec_name**
The normalised name of the spec discussed. If the data pipeline corrected a raw
seller input (e.g., mapped "thicness" → "Thickness"), the corrected name appears
here. This corrected form is the market-standard name — if your current spec uses
a different form, that is a rename candidate.


**total_product_count**
The number of products where this spec was discussed in calls. This is your proxy
for transactional importance. Sum across all values for a spec to get its overall
weight. Higher count = more buyers and sellers consider this attribute essential
to close a deal.


**example_values**
The actual values sellers quoted during calls. These are ground-truth option values
from real products in the real market. Any value appearing here but absent from the
current spec's option list is a strong candidate for addition.


**correction_applied**
A flag indicating whether the pipeline normalised the raw input. When true, the
spec_name shown is the corrected, standardised form. If your current spec uses the
raw/old form, this is a signal to rename or correct.


---
### Spec-level count (use to judge whether a spec matters)


Product count is relative. Do not use absolute thresholds. Instead, read the full
distribution of spec counts in the category and let the shape guide you:


- Rank all specs by total product count, highest to lowest
- Specs that cluster near the top are the attributes buyers consistently negotiate on — treat as strong signals
- Specs that sit far below the top cluster, with a visible drop-off from the rest, are weak signals — treat as directional only
- Specs at the very bottom of the distribution, especially those markedly separated from even the mid-range specs, are noise — do not act on them alone


The key signal is the **gap between high-count and low-count specs** within the same category. A spec is weak not because it falls below a fixed number, but because the distribution reveals it as an outlier relative to its peers.




### Option-value count (use to judge whether a specific value matters within a spec)

Within a given spec, individual option values also carry their own product counts.
Not every value that survives the 90% filter is equally worth adding — some may
represent fringe usage or data noise within an otherwise valid spec.

Apply relative logic within each spec's own value distribution:

- Rank all values for a spec by their product count, highest to lowest
- Values that cluster near the top of this distribution are the dominant market options — treat as strong candidates
- Values that sit far below the top cluster, with a visible drop-off from the rest, are tail values — treat as noise and ignore unless corroborated by another source
- If the counts across all values are similarly low with no clear leaders, the entire value set is weak — do not act on any individual value; the spec itself may be too thin to evaluate
- If a spec has very few total products (count < 3), do not evaluate individual values at all — the spec itself is too weak to act on


The key signal is the **gap between the high-count values and the low-count values** within the same spec. A value is noise if its count is markedly lower than the leading values in that spec — not because it falls below some fixed number, but because the distribution itself reveals it as an outlier.

If an individual option value has a product count < 3, treat it as noise and ignore it — do not add it to the option list, even if the parent spec is strong.


This prevents low-frequency outliers from inflating option lists with values that almost no buyer in the category actually negotiates on.




---


## What high product count actually means


High product count means buyers and sellers discuss this attribute when transacting.
It does NOT automatically mean the spec is missing from your platform — it may
already exist under a different name.


Before treating a high-count call spec as a missing spec, ask:
1. Is this spec already in the current spec list under the same name? → Already covered
2. Is this spec already in the current spec list under a different name? → Duplicate, consider rename
3. Does the category name already define this value for every product? → Implied, do not add
4. Is this a physical product attribute, or a commercial/logistics term? → If commercial, not a product spec


Only after checking all four should you pass it to missing spec reasoning.


---


## Signal classification — apply to every call spec before acting


| Classification | When it applies | What to do |
|---------------|----------------|------------|
| `VALID_SPEC` | Distinct filterable attribute with discrete values, not already in spec list | Investigate further — strong candidate |
| `IMPLIED` | Category name already defines this value for every product in the category | Do not add. If it exists in Primary, consider demotion |
| `DUPLICATE` | Same attribute as an existing spec under a different name | Merge with existing spec, do not add new |
| `NOT_A_PRODUCT_SPEC` | Delivery terms, payment, packaging, MOQ, warranty | Ignore entirely |
| `COMPOSITE` | Combines values from two specs (e.g., `10x20x5 mm`) | Break into components before evaluating |


---


## How to use call data in your audit


**To establish importance baseline**
At the start of your audit, read the full call data and rank specs by total_product_count.
This ranking tells you which attributes genuinely drive purchase decisions in this
category. Use it to calibrate every tier and importance judgment you make.


**To find missing specs**
Specs that appear in call data but are absent from the current spec list are
candidates for addition. Apply signal classification first. Require product count
above 2 before treating as a genuine gap signal.


**To validate current spec tiers**
A current Primary spec with near-zero product count in call data is suspicious.
Low call signal + low fill rate together = strong candidate for demotion or removal.
Call data is your check on whether the existing tier hierarchy reflects real buyer behaviour.


**To find option gaps**
Example values from call data are ground-truth option values. Compare them against
your current option lists. Values that appear in calls but not in current options
are strong candidates for addition — pass to option validation reasoning with this
as supporting evidence.


**To confirm cross-source signals**
When the same spec appears in both call data AND custom specs (Custom Seller Specs), that is two
independent signals pointing at the same gap. This combination reaches high confidence
for a missing spec addition.


---


## What call data cannot tell you alone


- **Whether a spec is missing** — it shows what is discussed, not what is absent.
  Always cross-check against the current spec list before concluding something is missing.
- **Final tier placement** — product count is one of three signals. You need fill rate
  (Spec Fill Rate) and search impressions (Buyer Search Data) to make a well-supported tier decision.
- **Option quality** — call data shows which values exist in the market, not whether
  your current option list is structurally correct. Bring these values to option
  validation reasoning for the full assessment.
   counts because every product has a material, not because Material is a differentiator.

---

