# spec_sequencing


## What this skill is for
When you need to decide whether a spec belongs in Primary, Secondary, or Tertiary —
read this document. It tells you how to assess tier placement using the signals
available to you, how to resolve conflicts, and what rules override signal data.
You produce the sequencing output yourself using this reasoning framework.


---

## The three signals you have and what they mean
You have three quantitative signals for every spec. Use all three together — no
single signal is enough on its own.


**Fill Rate (from Spec Fill Rate)**
The percentage of seller listings where this spec is filled. High fill rate means
sellers consider it important enough to describe. Weakness: can be inflated if the
spec was marked mandatory at some point, or if sellers fill it out of habit without
buyers caring.


**Search Impressions (from Buyer Search Data)**
How many times buyers used this spec as a filter in search. High impressions means
buyers actively want to narrow results by this attribute. Weakness: default UI
filters and specs that restate the category name (e.g. "Material: Aluminium" in
an Aluminium category) can inflate this artificially.


**Product Count / Call Count (from Buyer-Seller Call Data)**
How many times this spec was discussed in real buyer-seller phone conversations.
High count means it comes up during actual purchase negotiations. Weakness: implied
specs get discussed a lot simply because every product has the same value — this
is noise, not signal.


---


## How to calibrate "high" vs "low"


Do not use absolute thresholds. Compare each spec's signals against the other specs
in the same category. The spec with the highest fill rate is "high fill rate" — even
if that number is 45%. The spec with the lowest impressions is "low impressions" —
even if that number is 200. Always calibrate relative to the distribution in front of you.


---


## Convergence logic — how signals combine into a tier


| Signals agreeing | Convergence | Starting point |
|-----------------|-------------|----------------|
| 2 or 3 signals high relative to peers | STRONG | Primary or high Secondary |
| 1 signal high, others medium | MODERATE | Secondary |
| 1 signal high, others low | MODERATE-WEAK | Low Secondary or Tertiary |
| 0 signals high | WEAK | Tertiary |


When signals conflict, apply the conflict resolution rules below before deciding.


---


## Conflict resolution — what to do when signals disagree


**High Impressions + near-zero Product Count**
Buyers filter on it but sellers and buyers don't discuss it in calls. Usually means
the spec is a UI default filter, or it re-states something already obvious from the
category name. Do NOT auto-promote to Primary. Check whether the category name
already implies this attribute. Cap at Secondary pending domain validation.


**High Product Count + near-zero Impressions**
Comes up in negotiations but the platform doesn't surface it as a prominent filter.
The spec matters transactionally but isn't discoverable through search. Worth
Secondary. Can be Primary if it's the dominant signal by a clear margin and domain
logic supports it.


**High Fill Rate + low Impressions + low Product Count**
Sellers fill it consistently but buyers don't search for it or discuss it much.
Seller-oriented spec. Default to Secondary. Only demote to Tertiary if it's
single-value across all products or is directly implied by the category name.


**All three high**
Strongest Primary candidate. Place here unless an override rule applies.


**One source anomalously high, others low**
Investigate the inflation cause before deciding. One anomalous signal does not
override two low signals. Apply DATA_ARTIFACT check below.


---


## Override rules — these take priority over signal values


Apply these before finalising any tier placement.


### IMPLIED
**When it applies:** The category name already fixes this spec's value for every
product. Examples: "Inverter Type: Solar" in a Solar Inverter category. "Fabric:
Cotton" in a Cotton Fabric category. "Material: Aluminium" in an Aluminium Profiles
category.


**How to detect it:** The category name contains or directly implies the dominant
value of the spec. Nearly all example values match that implied value. High signals
are artifacts — every product in the category has this value, so of course it appears
everywhere.


**What to do:** Demote to Tertiary or remove entirely if it adds no differentiation
across products. Tag reasoning with [IMPLIED].


### DATA_ARTIFACT
**When it applies:** Signal numbers are inflated but don't represent genuine buyer
choice. Key cases:
- Brand spec where example values are all generic ("Local", "Unbranded", "As required")
- One option accounts for over 90% of all impressions for this spec
- Very high impressions combined with zero product count in calls
- Fill rate disproportionately high relative to search and call signals


**What to do:** Do not promote based on this signal. Investigate before deciding.
Use domain knowledge to determine if the signal is genuine. Tag reasoning with
[DATA_ARTIFACT].


### WEAK_EVIDENCE
**When it applies:** Impressions = 0 AND Product Count < 5, OR Fill Rate < 15% AND
Product Count < 3, OR example values are empty or single-value across all products.


**What to do:** Keep in Tertiary. Do not place in Primary or Secondary without
strong domain justification stated explicitly. Tag reasoning with [WEAK_EVIDENCE].


---


## Tier definitions — the tests to apply


**PRIMARY — hard maximum 3 specs**


A buyer cannot meaningfully describe what they want without this spec. A seller
cannot create a findable listing without this spec.


Ask yourself:
- What does a buyer say in the FIRST sentence when asking for this product?
- What do sellers fill first to make a listing appear in search?
- Is this a core attribute that defines what the product IS, not just describes it?


If yes to all three → Primary candidate.


Prefer radio_button input types in Primary. Multi-select can be Primary only if
the category genuinely requires multiple simultaneous values — justify this
explicitly if you choose it.


**SECONDARY — maximum 3 specs**


Determines whether a specific variant works for the buyer. Distinguishes one SKU
from another within the category.


Ask yourself:
- After confirming the Primary specs, what does the buyer ask about next?
- What separates one variant from another within this category?
- Would removing this spec from the listing make it harder to find the right variant?


If yes → Secondary candidate.


**TERTIARY — remaining specs, no hard maximum**


Helpful for final differentiation. Provides complete product information but is not
critical for discovery or purchase decisions.


Ask yourself:
- Would the buyer still find the right product without this spec?
- Is this a detail that matters only after the purchase decision is largely made?


If yes to either → Tertiary.


---


## When to re-sequence after other changes


**After option fixes:** If a spec had broken options, its fill rate and search
impressions may have been artificially depressed. After options are corrected,
re-assess that spec's tier — the real signal may be higher than the data showed.


**After adding new specs:** Adding specs changes the relative importance landscape.
Always re-assess the full tier balance after additions.


---


## Tier overflow — what to do when limits are breached

**Primary overflow:** If more than 3 specs qualify for Primary, demote the weakest — lowest convergence, or an override tag present — to Secondary. If Secondary is also full, demote to Tertiary. Document the decision.

**Secondary overflow:** If more than 3 specs qualify for Secondary, demote the weakest to Tertiary. Document the decision.

One spec, one tier. No ties, no shared ranks.

---
