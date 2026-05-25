---
# input-type-audit

## What this skill is for
  Use this skill to evaluate or correct the input_type of specs based purelyon the
  spec name and its existing option values — no data sources needed. Triggers: "wrong
  input type", "radio vs multi_select", "should this be text_type", or whenever options
  look mismatched with their input type.
---


## The three types
Understanding *why* each type exists is essential to making correct decisions.


### `radio_button`
**One and only one value applies to a given product at a time.**


The values are mutually exclusive by the physical or technical nature of the attribute.
A buyer filtering by one value correctly excludes all products with a different value.


Examples where `radio_button` is correct:
- Phase (Single Phase / Three Phase) — a motor cannot be both
- Voltage Rating (12 V / 24 V / 230 V) — a device has one rated voltage
- Material (MS / GI / Stainless Steel) — a pipe is made of one material
- Drive Type (Corded / Cordless) — a tool is one or the other
- IS Standard (IS 694 / IS 1554) — a product conforms to one standard


### `multi_select`
**Multiple values can simultaneously and legitimately describe the same product.**


A buyer selecting two values in a multi_select filter correctly retrieves products that
match either value. A seller legitimately selects more than one option for a single
listing.


Examples where `multi_select` is correct:
- Compatible Applications (Domestic / Industrial / Commercial) — a wire can be sold into all three markets
-  Certifications (ISI / CE / RoHS) — a product can carry all three marks
- Compatible Accessory Types (Drill Bits / Screwdriver Bits / Hole Saws) — a drill accepts multiple accessory families
- Suitable For (Indoor / Outdoor / Underground) — a cable can be rated for multiple
  installation environments


### `text_type`
**The value is free-form, unique per SKU, or has no stable, enumerable set of values.**


There is no finite list of options that meaningfully covers the real distribution.
Sellers need to type the value rather than select from a list. A buyer cannot usefully
filter by this spec — it is for display and comparison only.


Examples where `text_type` is correct:
- Model Number — every SKU has a unique identifier
- Catalogue Reference — brand-specific code with no standard pattern


---


## The two questions that decide the type


**1. Can a single product have two of these values at the same time?**
- No → `radio_button` (or `text_type` if free-form)
- Yes → `multi_select`


**2. Do the existing options form a finite, stable set?**
- Yes → `radio_button` or `multi_select`
- No / options are codes, identifiers, or continuous measures → `text_type`


---


## Platform rule — "Other" option on primary and secondary specs


All `radio_button` and `multi_select` specs in the **primary and secondary tiers** have an
"Other" button that lets sellers enter a custom value not in the list. This means:


- **Do not assign `text_type` to a primary or secondary spec just because its option list
  is incomplete.** The "Other" button covers edge cases.
- Only use `text_type` for primary/secondary specs when the value is genuinely free-form — not simply because some values are missing.



---


## Decision rules — stop at first match


| Rule | Condition | Action |
|------|-----------|--------|
| 1 → `text_type` | Options are model numbers, codes, or identifiers; or values are continuous / unique per SKU; or fewer than 2 standard values exist | Set `text_type`, clear options to `[]` |
| 2 → `radio_button` | Values are mutually exclusive and options form a finite set | Set `radio_button` |
| 3 → `multi_select` | Multiple values can apply to one product and options form a finite set | Set `multi_select` |
| 4 → Keep | Current type is correct per the above | No change |


---


## Common misclassifications


| Spec | Wrong type | Correct type | Why |
|------|-----------|--------------|-----|
| Application / Suitable For / Usage | `radio_button` | `multi_select` | One product serves multiple uses |
| Certifications, IS Standards | `radio_button` | `multi_select` | Products carry multiple marks |
| Phase, Voltage Rating, Insulation Class | `multi_select` | `radio_button` | One fixed value per SKU |
| Model Number, Part Number, Catalogue Code | `radio_button` | `text_type` | Unique per SKU, not enumerable |

---
