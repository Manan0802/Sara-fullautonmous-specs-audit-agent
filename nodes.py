"""
LangGraph Node Functions for SARA Agent.

Each node is a function that takes state and returns updated state.
These nodes preserve all the logic from the original agent.py while
adapting it to the LangGraph execution model.
"""
import os
import json
import requests
import time
import re

from state import SaraState
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
from web_search import web_search
from converter import load_mapping, convert
from uploader import upload_specs


# ══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS (from original agent.py)
# ══════════════════════════════════════════════════════════════════

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


def execute_tool_calls(response: str, state: SaraState) -> list:
    """
    Parse and execute all tool calls from the Master's response.
    Returns list of tool results.

    Preserves one-tool-per-turn priority: skills > search > web > data
    """
    results = []
    skills_read_tracker = state["skills_read"]
    turn = state["turn"]
    trace = state.get("trace")

    # Normalize once
    normalised = response.replace("`", "")

    # ── ONE TOOL TYPE PER TURN ──
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
                    log_skill_read(trace, turn, skill_name, result.get("content", ""))
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
        # Format 1: [WEB_SEARCH] query="..." [END]  or  [WEB_SEARCH]\nquery="..."
        for query in re.findall(r'\[WEB_SEARCH\]\s*\n?\s*query=["\']([^"\']+)["\']', normalised, re.IGNORECASE | re.DOTALL):
            print(f"  -> Web search: {query}")
            result = web_search(query)
            if trace:
                log_web_search(trace, turn, query, result)
            results.append({
                "tool": f"WEB_SEARCH({query})",
                "result": json.dumps(result, indent=2),
            })

        # Format 2: [WEB_SEARCH] some query text [END]  (no query= prefix)
        if not results:
            for query in re.findall(r'\[WEB_SEARCH\]\s+([^[\n]+?)\s*\[END\]', normalised, re.IGNORECASE):
                query = query.strip().strip('"').strip("'")
                if query and "query=" not in query.lower():
                    print(f"  -> Web search (inline): {query}")
                    result = web_search(query)
                    if trace:
                        log_web_search(trace, turn, query, result)
                    results.append({
                        "tool": f"WEB_SEARCH({query})",
                        "result": json.dumps(result, indent=2),
                    })

    # ── RUN_WEB_SEARCH fallback format ──
    if active_tool == "web_search" and not results:
        for query in re.findall(r'RUN_WEB_SEARCH\(["\']([^"\']+)["\']\)', normalised, re.IGNORECASE):
            print(f"  -> Web search (alt): {query}")
            result = web_search(query)
            if trace:
                log_web_search(trace, turn, query, result)
            results.append({
                "tool": f"WEB_SEARCH({query})",
                "result": json.dumps(result, indent=2),
            })

    # ── FETCH_DS calls ──
    if active_tool == "fetch":
        # Create lazy data fetchers that use state
        def get_ds1():
            if "ds1" not in state["fetch_cache"]:
                print("  [FETCH] Buyer-Seller Call Data...")
                raw = fetch_ds1_raw(state["mcat_id"])
                state["fetch_cache"]["ds1_raw"] = raw
                state["fetch_cache"]["ds1"] = aggregate_ds1(raw)
                if trace:
                    log_data_fetch(trace, turn, "DS1_Buyer_Call", len(raw), data=raw)
                print(f"  [FETCH] DS1 ready: {len(state['fetch_cache']['ds1'])} specs")
            return state["fetch_cache"]["ds1"]

        def get_ds2():
            if "ds2" not in state["fetch_cache"]:
                print("  [FETCH] Custom Seller Specs...")
                raw = fetch_ds2_raw(state["mcat_id"])
                state["fetch_cache"]["ds2_raw"] = raw
                state["fetch_cache"]["ds2"] = aggregate_ds2(raw)
                if trace:
                    log_data_fetch(trace, turn, "DS2_Custom_Specs", len(raw), data=raw)
                print(f"  [FETCH] DS2 ready: {len(state['fetch_cache']['ds2'])} specs")
            return state["fetch_cache"]["ds2"]

        def get_ds3():
            if "ds3" not in state["fetch_cache"]:
                print("  [FETCH] Buyer Search Data...")
                raw = fetch_ds3_raw(state["category_name"])
                state["fetch_cache"]["ds3_raw"] = raw
                state["fetch_cache"]["ds3"] = aggregate_ds3(raw)
                if trace:
                    log_data_fetch(trace, turn, "DS3_Buyer_Search", len(raw), data=raw)
                print(f"  [FETCH] DS3 ready: {len(state['fetch_cache']['ds3'])} specs")
            return state["fetch_cache"]["ds3"]

        def get_ds4():
            if "ds4" not in state["fetch_cache"]:
                print("  [FETCH] Spec Fill Rate...")
                state["fetch_cache"]["ds4"] = fetch_ds4_raw(state["mcat_id"])
                if trace:
                    ds4_data = state["fetch_cache"]["ds4"]
                    log_data_fetch(trace, turn, "DS4_Fill_Rate", len(ds4_data), data=ds4_data)
                print(f"  [FETCH] DS4 ready: {len(state['fetch_cache']['ds4'])} rows")
            return state["fetch_cache"]["ds4"]

        def get_ds5():
            if "ds5" not in state["fetch_cache"]:
                print("  [FETCH] Option Fill Rate...")
                state["fetch_cache"]["ds5"] = fetch_ds5_raw(state["mcat_id"])
                if trace:
                    ds5_data = state["fetch_cache"]["ds5"]
                    log_data_fetch(trace, turn, "DS5_Option_Fill", len(ds5_data), data=ds5_data)
                print(f"  [FETCH] DS5 ready: {len(state['fetch_cache']['ds5'])} rows")
            return state["fetch_cache"]["ds5"]

        if "[FETCH_Buyer-Seller Call Data]" in normalised:
            data = get_ds1()
            results.append({
                "tool": "FETCH_Buyer-Seller Call Data",
                "result": json.dumps(data, indent=2) if data else "[]",
            })

        if "[FETCH_Custom Seller Specs]" in normalised:
            data = get_ds2()
            results.append({
                "tool": "FETCH_Custom Seller Specs",
                "result": json.dumps(data, indent=2) if data else "[]",
            })

        if "[FETCH_Buyer Search Data]" in normalised:
            data = get_ds3()
            results.append({
                "tool": "FETCH_Buyer Search Data",
                "result": json.dumps(data, indent=2) if data else "[]",
            })

        if "[FETCH_Spec Fill Rate]" in normalised:
            data = get_ds4()
            results.append({
                "tool": "FETCH_Spec Fill Rate",
                "result": json.dumps(data, indent=2) if data else "[]",
            })

        if "[FETCH_Option Fill Rate]" in normalised:
            data = get_ds5()
            results.append({
                "tool": "FETCH_Option Fill Rate",
                "result": json.dumps(data, indent=2) if data else "[]",
            })

    return results


# ══════════════════════════════════════════════════════════════════
# LANGGRAPH NODES
# ══════════════════════════════════════════════════════════════════

def initialize_node(state: SaraState) -> SaraState:
    """
    Entry point: Initialize Langfuse, build system prompt, create initial message.
    """
    print("\n" + "="*60)
    print("SARA AGENT — LangGraph Mode")
    print("="*60)

    # Initialize Langfuse
    langfuse = get_langfuse_client()
    trace = create_trace(langfuse, state["mcat_id"], state["category_name"])

    # Build system prompt
    print("\nBuilding system prompt...")
    lf_prompt = get_master_prompt(langfuse)
    master_prompt = lf_prompt if lf_prompt else load_prompt("MASTER_PROMPT.md")

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

    # Build initial user message
    initial_msg = f"""mcat_id: {state["mcat_id"]}
category_name: {state["category_name"]}
seller_specs (current spec sheet): {json.dumps(state['ds0']['raw'], indent=2)}

No data has been loaded. Use the [FETCH_...] tools to retrieve data when you need it."""

    # Initialize state
    state["langfuse"] = langfuse
    state["trace"] = trace
    state["system_prompt"] = system_prompt
    state["messages"] = [{"role": "user", "content": initial_msg}]
    state["turn"] = 0
    state["max_turns"] = 30
    state["skills_read"] = []
    state["fetch_cache"] = {}
    state["token_usage"] = []
    state["is_complete"] = False
    state["full_output"] = ""
    state["raw_output"] = ""
    state["input_log"] = (
        "=== SYSTEM PROMPT ===\n"
        f"{system_prompt}\n\n"
        "=== INITIAL USER MESSAGE ===\n"
        f"{initial_msg}\n"
    )

    print("Initialization complete. Starting agent loop...")
    return state


def agent_reasoning_node(state: SaraState) -> SaraState:
    """
    Call LLM with thinking mode, log turn to Langfuse, update state with response.
    """
    state["turn"] += 1
    turn = state["turn"]

    print(f"\n{'='*50}\nMASTER TURN {turn}\n{'='*50}")

    # Call LLM
    url = API_URL
    if "/chat/completions" not in url:
        url = f"{url.rstrip('/')}/chat/completions"

    payload = {
        "model": MASTER_MODEL,
        "messages": [{"role": "system", "content": state["system_prompt"]}] + state["messages"],
        "max_tokens": 20000,
        "thinking": {"type": "enabled", "budget_tokens": 15000}
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}",
    }

    for attempt in range(4):
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

    # Extract thinking and response
    thinking_text = None
    response_text = ""
    choice = data["choices"][0]
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

    # Add to conversation
    if thinking_text:
        state["messages"].append({
            "role": "assistant",
            "content": f"<thinking>{thinking_text}</thinking>\n\n{response_text}"
        })
    else:
        state["messages"].append({
            "role": "assistant",
            "content": response_text
        })

    # Log outputs
    turn_block = f"\n\n{'='*50}\nTURN {turn}\n{'='*50}\n"
    if thinking_text:
        turn_block += f"\n--- RAW THINKING ---\n{thinking_text}\n--- END THINKING ---\n\n"
    turn_block += f"--- RESPONSE ---\n{response_text}"

    state["full_output"] += turn_block
    state["raw_output"] += (
        f"\n\n{'='*50}\nRAW GATEWAY — TURN {turn}\n{'='*50}\n"
        f"{json.dumps(data, indent=2, ensure_ascii=False)}\n"
    )

    if thinking_text:
        print(f"\n[RAW THINKING]\n{thinking_text[:500] if thinking_text else ''}...\n[END THINKING]\n")
    if response_text:
        print(f"[RESPONSE]\n{response_text[:500]}...")
    else:
        print("[RESPONSE]\n(empty response)")

    # Track token usage
    usage = data.get("usage", {})
    state["token_usage"].append({
        "turn": turn,
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
    })

    # Log to Langfuse
    log_turn(
        trace=state["trace"],
        turn=turn,
        thinking=thinking_text or "",
        response=response_text,
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        model=MASTER_MODEL,
    )

    # Update state
    state["last_response"] = response_text
    state["last_thinking"] = thinking_text
    state["last_raw_json"] = data

    return state


def check_output_node(state: SaraState) -> SaraState:
    """
    Check if response contains final output and validate it.
    Also clears stale routing state from previous turns.
    """
    response = state["last_response"]

    # Clear stale routing state from previous iterations
    state["violations"] = None
    state["last_tool_results"] = None

    if is_final_output(response):
        print("\n[VALIDATION] Checking final output...")
        violations = validate_final_output(
            response,
            state["skills_read"],
            state["messages"]
        )

        if violations:
            state["violations"] = violations
            print(f"  [VALIDATION] Report rejected — {len(violations)} violation(s)")
            for v in violations:
                print(f"    • {v[:80]}...")
        else:
            state["final_output"] = response
            state["is_complete"] = True
            print("\nOK - Master produced valid final output. Done.")

    return state


def execute_tool_node(state: SaraState) -> SaraState:
    """
    Parse and execute tools from last response.
    """
    response = state["last_response"]
    tool_results = execute_tool_calls(response, state)

    if tool_results:
        state["last_tool_results"] = tool_results
        print(f"  [TOOLS] {len(tool_results)} tool call(s) processed")

    return state


def return_results_node(state: SaraState) -> SaraState:
    """
    Add tool results to conversation and clear from state.
    """
    tool_results = state.get("last_tool_results", [])

    if tool_results:
        results_msg = f"Here are the results from {len(tool_results)} tool call(s) you made:\n\n"
        for i, tr in enumerate(tool_results, 1):
            results_msg += f"--- Result {i}: {tr['tool']} ---\n{tr['result']}\n\n"

        state["messages"].append({"role": "user", "content": results_msg})
        state["input_log"] += f"\n=== TOOL RESULTS (Turn {state['turn']}) ===\n{results_msg}\n"
        state["last_tool_results"] = None

    return state


def handle_violation_node(state: SaraState) -> SaraState:
    """
    Handle validation violations by sending rejection message.
    """
    violations = state.get("violations", [])

    if violations:
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

        state["messages"].append({"role": "user", "content": violation_msg})
        state["input_log"] += f"\n=== VALIDATION REJECTION (Turn {state['turn']}) ===\n{violation_msg}\n"
        state["violations"] = None

    return state


def nudge_agent_node(state: SaraState) -> SaraState:
    """
    Nudge agent to continue or produce final output.
    """
    # Count previous nudges
    nudge_count = sum(
        1 for m in state["messages"]
        if m["role"] == "user" and "final output" in m.get("content", "").lower()
    )

    if nudge_count >= 2:
        nudge_msg = (
            "FINAL OUTPUT REQUIRED NOW. Phase 1 must terminate. Write the complete "
            "7-section report including the corrected specs JSON immediately."
        )
    else:
        nudge_msg = (
            "**Audit Status:** You are currently in **Phase 1: Investigation & Reasoning**. "
            "Continue gathering evidence and reading required frameworks. "
            "Do not jump to the 7-section report until the `critic` skill and all relevant reasoning frameworks have been read.\n\n"
            "Use [READ_SKILL], [FETCH_...], or [WEB_SEARCH] if you need more information. "
            "Only once Phase 1 is complete, produce your final Phase 2 output."
        )

    state["messages"].append({"role": "user", "content": nudge_msg})
    state["input_log"] += f"\n=== NUDGE (Turn {state['turn']}) ===\n{nudge_msg}\n"
    print(f"  [NUDGE] Agent prompted to continue/finish")

    return state


def finalize_node(state: SaraState) -> SaraState:
    """
    Save all files, convert, upload, finalize Langfuse trace.
    """
    print("\n" + "="*60)
    print("FINALIZING")
    print("="*60)

    mcat_id = state["mcat_id"]
    category_name = state["category_name"]

    # Create directories
    for d in ["inputs", "data", "rawoutput", "output", "skilllogs"]:
        os.makedirs(d, exist_ok=True)

    # Build token summary
    summary = "\n\n" + "="*50 + "\nTOKEN USAGE SUMMARY\n" + "="*50 + "\n\n"
    for t in state["token_usage"]:
        summary += (f"Turn {t['turn']}: "
                    f"prompt={t['prompt_tokens']} | "
                    f"completion={t['completion_tokens']} | "
                    f"total={t['total_tokens']}\n")

    total_prompt = sum(t["prompt_tokens"] for t in state["token_usage"])
    total_completion = sum(t["completion_tokens"] for t in state["token_usage"])
    total_all = sum(t["total_tokens"] for t in state["token_usage"])

    summary += f"\nGRAND TOTAL:\n"
    summary += f"  Prompt Tokens:     {total_prompt}\n"
    summary += f"  Completion Tokens: {total_completion}\n"
    summary += f"  Total Tokens:      {total_all}\n"
    summary += "="*50 + "\n"

    state["raw_output"] += summary

    # Save data snapshot
    save_dataa_txt(
        state["ds0"],
        state["fetch_cache"].get("ds1_raw", []),
        state["fetch_cache"].get("ds2_raw", []),
        state["fetch_cache"].get("ds3_raw", []),
        state["fetch_cache"].get("ds4", []),
        state["fetch_cache"].get("ds5", []),
        mcat_id,
    )

    # Save files
    with open(os.path.join("inputs", f"input_{mcat_id}.txt"), "w", encoding="utf-8") as f:
        f.write(state["input_log"])
    with open(os.path.join("rawoutput", f"rawoutput_{mcat_id}.md"), "w", encoding="utf-8") as f:
        f.write(state["raw_output"])
    with open(os.path.join("output", f"output_{mcat_id}.md"), "w", encoding="utf-8") as f:
        f.write(state["full_output"])

    # Skill log
    with open(os.path.join("skilllogs", f"skill_log_{mcat_id}.md"), "w", encoding="utf-8") as f:
        f.write(f"# Skill Log — {category_name} ({mcat_id})\n\n")
        f.write("## Architecture: LangGraph Tool-Based Skill Access\n\n")
        f.write("Master Agent accessed skills on-demand via tool calls.\n\n")
        f.write(f"**Total turns:** {state['turn']}\n")
        f.write(f"**Skills read:** {', '.join(state['skills_read']) if state['skills_read'] else 'None'}\n")
        web_count = sum(1 for m in state["messages"] if m["role"] == "user" and "WEB_SEARCH" in m.get("content", ""))
        f.write(f"**Web searches:** {web_count}\n")

    print(f"\nAll files saved for {mcat_id}.")

    # Convert
    try:
        mapping = load_mapping()
        convert(mcat_id, category_name, mapping)
    except Exception as e:
        print(f"Converter warning: {e}")

    # Upload
    ENABLE_UPLOAD = os.getenv("ENABLE_UPLOAD", "false").lower() == "true"
    if ENABLE_UPLOAD:
        print(f"\nUploading specs for {mcat_id}...")
        result = upload_specs(mcat_id)
        if result["success"]:
            print(f"OK - Upload successful! Status: {result['status_code']}")
        else:
            print(f"✗ Upload failed: {result['error']}")
    else:
        print("Upload skipped — set ENABLE_UPLOAD=true in .env to enable")

    # Finalize Langfuse
    finalise_trace(state["trace"], mcat_id, total_all, state["turn"], state["skills_read"])
    state["langfuse"].flush()
    print("OK - Langfuse trace logged.")

    return state
