
## What this skill is for

Apply this document every time you propose a specific action during your Phase 1 investigation. Do not wait until the final report turn. 

It provides the framework to challenge your own reasoning for each individual spec addition, removal, or re-tiering as it emerges from the data. Use it to avoid bias and ensure only strong, validated actions reach Phase 2.

---

## The critic's job

Challenge proposed actions before they become final. Not to reject everything —
to find what is weak, what is thin, and what could be wrong. A critic that
approves everything has failed. A critic that rejects everything has also failed.
The goal is calibrated skepticism: approve what is strong, flag what is thin,
reject what is unsupported.

---

## Two modes — when to apply each

**Per-action critique**
Apply immediately after proposing each action. Challenge the single action in
isolation before moving on.

**Holistic review**
Apply once after all individual actions have been proposed and critiqued. Review
the complete action set as a whole for contradictions, missed gaps, and coherence.

---

## Per-action critique — what to check

### Check 1: Evidence quality

| Question | What makes it weak | What makes it strong |
|----------|--------------------|----------------------|
| How many independent sources support this? | 1 source only | 2+ sources converge |
| How strong are the signal numbers? | 3 call mentions, 10 impressions | 90 call mentions, 5000 impressions |
| Is there contradictory evidence? | Another source actively argues against it | All sources point the same direction |
| Is the evidence the right type for this action? | ADD_SPEC based only on domain knowledge | ADD_SPEC backed by call data + search |

### Check 2: Alternative explanations

Every data pattern has multiple possible explanations. Articulate at least one:

- High search volume → could be a CONTEXT_TERM, not a missing spec
- Low fill rate → could be bad options, not an irrelevant spec
- Zero call mentions → could be a spec buyers check in listings, not discussed verbally
- Multiple sellers adding custom spec → could be one seller's duplicate listings

The alternative does not have to be right — it must be plausible enough that
it should have been addressed.

### Check 3: Related signals not considered

When an action targets one spec, check whether related attributes were examined:

- Adding `Length` → Was `Width` also investigated? Dimensions are a family.
- Adding options to `Finish` → Were the same values checked in `Color`?
- Moving a spec up in tier → What gets displaced? Was the displaced spec evaluated?
- Removing an option → Is there a niche segment that actually uses this value?

### Check 4: When to execute a web search

Execute a web search immediately — do not flag it for later — when:
- The action relies solely on domain reasoning with no quantitative signal
- Two internal sources conflict and platform data cannot resolve which is correct
- An option value's canonical format is uncertain
- A spec has high volume in one source but zero signal elsewhere

### Check 5: Assign verdict

**`approved`**
Evidence is strong across multiple sources. Reasoning is sound. No significant
alternative explanation undermines the action. Proceed.

**`caution`**
Evidence exists but is thin — single source, low volume, or domain-only reasoning.
Or the reasoning has a gap that was not addressed. Action can proceed but must be
flagged as lower confidence. A suggested revision is required.

**`reject`**
Evidence does not support the action. Either: no quantitative data backs it,
a strong alternative explanation was ignored, or the action contradicts other
accepted actions. State what evidence would be needed to act on this in future.

---

## Per-action critique output

Produce this after every proposed action:

```
Critic — [action type + spec name]
Verdict: approved / caution / reject
Challenge: [the strongest evidence gap or alternative explanation, citing
signal numbers. If caution or reject: what evidence would change the verdict.]
```

Keep it tight — 2-3 sentences. The goal is a genuine challenge, not a
comprehensive report. Scale depth to the impact of the action: a minor option
addition needs less scrutiny than a full spec removal or tier restructuring.

---

## Heightened scrutiny — apply to destructive actions

Destructive actions require stronger evidence than constructive ones:

- `REMOVE_SPEC` — requires multi-source evidence. Domain reasoning alone is
  insufficient. Zero signal across all sources is required, or strong evidence
  that the spec is a duplicate or context term.
- `REMOVE_OPTIONS` — requires zero signal across option fill rate, impressions,
  and call data simultaneously.
- `MERGE_SPECS` — requires clear evidence that both specs capture exactly the
  same attribute with no information lost by merging.

When reviewing a destructive action, explicitly state: "This is a destructive
action. Evidence reviewed: [list sources checked]."

---

## Holistic review — what to check

Apply this once after all individual actions are complete.

### Check 1: Contradictions between accepted actions
Do any accepted actions conflict with each other?
- Adding a spec AND removing a spec that captures the same attribute
- Moving a spec up in tier AND reducing its option list
- Two specs promoted to Primary when combined they exceed the tier maximum

### Check 2: Missed gaps
Review all signals from the data sources and ask: is there anything the analysis
noticed but never proposed an action for, and never classified as a Skipped Gap?

### Check 3: Skipped gap justifications
Check the Skipped Gaps list. For each:
- Is the reason for skipping defensible?
- Was the classification validated with data, or just assumed?
- Should any skipped gap be reconsidered given other accepted actions?

### Check 4: Overall coherence
Does the final spec set make sense as a whole for how this product is actually
bought and sold in Indian B2B? What is the biggest strength? What is the biggest
remaining weakness?

---

## Holistic review output

```
Holistic Review
Contradictions: [list any conflicting accepted actions, or "None"]
Missed gaps: [any signals not acted on and not in Skipped Gaps, or "None"]
Skipped gaps: [are the skipped gap justifications defensible, or should any be reconsidered]
Overall: [one paragraph — coherence, strength, weakness, confidence in final output]
```

---

## Calibration rules

**Be specific, not vague**
Wrong: "This seems weak."
Right: "This action is based on search data alone (164 impressions) with zero
call mentions and zero custom spec signal — single-source evidence at moderate volume."

**Be evidence-based, not contrarian**
Challenge based on data gaps and reasoning flaws. If the evidence is genuinely
strong, approving is the right call.

**Be proportional**
A minor option addition with solid evidence does not need the same scrutiny as
a full spec removal or complete resequencing.

**Be constructive**
Every `caution` or `reject` must include a suggested revision — a way to fix
the problem, not just a complaint.


