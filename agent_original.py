"""
Master Agent loop — Tool-based skill access architecture.

Skills are .md knowledge files accessed on-demand through tools:
  - list_skills()           → see what skills are available
  - read_skill(skill_name)  → load full skill content
  - search_skills(query)    → find relevant skills by keyword
  - web_search(query)       → search the internet

The Master Agent decides which skills to read, when to read them,
and applies the reasoning frameworks itself. No sub-agents.
"""
import os
import re
import json
import requests
import time

from web_search import web_search

from converter import load_mapping, convert
from uploader import upload_specs
from langfuse_handler import (
    get_langfuse_client, create_trace, log_turn,
    log_skill_read, log_web_search, log_data_fetch,
    finalise_trace, get_master_prompt
)

from utils import load_prompt, save_dataa_txt
from llm import MASTER_MODEL, API_URL, LLM_API_KEY
from skills import aggregate_ds1, aggregate_ds2, aggregate_ds3
from skill_registry import list_skills, read_skill, search_skills, get_registry_summary
from data_fetchers import (
    fetch_ds1_raw, fetch_ds2_raw, fetch_ds3_raw,
    fetch_ds4_raw, fetch_ds5_raw,
)

INPUTS_DIR    = "inputs"
DATA_DIR      = "data"
RAWOUTPUT_DIR = "rawoutput"
OUTPUT_DIR    = "output"
SKILLLOGS_DIR = "skilllogs"

for d in [INPUTS_DIR, DATA_DIR, RAWOUTPUT_DIR, OUTPUT_DIR, SKILLLOGS_DIR]:
    os.makedirs(d, exist_ok=True)

MAX_TURNS = 30


def run_agent(mcat_id: int, category_name: str, ds0: dict) -> str:
    # ── Step 0: Initialize Langfuse observability ─────────────────
    langfuse = get_langfuse_client()
    trace    = create_trace(langfuse, mcat_id, category_name)

    # ── Step 1: Data is fetched ON DEMAND when agent requests it ───
    # Nothing is pre-fetched. The agent controls what it sees and when.
    # A cache is used so repeated fetches of the same source don't
    # hit the network more than once per run.
    fetch_cache = {}
    turn = 0  # Track current turn for logging

    def get_ds1():
        if "ds1" not in fetch_cache:
            print("  [FETCH] Buyer-Seller Call Data...")
            raw = fetch_ds1_raw(mcat_id)
            fetch_cache["ds1_raw"] = raw
            fetch_cache["ds1"] = aggregate_ds1(raw)
            log_data_fetch(trace, turn, "DS1_Buyer_Call", len(raw))
            print(f"  [FETCH] DS1 ready: {len(fetch_cache['ds1'])} specs")
        return fetch_cache["ds1"]

    def get_ds2():
        if "ds2" not in fetch_cache:
            print("  [FETCH] Custom Seller Specs...")
            raw = fetch_ds2_raw(mcat_id)
            fetch_cache["ds2_raw"] = raw
            fetch_cache["ds2"] = aggregate_ds2(raw)
            log_data_fetch(trace, turn, "DS2_Custom_Specs", len(raw))
            print(f"  [FETCH] DS2 ready: {len(fetch_cache['ds2'])} specs")
        return fetch_cache["ds2"]

    def get_ds3():
        if "ds3" not in fetch_cache:
            print("  [FETCH] Buyer Search Data...")
            raw = fetch_ds3_raw(category_name)
            fetch_cache["ds3_raw"] = raw
            fetch_cache["ds3"] = aggregate_ds3(raw)
            log_data_fetch(trace, turn, "DS3_Buyer_Search", len(raw))
            print(f"  [FETCH] DS3 ready: {len(fetch_cache['ds3'])} specs")
        return fetch_cache["ds3"]

    def get_ds4():
        if "ds4" not in fetch_cache:
            print("  [FETCH] Spec Fill Rate...")
            fetch_cache["ds4"] = fetch_ds4_raw(mcat_id)
            log_data_fetch(trace, turn, "DS4_Fill_Rate", len(fetch_cache["ds4"]))
            print(f"  [FETCH] DS4 ready: {len(fetch_cache['ds4'])} rows")
        return fetch_cache["ds4"]

    def get_ds5():
        if "ds5" not in fetch_cache:
            print("  [FETCH] Option Fill Rate...")
            fetch_cache["ds5"] = fetch_ds5_raw(mcat_id)
            log_data_fetch(trace, turn, "DS5_Option_Fill", len(fetch_cache["ds5"]))
            print(f"  [FETCH] DS5 ready: {len(fetch_cache['ds5'])} rows")
        return fetch_cache["ds5"]

    # ── Step 2: Build system prompt (constitution + tool docs + skill registry) ──

    print("\nBuilding system prompt...")
    # Try fetching from Langfuse first, fallback to local file
    lf_prompt = get_master_prompt(langfuse)
    master_prompt = lf_prompt if lf_prompt else load_prompt("MASTER_PROMPT.md")

    # Append skill registry summary (metadata only, NOT full content)
    registry_section = f"""

---

## AVAILABLE SKILLS (KNOWLEDGE LIBRARY)

You have access to {len(list_skills())} reasoning framework documents. These are NOT sub-agents — they are reference manuals you can read on-demand.

**How to access them:**

1. **List all skills** — you already see the registry below
2. **Read a skill** — when you need a specific framework, call:
   ```
   [READ_SKILL] skill_name [END]
   ```
3. **Search skills** — if you're unsure which skill applies:
   ```
   [SEARCH_SKILLS] your query here [END]
   ```

**Available skills:**

{get_registry_summary()}

**Important:** Read skills selectively and at the right moment — each skill description tells you exactly when to reach for it. The `domain_expert` skill must be read before finalising any action that adds, removes, or promotes a spec or option. You can read the same skill multiple times if needed.

"""
    system_prompt = master_prompt + registry_section

    # ── Step 3: Build initial user message with ONLY DS0 ──────────
    initial_msg = f"""mcat_id: {mcat_id}
category_name: {category_name}
seller_specs (current spec sheet): {json.dumps(ds0['raw'], indent=2)}

No data has been loaded. Use the [FETCH_...] tools to retrieve data when you need it."""

    conversation = []
    skills_read = []  # Track which skills were accessed

    def add_message(role, content):
        conversation.append({"role": role, "content": content})

    def call_master() -> tuple:
        url = API_URL
        if "/chat/completions" not in url:
            url = f"{url.rstrip('/')}/chat/completions"
        payload = {
            "model": MASTER_MODEL,
            "messages": [{"role": "system", "content": system_prompt}] + conversation,
            "max_tokens": 20000,
            "thinking": {"type": "enabled", "budget_tokens": 15000}
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}",
        }
        for attempt in range(3):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=300)
                resp.raise_for_status()
                break
            except requests.exceptions.HTTPError as e:
                if attempt < 3:
                    print(f"  [RETRY] Attempt {attempt+2}/4, waiting 20s...")
                    time.sleep(20)
                else:
                    raise
        data = resp.json()

        thinking_text = None
        response_text = ""
        choice  = data["choices"][0]
        message = choice["message"]

        if "thinking" in message:
            thinking_text = message["thinking"]
        if isinstance(message.get("content"), list):
            for block in message["content"]:
                if isinstance(block, dict):
                    if block.get("type") == "thinking":
                        thinking_text = block.get("thinking") or block.get("text", "")
                    elif block.get("type") == "text":
                        response_text += block.get("text", "")
        else:
            response_text = message.get("content", "")
        if not thinking_text and "reasoning_content" in message:
            thinking_text = message["reasoning_content"]


        return thinking_text, response_text, data

    add_message("user", initial_msg)

    # Save input log
    input_log = (
        "=== SYSTEM PROMPT ===\n"
        f"{system_prompt}\n\n"
        "=== INITIAL USER MESSAGE ===\n"
        f"{initial_msg}\n"
    )

    full_output   = ""
    raw_output    = ""
    turn          = 0
    token_usage_per_turn = []

    # ── Step 4: Agent loop (tool-based: on-demand data + skill reads) ─
    while turn < MAX_TURNS:
        turn += 1
        print(f"\n{'='*50}\nMASTER TURN {turn}\n{'='*50}")

        thinking, response, raw_json = call_master()

        turn_block = f"\n\n{'='*50}\nTURN {turn}\n{'='*50}\n"
        if thinking:
            turn_block += f"\n--- RAW THINKING ---\n{thinking}\n--- END THINKING ---\n\n"
        turn_block += f"--- RESPONSE ---\n{response}"
        if thinking:
            add_message("assistant", f"<thinking>{thinking}</thinking>\n\n{response}")
        else:
            add_message("assistant", response)

        if thinking:
            print(f"\n[RAW THINKING]\n{thinking}\n[END THINKING]\n")
        print(f"[RESPONSE]\n{response}")

        # ── Log data for this turn ──
        full_output += turn_block
        raw_output += (
            f"\n\n{'='*50}\nRAW GATEWAY — TURN {turn}\n{'='*50}\n"
            f"{json.dumps(raw_json, indent=2, ensure_ascii=False)}\n"
        )
        usage = raw_json.get("usage", {})
        token_usage_per_turn.append({
            "turn": turn,
            "prompt_tokens":     usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens":      usage.get("total_tokens", 0),
        })

        # Log this turn to Langfuse
        log_turn(
            trace=trace,
            turn=turn,
            thinking=thinking or "",
            response=response,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            model=MASTER_MODEL,
        )

        # ── Check final output FIRST — before any tool execution ──
        # This prevents the loop from continuing if the agent produced
        # the final 7 sections in the same turn as a tool call tag.
        if is_final_output(response):
            violations = validate_final_output(response, skills_read, conversation)
            if violations:
                # Report contains fabricated citations — reject and force correction
                violation_msg = (
                    "### ❌ AUDIT GATE REJECTION\n\n"
                    "Your report has been rejected because it violates the **PHASE-BASED AUDIT PROTOCOL**. "
                    "You included citations for reasoning skills or web searches that were never physically "
                    "executed. This is considered a critical accuracy failure.\n\n"
                    "**Required Actions before Phase 2:**\n"
                    + "\n".join(f"- {v}" for v in violations)
                    + "\n\n**Instructions:**\n"
                    "1. Execute the missing [READ_SKILL] or [WEB_SEARCH] calls immediately.\n"
                    "2. Process the results in your thinking.\n"
                    "3. Fully recreate your 7-section report once Phase 1 is genuinely complete."
                )
                add_message("user", violation_msg)
                input_log += f"\n=== VALIDATION REJECTION (Turn {turn}) ===\n{violation_msg}\n"
                print(f"  [VALIDATION] Report rejected — {len(violations)} violation(s):")
                for v in violations:
                    print(f"    • {v[:80]}...")
                continue
            print("\n✓ Master produced valid final output. Done.")
            break

        # ── Parse tool calls from response ONLY (never from thinking) ──
        tool_results = execute_tool_calls(
            response or "", skills_read, turn=turn, trace=trace,
            get_ds1=get_ds1, get_ds2=get_ds2, get_ds3=get_ds3,
            get_ds4=get_ds4, get_ds5=get_ds5,
        )

        # ── Handle Tool Results ──
        if tool_results:
            results_msg = f"Here are the results from {len(tool_results)} tool call(s) you made:\n\n"
            for i, tr in enumerate(tool_results, 1):
                results_msg += f"--- Result {i}: {tr['tool']} ---\n{tr['result']}\n\n"

            add_message("user", results_msg)
            input_log += f"\n=== TOOL RESULTS (Turn {turn}) ===\n{results_msg}\n"
            print(f"  [TOOLS] {len(tool_results)} tool call(s) processed")
            continue

        # ── No tools and no final output → nudge ──
        nudge_count = sum(
            1 for m in conversation
            if m["role"] == "user" and "final output" in m.get("content", "").lower()
        )
        if nudge_count >= 2:
            add_message("user",
                "FINAL OUTPUT REQUIRED NOW. Phase 1 must terminate. Write the complete 7-section report including the corrected specs JSON immediately.")
        else:
            add_message("user",
                "**Audit Status:** You are currently in **Phase 1: Investigation & Reasoning**. "
                "Continue gathered evidence and reading required frameworks. "
                "Do not jump to the 7-section report until the `critic` skill and all relevant reasoning frameworks have been read.\n\n"
                "Use [READ_SKILL], [FETCH_...], or [WEB_SEARCH] if you need more information. "
                "Only once Phase 1 is complete, produce your final Phase 2 output.")
        input_log += f"\n=== NUDGE (Turn {turn}) ===\n"

    # ── Save data snapshot (only what was actually fetched) ────────
    save_dataa_txt(
        ds0,
        fetch_cache.get("ds1_raw", []),
        fetch_cache.get("ds2_raw", []),
        fetch_cache.get("ds3_raw", []),
        fetch_cache.get("ds4", []),
        fetch_cache.get("ds5", []),
        mcat_id,
    )

    # ── Save files ─────────────────────────────────────────────────
    summary = "\n\n" + "="*50 + "\nTOKEN USAGE SUMMARY\n" + "="*50 + "\n\n"
    for t in token_usage_per_turn:
        summary += (f"Turn {t['turn']}: "
                    f"prompt={t['prompt_tokens']} | "
                    f"completion={t['completion_tokens']} | "
                    f"total={t['total_tokens']}\n")

    total_prompt     = sum(t["prompt_tokens"]     for t in token_usage_per_turn)
    total_completion = sum(t["completion_tokens"] for t in token_usage_per_turn)
    total_all        = sum(t["total_tokens"]       for t in token_usage_per_turn)

    summary += f"\nGRAND TOTAL:\n"
    summary += f"  Prompt Tokens:     {total_prompt}\n"
    summary += f"  Completion Tokens: {total_completion}\n"
    summary += f"  Total Tokens:      {total_all}\n"
    summary += "="*50 + "\n"

    raw_output += summary

    with open(os.path.join(INPUTS_DIR, f"input_{mcat_id}.txt"), "w", encoding="utf-8") as f:
        f.write(input_log)
    with open(os.path.join(RAWOUTPUT_DIR, f"rawoutput_{mcat_id}.md"), "w", encoding="utf-8") as f:
        f.write(raw_output)
    with open(os.path.join(OUTPUT_DIR, f"output_{mcat_id}.md"), "w", encoding="utf-8") as f:
        f.write(full_output)

    # Skill log
    with open(os.path.join(SKILLLOGS_DIR, f"skill_log_{mcat_id}.md"), "w", encoding="utf-8") as f:
        f.write(f"# Skill Log — {category_name} ({mcat_id})\n\n")
        f.write("## Architecture: Tool-Based Skill Access\n\n")
        f.write("Master Agent accessed skills on-demand via tool calls.\n\n")
        f.write(f"**Total turns:** {turn}\n")
        f.write(f"**Skills read:** {', '.join(skills_read) if skills_read else 'None'}\n")
        web_count = sum(1 for m in conversation if m["role"] == "user" and "WEB_SEARCH" in m.get("content", ""))
        f.write(f"**Web searches:** {web_count}\n")

    print(f"\nAll files saved for {mcat_id}.")

    # Auto-convert to upload format
    try:
        mapping = load_mapping()
        convert(mcat_id, category_name, mapping)
    except Exception as e:
        print(f"Converter warning: {e}")

    ENABLE_UPLOAD = os.getenv("ENABLE_UPLOAD", "false").lower() == "true"
    if ENABLE_UPLOAD:
        print(f"\nUploading specs for {mcat_id}...")
        result = upload_specs(mcat_id)
        if result["success"]:
            print(f"✓ Upload successful! Status: {result['status_code']}")
        else:
            print(f"✗ Upload failed: {result['error']}")
    else:
        print("Upload skipped — set ENABLE_UPLOAD=true in .env to enable")

    # ── Finalize Langfuse trace ────────────────────────────────────
    finalise_trace(trace, mcat_id, total_all, turn, skills_read)
    langfuse.flush()
    print("✓ Langfuse trace logged.")

    return full_output
    


# ── Tool Execution ─────────────────────────────────────────────────────

def execute_tool_calls(response: str, skills_read_tracker: list,
                       turn: int = 0,
                       trace=None,
                       get_ds1=None, get_ds2=None, get_ds3=None,
                       get_ds4=None, get_ds5=None) -> list:
    """Parse and execute all tool calls from the Master's response.
    
    Data sources are fetched lazily via getter functions — only when
    the agent explicitly requests them. This enforces genuine sequential
    investigation rather than pre-planned bulk analysis.
    """
    results = []

    # Normalise once — strip backticks so `[TOOL]` matches the same as [TOOL]
    normalised = response.replace("`", "")

    # ── ONE TOOL TYPE PER TURN ──
    # Detect which tool type appears in this response and execute only that one.
    # Priority: skill reads > skill search > web search > data fetches.
    has_skill_read = bool(re.search(r'\[READ_SKILL\]', normalised, re.IGNORECASE))
    has_search_skills = bool(re.search(r'\[SEARCH_SKILLS\]', normalised, re.IGNORECASE))
    has_web_search = bool(re.search(r'\[WEB_SEARCH\]|RUN_WEB_SEARCH', normalised, re.IGNORECASE))
    has_fetch = any(tag in normalised for tag in [
        "[FETCH_Buyer-Seller Call Data]", "[FETCH_Custom Seller Specs]",
        "[FETCH_Buyer Search Data]", "[FETCH_Spec Fill Rate]", "[FETCH_Option Fill Rate]"
    ])

    if has_skill_read:
        active_tool = "skill_read"
    elif has_search_skills:
        active_tool = "search_skills"
    elif has_web_search:
        active_tool = "web_search"
    elif has_fetch:
        active_tool = "fetch"
    else:
        active_tool = None

    # ── READ_SKILL calls ──
    if active_tool == "skill_read":
        for skill_name in re.findall(r'\[READ_SKILL\]\s*(\S+)\s*\[END\]', normalised, re.IGNORECASE):
            skill_name = skill_name.strip().strip('"').strip("'")
            print(f"  -> Reading skill: {skill_name}")
            result = read_skill(skill_name)
            if "content" in result:
                skills_read_tracker.append(skill_name)
                if trace:
                    log_skill_read(trace, turn, skill_name, result.get("content", "")[:500])
                results.append({
                    "tool": f"READ_SKILL({skill_name})",
                    "result": result["content"],
                })
            else:
                error_msg = result.get("error", f"Skill '{skill_name}' not found in registry.")
                results.append({
                    "tool": f"READ_SKILL({skill_name})",
                    "result": f"ERROR: {error_msg}\n\nAvailable skills: {', '.join([s['name'] for s in list_skills()])}",
                })

    # ── SEARCH_SKILLS calls ──
    if active_tool == "search_skills":
        for query in re.findall(r'\[SEARCH_SKILLS\]\s*(.+?)\s*\[END\]', normalised, re.IGNORECASE | re.DOTALL):
            query = query.strip()
            print(f"  -> Searching skills: {query}")
            result = search_skills(query)
            results.append({
                "tool": f"SEARCH_SKILLS({query})",
                "result": json.dumps(result, indent=2),
            })

    # ── WEB_SEARCH calls ──
    if active_tool == "web_search":
        for query in re.findall(r'\[WEB_SEARCH\]\s*\n?\s*query=["\']([^"\']+)["\']', normalised, re.IGNORECASE | re.DOTALL):
            print(f"  -> Web search: {query}")
            result = web_search(query)
            if trace:
                log_web_search(trace, turn, query, result)
            results.append({
                "tool": f"WEB_SEARCH({query})",
                "result": json.dumps(result, indent=2),
            })

    # ── RUN_WEB_SEARCH fallback format ──
    if active_tool == "web_search":
        for query in re.findall(r'RUN_WEB_SEARCH\(["\']([^"\']+)["\']\)', normalised, re.IGNORECASE):
            print(f"  -> Web search (alt): {query}")
            result = web_search(query)
            if trace:
                log_web_search(trace, turn, query, result)
            results.append({
                "tool": f"WEB_SEARCH({query})",
                "result": json.dumps(result, indent=2),
            })

    # ── FETCH_DS calls — lazy: fetched only when agent requests ──
    # Only execute if no higher-priority tool was found in this turn
    if active_tool == "fetch":

        if "[FETCH_Buyer-Seller Call Data]" in normalised:
            data = get_ds1() if get_ds1 else []
            results.append({
                "tool": "FETCH_Buyer-Seller Call Data",
                "result": json.dumps(data, indent=2) if data else "[]",
            })

        if "[FETCH_Custom Seller Specs]" in normalised:
            data = get_ds2() if get_ds2 else []
            results.append({
                "tool": "FETCH_Custom Seller Specs",
                "result": json.dumps(data, indent=2) if data else "[]",
            })

        if "[FETCH_Buyer Search Data]" in normalised:
            data = get_ds3() if get_ds3 else []
            results.append({
                "tool": "FETCH_Buyer Search Data",
                "result": json.dumps(data, indent=2) if data else "[]",
            })

        if "[FETCH_Spec Fill Rate]" in normalised:
            data = get_ds4() if get_ds4 else []
            results.append({
                "tool": "FETCH_Spec Fill Rate",
                "result": json.dumps(data, indent=2) if data else "[]",
            })

        if "[FETCH_Option Fill Rate]" in normalised:
            data = get_ds5() if get_ds5 else []
            results.append({
                "tool": "FETCH_Option Fill Rate",
                "result": json.dumps(data, indent=2) if data else "[]",
            })

    return results


def is_final_output(response: str) -> bool:
    """Check if the response contains the complete final audit output."""
    return (
        "finalized_primary_specs" in response and
        "generated_by" in response and
        "finalized_tertiary_specs" in response
    )


def validate_final_output(response: str, skills_read: list, conversation: list) -> list:
    """
    Verify that skills and web searches cited in the Investigation Log were
    actually executed as tool calls. Returns a list of violation messages.
    An empty list means the output is valid and can be accepted.

    This prevents the agent from fabricating citations — writing "I read
    domain_expert" or "web search confirmed X" without having actually done so.
    """
    violations = []

    # Skills that must have been read if cited in the report
    citable_skills = [
        "missing_spec_addition",
        "domain_expert",
        "option_validator",
        "spec_sequencing",
        "critic",
        "input_type_audit",
        "buyer_call_analysis",
        "custom_spec_analysis",
        "buyer_search_analysis",
    ]

    for skill in citable_skills:
        # Check if skill name appears in the report text
        if skill in response and skill not in skills_read:
            violations.append(
                f"`{skill}` is cited in your Investigation Log but was never "
                f"read. You must call [READ_SKILL] {skill} [END] and receive "
                f"its content before you can cite it. Rewrite the report after "
                f"reading the skill."
            )

    # Check if web search is cited but never executed
    web_cited = (
        "[WEB_SEARCH]" in response
        or "web search" in response.lower()
        or "websearch" in response.lower()
    )
    web_executed = any(
        "WEB_SEARCH" in m.get("content", "")
        for m in conversation
        if m["role"] == "user"
    )
    if web_cited and not web_executed:
        violations.append(
            "Your Investigation Log cites web search results but no "
            "[WEB_SEARCH] tool call was ever executed. Run the required "
            "web searches first, then rewrite the report with the actual "
            "results from your turn history."
        )

    # Check if Option Fill Rate data is needed but never fetched
    option_changes_mentioned = (
        "Option Changes" in response
        and any(
            action in response
            for action in ["ADDED", "REMOVED", "RENAMED TO", "MERGED INTO"]
        )
    )
    ds5_fetched = any(
        "FETCH_Option Fill Rate" in m.get("content", "")
        for m in conversation
        if m["role"] == "user"
    )
    if option_changes_mentioned and not ds5_fetched:
        violations.append(
            "Your report contains option-level changes but Option Fill Rate "
            "data was never fetched. Call [FETCH_Option Fill Rate] to see "
            "which options are actually being used before finalising changes."
        )

    # Check if Spec Fill Rate data is needed but never fetched
    sequencing_mentioned = (
        "spec_sequencing" in response
        or "RE-TIERED" in response
    )
    ds4_fetched = any(
        "FETCH_Spec Fill Rate" in m.get("content", "")
        for m in conversation
        if m["role"] == "user"
    )
    if sequencing_mentioned and not ds4_fetched:
        violations.append(
            "Your report contains sequencing/tiering changes but Spec Fill Rate "
            "data (DS4) was never fetched. You are FORBIDDEN from assigning "
            "tiers without this signal. Call [FETCH_Spec Fill Rate] now and "
            "re-evaluate your sequencing."
        )

    # Check if Data interpretation skills were read for all fetched sources
    interpretation_mapping = {
        "FETCH_Buyer-Seller Call Data": "buyer_call_analysis",
        "FETCH_Custom Seller Specs": "custom_spec_analysis",
        "FETCH_Buyer Search Data": "buyer_search_analysis",
    }
    for fetch_tool, skill_name in interpretation_mapping.items():
        fetched = any(fetch_tool in m.get("content", "") for m in conversation if m["role"] == "user")
        if fetched and skill_name not in skills_read:
            violations.append(
                f"You fetched `{fetch_tool}` but never read the `{skill_name}` "
                f"interpretation skill. You are mandated to read the framework "
                f"for every data source you use. Read it now."
            )

    return violations
