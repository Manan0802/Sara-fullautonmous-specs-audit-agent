"""
Skill Registry — Tool-based skill access for the Master Agent.

Skills are .md knowledge files. Instead of injecting all of them into the
system prompt, the Master Agent accesses them on-demand through tools:

  list_skills()         → lightweight registry (name + description + tags)
  read_skill(name)      → full .md content
  search_skills(query)  → keyword search across skill metadata

Each skill description uses trigger language — telling the agent not just
what the skill does but exactly when to reach for it. This prevents bulk
upfront reading and encourages selective, moment-of-need access.
"""
import os
import json
from utils import load_prompt


# ── Skill Registry (Layer A: metadata only) ──────────────────────────

SKILL_REGISTRY = [
    {
        "name": "buyer_call_analysis",
        "description": (
            "Read this immediately after fetching Buyer-Seller Call Data to correctly "
            "interpret the signals — product count thresholds, what counts as high vs "
            "low signal, how to extract spec candidates from conversation context, and "
            "how to avoid false positives from noisy call data."
        ),
        "tags": ["buyer-calls", "signal-interpretation", "product-count", "DS1"],
        "file": "SKILL_1_buyer_call.md",
    },
    {
        "name": "custom_spec_analysis",
        "description": (
            "Read this immediately after fetching Custom Seller Specs to correctly "
            "interpret what sellers are adding and why — distinguishing genuine gaps "
            "from noise, context terms, and duplicate signals across data sources."
        ),
        "tags": ["custom-specs", "gap-detection", "seller-signal", "DS2"],
        "file": "SKILL_2_custom_spec.md",
    },
    {
        "name": "buyer_search_analysis",
        "description": (
            "Read this immediately after fetching Buyer Search Data to correctly "
            "interpret impression counts, identify which search terms are genuine "
            "filter signals vs context terms, and understand cross-category pollution."
        ),
        "tags": ["buyer-search", "impressions", "filter-discovery", "DS3"],
        "file": "SKILL_3_buyer_search.md",
    },
    {
        "name": "missing_spec_addition",
        "description": (
            "Read this to add new specifications after identifying gaps from buyer–seller calls, buyer search data, and custom inputs. Validate whether a candidate specification is suitable, and define it completely, including its name, input type, options, and tier."
        ),
        "tags": ["spec-addition", "missing-specs", "false-positive", "gap-identification", "new-spec", "missing spec"],
        "file": "SKILL_4_missing_spec_addition.md",
    },
    {
        "name": "spec_sequencing",
        "description": (
            "Read this when you are ready to assign or change the tier of a spec — "
            "It provides the "
            "convergence logic, signal calibration, and override rules (IMPLIED, "
            "DATA_ARTIFACT, WEAK_EVIDENCE) needed to justify Primary vs Secondary "
            "vs Tertiary placement. Read it after fetching the Fill Rate data, Buyer Seller Call Data and Buyer Search Data"
        ),
        "tags": ["ranking", "tiering", "sequencing", "convergence", "primary", "secondary", "tertiary"],
        "file": "SKILL_5_sequencing.md",
    },
    {
        "name": "option_validator",
        "description": (
            "Read this when you need to audit and correct the option list for any spec."
            "It tells you how to first check whether the spec belongs in this category,"
            "then evaluate each existing option (keep, reject, or merge), identify new"
            "options to add, and apply structural fixes. You produce the validation output"
            "yourself using this reasoning framework"
        ),
        "tags": ["options", "validation", "option-audit", "corrections"],
        "file": "SKILL_6_option_validator.md",
    },
    {
        "name": "domain_expert",
        "description": (
            "Read this when you identify a potential spec or option to add, remove, "
            "or re-tier — not upfront and not at the end. Use it during your Phase 1 "
            "investigation to sanity-check a candidate change against the real "
            "Indian B2B market before finalizing your reasoning for that action."
        ),
        "tags": ["domain", "indian-b2b", "conflict-resolution", "sanity-check", "standards", "market-reality"],
        "file": "SKILL_7_domain_expert.md",
    },
    {
        "name": "critic",
        "description": (
            "Read this whenever you are about to finalize your reasoning for a "
            "specific action in Phase 1 (addition, removal, merge, etc.). Apply the "
            "per-action challenge framework to your thinking block for every "
            "individual action you propose. Do not wait until the final report to "
            "invoke the critic."
        ),
        "tags": ["critic", "review", "challenge", "evidence-quality", "verdict", "holistic"],
        "file": "SKILL_8_Critic.md",
    },
    {
        "name": "input_type_audit",
        "description": (
            "Read this when you are deciding or changing the input_type of a spec — "
            "not upfront. Read it when you have a specific spec in front of you and "
            "need to determine whether radio_button, multi_select, or text_type is "
            "correct based on the spec's nature and the platform rules."
        ),
        "tags": ["input-type", "radio_button", "multi-select", "text-type", "options"],
        "file": "SKILL_9_Input_type.md",
    },
    {
        "name": "brand_option_review",
        "description": (
            "Read this only when you are auditing or removing options from a Brand "
            "spec. It provides the web-confirmation requirement before any brand "
            "option can be removed, and rules for handling oversized brand lists."
        ),
        "tags": ["brand", "brand-options", "oem", "web-check", "option-removal"],
        "file": "SKILL_10_Brand.md",
    },
]


# ── Tool Functions (Layer B: full content access) ────────────────────

def list_skills() -> list:
    """Returns lightweight registry: name + description + tags only."""
    return [
        {
            "name": s["name"],
            "description": s["description"],
            "tags": s["tags"],
        }
        for s in SKILL_REGISTRY
    ]


def read_skill(skill_name: str) -> dict:
    """Returns full .md content for a specific skill."""
    for s in SKILL_REGISTRY:
        if s["name"] == skill_name:
            try:
                content = load_prompt(s["file"])
                return {
                    "name": s["name"],
                    "content": content,
                }
            except FileNotFoundError:
                return {
                    "name": s["name"],
                    "error": f"Skill file not found: {s['file']}",
                }
    return {"error": f"Unknown skill: {skill_name}. Use list_skills() to see available skills."}


def search_skills(query: str) -> list:
    """Search skills by keyword matching across name, description, and tags."""
    query_lower = query.lower()
    query_words = query_lower.split()

    scored = []
    for s in SKILL_REGISTRY:
        score = 0
        searchable = f"{s['name']} {s['description']} {' '.join(s['tags'])}".lower()
        for word in query_words:
            if word in searchable:
                score += 1
        if score > 0:
            scored.append({
                "name": s["name"],
                "description": s["description"],
                "tags": s["tags"],
                "relevance_score": score,
            })

    scored.sort(key=lambda x: x["relevance_score"], reverse=True)
    return scored




# ── Registry summary for system prompt ───────────────────────────────

def get_registry_summary() -> str:
    """
    Returns a compact text summary of available skills for the system prompt.
    Includes trigger guidance so the agent knows when to reach for each skill
    without reading every one upfront.
    """
    lines = []
    for s in SKILL_REGISTRY:
        tags_str = ", ".join(s["tags"])
        lines.append(
            f"- **{s['name']}**: {s['description']}\n"
            f"  Tags: `{tags_str}`"
        )
    return "\n".join(lines)
