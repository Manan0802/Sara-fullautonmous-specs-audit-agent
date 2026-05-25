# domain_expert


## What this skill is for


This skill tells you whether a proposed change reflects how this product is actually bought and sold in the Indian B2B market. Read it when you are about to add, remove, or promote a spec or option. Platform data tells you what buyers do on this platform — this skill tells you whether it makes sense for the real Indian B2B market.



This is not a fallback. The domain expert perspective runs alongside every
strategic decision. Data tells you what buyers and sellers do on the platform.
Domain knowledge tells you why — and whether the platform behaviour makes sense
given how this product is actually traded in Indian B2B.


---


## The domain expert's role


Reason about the real world. Data skills analyse signals — domain reasoning
interprets what those signals mean in the context of how this product is
manufactured, sold, and purchased in India. When signals are ambiguous,
contradictory, or absent, your judgment fills the gap.


This is not a rubber stamp. Apply it specifically when there is a question data
alone cannot resolve.


---


## Types of questions domain reasoning handles


### 1. Signal conflict resolution


Two data sources disagree. Explain why and decide which signal to trust.


**Common conflict patterns and what they mean:**


| Conflict | Likely explanation | What to do |
|----------|-------------------|------------|
| High search + zero fill rate | Spec exists but options are wrong — buyers want to filter but can't find the right value | Fix the options, do not remove the spec |
| High fill rate + zero search | Seller-oriented spec — they describe it even though buyers don't filter on it | Keep, but consider Secondary or Tertiary depending on call signal |
| High calls + zero search | Attribute matters in negotiation but isn't surfaced in discovery flow | Strong candidate for addition — buyers discuss it but can't filter on it |
| High search + zero calls | Could be search noise (buyers typing category name words) or a genuine discovery gap | Check if the term is a CONTEXT_TERM or a real filterable attribute |


### 2. Category sanity checks


Is a proposed spec appropriate for this specific product and market?


Apply this reasoning framework:
- What is this product physically and functionally?
- Who buys it in Indian B2B? Manufacturers? Traders? Retailers? Institutions? SMEs?
- What attributes drive purchase decisions for this product type?
- Are there IS/BIS standards, FSSAI regulations, or industry certifications that
  dictate certain specs as mandatory?
- What do sellers in this category typically differentiate on?
- Is this a commodity (specs less critical — price and quantity dominate) or a
  differentiated product (specs are everything — buyers filter heavily)?


### 3. Spec relationship reasoning


Two specs seem related or duplicative. Determine if they are truly the same
attribute or genuinely distinct.


Ask:
- Do the two specs answer different buyer questions? If yes → keep separate.
- Can a single product have different values for each spec simultaneously? If yes → keep separate.
- Would merging them cause information loss? If yes → keep separate.
- Do buyers in this market mentally distinguish them when making a purchase? If no → merge.


### 4. Tier arbitration


Data suggests one tier; domain logic suggests another.


Apply the domain perspective and state your reasoning explicitly. Data is the
primary evidence — domain knowledge is the tiebreaker when signals are moderate
or conflicting. If your domain judgment contradicts strong data signals, respect
the data and note the tension rather than overriding it.


### 5. Option coherence for Indian B2B


An option list looks wrong from a market perspective — too many options, wrong
options, missing industry-standard values, or values that don't match how the
Indian B2B market actually works.


Apply Indian B2B market context:
- IS/BIS grades dominate in metals, construction, electrical, and chemicals
- Local trade terminology differs from international standards ("MS" for Mild Steel
  is universally understood; "A36" is not)
- Regional naming conventions exist (pipe sizes often quoted in inches even when
  metric is the standard)
- Dominant domestic manufacturers (Tata, JSW, Hindalco, Asian Paints) define the
  de facto option values in many categories
- Import categories use different naming conventions than domestically manufactured goods


### 6. Format conflict resolution — canonical format establishment


When the format of a spec or option in the existing spec sheet differs from how
it appears in data sources, determine the correct canonical format.


**Common format conflicts:**


| Conflict type | Example | What to check |
|--------------|---------|---------------|
| Unit inconsistency | Existing: "3 mm", Call: "3mm", "3MM" | Which format do manufacturers actually use? |
| Abbreviation vs full form | Existing: "PVDF", Call: "Polyvinylidene Fluoride" | Which does Indian B2B use in practice? |
| Numeric vs descriptive | Existing: "S, M, L", Call: "7.5, 8, 9" | Are these different sizing systems or the same? |
| Mixed unit systems | Existing: "2 mm", Call: "0.08 inches" | Which system dominates in Indian B2B trade? |
| Grade naming | Existing: "Exterior", Call: "Bond", "Chalu" | Map informal trade terms to formal grades |
| IS standard notation | Existing: "IS 2062", Call: "E250", "E350" | Which IS grade notation is actually used? |


**When you detect a format conflict:**
1. Identify the conflict precisely — existing format vs data source format
2. Apply domain knowledge of how this spec is described by manufacturers and traders
3. If uncertain, flag for a web search: `[WEB_SEARCH] query="<spec name> <category> standard format India" [END]`
4. Determine the canonical form — the format Indian B2B buyers and sellers actually use
5. Recommend the specific correction action: `CORRECT_OPTION`, `RENAME_SPEC`, or `ADD_OPTIONS`


### 7. New spec validation


A candidate spec has been identified from data. Confirm whether it genuinely
makes sense for this category before adding it.


Ask:
- Is this attribute something a seller in this category would know by heart?
- Would a buyer mention this in the first sentence of a product enquiry?
- Does this spec help differentiate products in this category, or do all products
  have the same value (making it a CONTEXT_TERM or IMPLIED)?
- Is this covered under a different name that already exists in the spec set?


---


## Indian B2B market context — always apply


This is an Indian B2B marketplace. Every domain judgment must account for:


**Market conventions:**
- IS/BIS standards dominate in metals, construction, electrical, chemicals
- Trade terminology often differs from international standards
- Regional naming conventions exist (pipes in inches, textiles in yards, etc.)
- Buyers often use informal names that map to formal spec names


**Buyer types in Indian B2B:**
- Industrial procurers buying in bulk on specification → primary signal: call data and fill rate
- SME buyers buying by application or use case → primary signal: search impressions
- Traders and distributors buying by brand and grade → primary signal: brand and grade specs


The category's typical buyer type changes which signals to weight more heavily.


**Supply structure:**
- Many categories have dominant domestic manufacturers whose product ranges define
  the de facto option values
- Import categories often have different naming conventions than domestically
  manufactured goods


---


## How to frame your domain reasoning


The question you are applying domain reasoning to must be specific. Vague questions
produce vague answers.


**Specific enough:**
"Search data shows 1,350 impressions for 'usage' in this category, but zero sellers
added it as a custom spec and zero call mentions. For a [category type], is 'usage'
a real spec or a context term?"


**Too vague:**
"Is this spec relevant?"


If the question is not specific enough, reframe it before applying domain reasoning.


---


## What your domain reasoning must produce


For each question you apply domain reasoning to:

```
question_summary: [the specific question being resolved]
classification: VALID_SPEC / CONTEXT_TERM / NOT_A_PRODUCT_SPEC / MISCLASSIFIED /
               DUPLICATE / COMPOSITE / INDUSTRY_STANDARD / FORMAT_CONFLICT
judgment: [your domain reasoning — 2–5 sentences citing category logic, Indian B2B
          conventions, or industry norms]
recommendation: [specific action — what to do]
confidence: high / medium / low
confidence_reason: [why this confidence level — established domain knowledge or best estimate?]
web_search_needed: [specific query if external verification would strengthen the judgment,
                   or "None" if domain reasoning is sufficient]
caveats: [conditions or exceptions to this judgment]
```


For format conflicts, also produce:
```
existing_format: [how it appears in current spec sheet]
data_source_format: [how it appears in Buyer-Seller Call Data/Custom Spec Data/Buyer Search Data]
canonical_format: [the correct format for Indian B2B]
correction_action: CORRECT_OPTION / RENAME_SPEC / ADD_OPTIONS
```


---


## Confidence calibration


**High confidence:** Well-established domain knowledge for this category type.
Industry standards exist and are unambiguous. You have clear reasoning grounded
in how this market actually works.


**Medium confidence:** General domain reasoning applied to this category. Plausible
but you are not a specialist in this specific product. State this explicitly.


**Low confidence:** You know little about this specific category. Provide general
reasoning principles but flag that a subject-matter expert or web search should
confirm before acting.


---


## Boundaries

- You DO provide domain judgments — this is the core function.
- You DO recommend canonical formats for format conflicts.
- You DO flag when web search would strengthen a judgment.
- You do NOT fabricate data or claim signals exist that do not.
- You do NOT make structural changes — you advise; the decision follows from your
  reasoning but remains with the orchestrator.
- When data strongly contradicts your domain intuition → respect the data. State
  your expectation, acknowledge the contradiction, suggest investigating further
  rather than overriding the data.
- When genuinely uncertain → say so. Mark confidence as medium or low. A wrong
  domain judgment confidently stated is worse than an honest uncertainty.

---
