# buyer_search_analysis


## What this skill is for


When you read the Buyer Search Data output — use this document to understand
what impression counts mean, how to classify each search signal, and how to use
search findings in your audit decisions. You apply this interpretation yourself —
no separate process runs.


---


## What this data source is


Buyer search data contains spec-option combinations that buyers selected as filters
when searching the marketplace, along with impression counts showing how many times
each filter was used. When a buyer clicks "Thickness: 3mm" as a search filter, that
generates one impression for that spec-option combination.


This data tells you what buyers actively want to narrow their search by. High
impressions mean many buyers are expressing demand for this attribute as a filter.
It is your most direct measure of buyer intent on the platform.


---


## What the fields mean


**spec_name**
The name of the spec buyers used as a filter. May not match the platform spec name
exactly — use semantic matching, not exact string matching. "Wattage" and "Power"
refer to the same buyer intent.


**spec_option / option value**
The specific value buyers filtered by. Values appearing here but absent from your
current option list are strong candidates for addition.


**impression / total_impressions**
How many times buyers used this spec-option combination as a filter. Your primary
signal from this data source. Higher = more buyer demand.


---


## How to read impression counts — orientation thresholds


These are not hard rules — calibrate relative to the distribution in your category.


| Total impressions for a spec | Signal strength |
|-----------------------------|-----------------|
| Below 50 | Noise — do not act on this alone |
| 50 to 500 | Weak — needs corroboration from another source |
| 500 to 2000 | Moderate — worth investigating, check for artifacts |
| Above 2000 | Strong — genuine buyer demand |


A spec with 200 impressions that also appears in call data is stronger evidence than
a spec with 1000 impressions that has zero product count and looks like a UI default.
Always cross-reference.


---


## The two types of specs in search data


**Present specs** — Buyers are using a spec the platform already has. High impressions
for a present spec validate that it belongs where it is. Very high impressions for a
present Tertiary spec is a signal it may be misplaced.


**Missing specs** — Buyers are filtering on an attribute the platform does not offer
as a standardised spec. These are discovery gaps — buyers are either finding no
results or settling for imprecise results. High-value candidates for addition.


Use semantic matching when classifying — "Wattage" is present if the platform has
"Power". The buyer intent is the same regardless of the label difference.


---


## Signal classification — apply to every search spec before acting


Not every high-impression term should become a spec. Classify first:


| Classification | When it applies | What to do |
|---------------|----------------|------------|
| `VALID_SPEC` | Distinct filterable attribute, impressions ≥ 50, not already covered | Addition candidate |
| `CONTEXT_TERM` | A word describing context or setting, not a filterable attribute | Do not add |
| `IMPLIED` | Category name already defines this value for every product | Do not add — artifact |
| `DUPLICATE` | Semantically same as an existing platform spec under a different name | Do not add — already covered |
| `NOT_A_PRODUCT_SPEC` | Delivery, payment, warranty, MOQ | Do not add |
| `DATA_ARTIFACT` | One option has over 90% of impressions, or known default UI filter | Do not promote based on this alone |


**Category-implied check — apply every time:**
If the category name itself tells you the value of this spec for every product,
buyer impressions are an artifact. Example: buyers searching "Material: Aluminium"
in an Aluminium Profiles category are not expressing a new spec need. Every product
is already aluminium. The impressions come from the filter existing, not from genuine
buyer differentiation need.


**Data artifact check — apply when impressions look disproportionate:**
- Does one option account for over 90% of total impressions for this spec?
- Is this likely a default filter the platform pre-selects for buyers?
- Does product count in call data = 0 despite very high impressions?


If yes to any of these, tag as `DATA_ARTIFACT` and do not promote based on this signal.


---


## How to use search data in your audit


**Finding discovery gaps**
Search for specs classified as missing with impressions above 50. These are attributes
buyers want to filter on but the platform does not offer. High-priority addition
candidates. Cross-reference with call data and custom specs before adding.


**Validating tier placement**
A spec currently in Tertiary with thousands of impressions is almost certainly
misplaced. Bring this signal into your sequencing reasoning alongside fill rate
and product count.


**Finding option gaps**
When buyers filter by a specific value that does not exist in the current option list,
that is a direct signal to add that option. Example: "48V" appearing in search but
absent from the Voltage spec options. Bring to your option validation reasoning with
this as evidence.


**Cross-source confirmation**
A spec appearing as missing in search AND in call data is confirmed from both the
demand side (buyers want to filter) and the transactional side (buyers and sellers
discuss it). This combination reaches high confidence for addition.


---


## What search data cannot tell you alone


**Whether a spec is genuinely missing** — High impressions may reflect an artifact,
a context term, or a spec that already exists under a different name. Always classify
before acting.


**Final tier placement** — Impressions are one of three signals. You need fill rate
 and product count  to make a well-supported tier decision.


**Option quality** — Search data shows which values buyers look for, not whether your
current option list is structurally correct. Use these values as evidence in your
option validation reasoning.


**Why impressions are high** — Search data shows that buyers filtered on something,
not why. A spec with 5000 impressions could be a genuinely important attribute or
a default UI filter every buyer sees. Investigate before acting.

