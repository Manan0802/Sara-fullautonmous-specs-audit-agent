"""
Comprehensive test suite for SARA LangGraph agent.
Tests all modules, skill loading, graph building, routing, tool parsing, and state flow.
"""
import os
import sys
import json
import traceback

PASS = 0
FAIL = 0

def check(label, fn):
    global PASS, FAIL
    try:
        result = fn()
        PASS += 1
        detail = f" -- {result}" if result else ""
        print(f"  [OK] {label}{detail}")
    except Exception as e:
        FAIL += 1
        print(f"  [FAIL] {label}: {e}")
        traceback.print_exc()


# ===================================================
# 1. MODULE IMPORTS
# ===================================================
print("\n1. MODULE IMPORTS")
print("=" * 50)

check("state.py", lambda: __import__("state") and None)
check("llm.py", lambda: __import__("llm") and None)
check("utils.py", lambda: __import__("utils") and None)
check("skills.py", lambda: __import__("skills") and None)
check("skill_registry.py", lambda: __import__("skill_registry") and None)
check("data_fetchers.py", lambda: __import__("data_fetchers") and None)
check("web_search.py", lambda: __import__("web_search") and None)
check("langfuse_handler.py", lambda: __import__("langfuse_handler") and None)
check("converter.py", lambda: __import__("converter") and None)
check("uploader.py", lambda: __import__("uploader") and None)
check("nodes.py", lambda: __import__("nodes") and None)
check("graph.py", lambda: __import__("graph") and None)
check("agent_langgraph.py", lambda: __import__("agent_langgraph") and None)


# ===================================================
# 2. SKILL FILES
# ===================================================
print("\n2. SKILL FILE LOADING")
print("=" * 50)

from skill_registry import SKILL_REGISTRY, read_skill, list_skills, search_skills, get_registry_summary

for s in SKILL_REGISTRY:
    name = s["name"]
    def test_skill(n=name):
        result = read_skill(n)
        if "error" in result:
            raise Exception(result["error"])
        return f"{len(result['content'])} chars"
    check(f"skill: {name}", test_skill)


# ===================================================
# 3. SKILL SEARCH
# ===================================================
print("\n3. SKILL SEARCH FUNCTIONALITY")
print("=" * 50)

def test_list_skills():
    skills = list_skills()
    assert len(skills) == len(SKILL_REGISTRY), f"Expected {len(SKILL_REGISTRY)}, got {len(skills)}"
    return f"{len(skills)} skills"
check("list_skills()", test_list_skills)

def test_search_skills():
    results = search_skills("buyer call data interpretation")
    assert len(results) > 0, "No search results"
    assert results[0]["name"] == "buyer_call_analysis"
    return f"{len(results)} matches, top={results[0]['name']}"
check("search_skills()", test_search_skills)

def test_registry_summary():
    summary = get_registry_summary()
    assert len(summary) > 100, "Summary too short"
    return f"{len(summary)} chars"
check("get_registry_summary()", test_registry_summary)


# ===================================================
# 4. PROMPT FILE
# ===================================================
print("\n4. PROMPT FILE")
print("=" * 50)

from utils import load_prompt

def test_master_prompt():
    prompt = load_prompt("MASTER_PROMPT.md")
    assert len(prompt) > 500, "Master prompt too short"
    return f"{len(prompt)} chars"
check("MASTER_PROMPT.md", test_master_prompt)


# ===================================================
# 5. GRAPH BUILDING & STRUCTURE
# ===================================================
print("\n5. GRAPH BUILDING")
print("=" * 50)

from graph import build_sara_graph, should_continue

def test_graph_build():
    g = build_sara_graph()
    assert g is not None, "Graph is None"
    return "compiled OK"
check("build_sara_graph()", test_graph_build)


# ===================================================
# 6. ROUTING LOGIC
# ===================================================
print("\n6. ROUTING LOGIC (should_continue)")
print("=" * 50)

def make_state(**overrides):
    base = {
        "turn": 1,
        "max_turns": 30,
        "is_complete": False,
        "violations": None,
        "last_tool_results": None,
        "last_response": "",
        "messages": [],
        "skills_read": [],
    }
    base.update(overrides)
    return base

def test_route_max_turns():
    state = make_state(turn=30, max_turns=30)
    result = should_continue(state)
    assert result == "finalize", f"Expected finalize, got {result}"
    return "turn=30 -> finalize"
check("max_turns reached", test_route_max_turns)

def test_route_complete():
    state = make_state(is_complete=True)
    result = should_continue(state)
    assert result == "finalize", f"Expected finalize, got {result}"
    return "is_complete -> finalize"
check("is_complete", test_route_complete)

def test_route_violations():
    state = make_state(violations=["some violation"])
    result = should_continue(state)
    assert result == "handle_violation", f"Expected handle_violation, got {result}"
    return "violations -> handle_violation"
check("violations detected", test_route_violations)

def test_route_tool_results():
    state = make_state(last_tool_results=[{"tool": "test", "result": "ok"}])
    result = should_continue(state)
    assert result == "return_results", f"Expected return_results, got {result}"
    return "tool_results -> return_results"
check("tool results ready", test_route_tool_results)

def test_route_execute_tool_skill():
    state = make_state(last_response="[READ_SKILL] domain_expert [END]")
    result = should_continue(state)
    assert result == "execute_tool", f"Expected execute_tool, got {result}"
    return "[READ_SKILL] -> execute_tool"
check("READ_SKILL -> execute_tool", test_route_execute_tool_skill)

def test_route_execute_tool_fetch():
    state = make_state(last_response="[FETCH_Spec Fill Rate]")
    result = should_continue(state)
    assert result == "execute_tool", f"Expected execute_tool, got {result}"
    return "[FETCH_] -> execute_tool"
check("FETCH_ -> execute_tool", test_route_execute_tool_fetch)

def test_route_execute_tool_websearch():
    state = make_state(last_response='[WEB_SEARCH] query="test query"')
    result = should_continue(state)
    assert result == "execute_tool", f"Expected execute_tool, got {result}"
    return "[WEB_SEARCH] -> execute_tool"
check("WEB_SEARCH -> execute_tool", test_route_execute_tool_websearch)

def test_route_execute_tool_search_skills():
    state = make_state(last_response="[SEARCH_SKILLS] buyer data [END]")
    result = should_continue(state)
    assert result == "execute_tool", f"Expected execute_tool, got {result}"
    return "[SEARCH_SKILLS] -> execute_tool"
check("SEARCH_SKILLS -> execute_tool", test_route_execute_tool_search_skills)

def test_route_nudge():
    state = make_state(last_response="I am thinking about this...", is_complete=False)
    result = should_continue(state)
    assert result == "nudge", f"Expected nudge, got {result}"
    return "no tools -> nudge"
check("no tools/output -> nudge", test_route_nudge)


# ===================================================
# 7. TOOL CALL PARSING (execute_tool_calls)
# ===================================================
print("\n7. TOOL CALL PARSING")
print("=" * 50)

from nodes import execute_tool_calls, is_final_output, validate_final_output

def test_read_skill_parsing():
    test_state = {
        "skills_read": [],
        "turn": 1,
        "trace": None,
        "mcat_id": 123,
        "category_name": "Test",
        "fetch_cache": {},
    }
    response = "[READ_SKILL] domain_expert [END]"
    results = execute_tool_calls(response, test_state)
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    assert "domain_expert" in results[0]["tool"]
    assert "domain_expert" in test_state["skills_read"]
    return f"parsed {len(results)} skill read, tracked in skills_read"
check("READ_SKILL parsing", test_read_skill_parsing)

def test_search_skills_parsing():
    test_state = {
        "skills_read": [],
        "turn": 1,
        "trace": None,
        "mcat_id": 123,
        "category_name": "Test",
        "fetch_cache": {},
    }
    response = "[SEARCH_SKILLS] buyer tier signal [END]"
    results = execute_tool_calls(response, test_state)
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    return f"parsed {len(results)} search"
check("SEARCH_SKILLS parsing", test_search_skills_parsing)

def test_web_search_parsing_format1():
    test_state = {
        "skills_read": [],
        "turn": 1,
        "trace": None,
        "mcat_id": 123,
        "category_name": "Test",
        "fetch_cache": {},
    }
    response = '[WEB_SEARCH]\nquery="aluminium profiles India B2B specifications"'
    results = execute_tool_calls(response, test_state)
    return f"parsed {len(results)} web search(es) (format 1)"
check("WEB_SEARCH format 1 (query=)", test_web_search_parsing_format1)

def test_web_search_parsing_format2():
    test_state = {
        "skills_read": [],
        "turn": 1,
        "trace": None,
        "mcat_id": 123,
        "category_name": "Test",
        "fetch_cache": {},
    }
    response = '[WEB_SEARCH] aluminium profiles India B2B [END]'
    results = execute_tool_calls(response, test_state)
    return f"parsed {len(results)} web search(es) (format 2 inline)"
check("WEB_SEARCH format 2 (inline)", test_web_search_parsing_format2)

def test_fetch_ds4_parsing():
    test_state = {
        "skills_read": [],
        "turn": 1,
        "trace": None,
        "mcat_id": 68910,
        "category_name": "Protein Powder",
        "fetch_cache": {},
    }
    response = "[FETCH_Spec Fill Rate]"
    results = execute_tool_calls(response, test_state)
    return f"parsed {len(results)} fetch call(s) -- no crash with trace=None"
check("FETCH_DS4 (trace=None safe)", test_fetch_ds4_parsing)


# ===================================================
# 8. FINAL OUTPUT DETECTION
# ===================================================
print("\n8. FINAL OUTPUT DETECTION")
print("=" * 50)

def test_is_final_yes():
    text = '{"finalized_primary_specs": {}, "finalized_tertiary_specs": {}, "generated_by": "agent"}'
    assert is_final_output(text), "Should detect final output"
    return "detected correctly"
check("is_final_output (positive)", test_is_final_yes)

def test_is_final_no():
    text = "I am still investigating the specs..."
    assert not is_final_output(text), "Should NOT detect final output"
    return "rejected correctly"
check("is_final_output (negative)", test_is_final_no)

def test_validate_no_violations():
    text = '{"finalized_primary_specs": {}, "finalized_tertiary_specs": {}, "generated_by": "agent"}'
    violations = validate_final_output(text, ["domain_expert", "critic"], [])
    return f"{len(violations)} violations"
check("validate_final_output (clean)", test_validate_no_violations)

def test_validate_with_violations():
    text = 'I used domain_expert and critic findings to determine...'
    violations = validate_final_output(text, [], [])
    assert len(violations) >= 2, f"Expected >=2 violations, got {len(violations)}"
    return f"{len(violations)} violations detected"
check("validate_final_output (violations)", test_validate_with_violations)


# ===================================================
# 9. NODE FUNCTIONS (unit test with mock state)
# ===================================================
print("\n9. NODE STATE HANDLING")
print("=" * 50)

from nodes import check_output_node, return_results_node, handle_violation_node, nudge_agent_node

def test_check_output_no_final():
    state = {
        "last_response": "Still working...",
        "skills_read": [],
        "messages": [],
        "violations": ["old violation"],
        "last_tool_results": [{"tool": "old"}],
    }
    result = check_output_node(state)
    assert not result.get("is_complete"), "Should not be complete"
    assert result.get("violations") is None, "Stale violations should be cleared"
    assert result.get("last_tool_results") is None, "Stale tool results should be cleared"
    return "not complete, stale state cleared"
check("check_output_node (clears stale state)", test_check_output_no_final)

def test_return_results():
    state = {
        "last_tool_results": [{"tool": "TEST", "result": "ok"}],
        "messages": [],
        "turn": 1,
        "input_log": "",
    }
    result = return_results_node(state)
    assert result["last_tool_results"] is None, "Tool results should be cleared"
    assert len(result["messages"]) == 1, "Should have added result message"
    return "results appended and cleared"
check("return_results_node", test_return_results)

def test_handle_violation():
    state = {
        "violations": ["Test violation"],
        "messages": [],
        "turn": 1,
        "input_log": "",
    }
    result = handle_violation_node(state)
    assert result["violations"] is None, "Violations should be cleared"
    assert len(result["messages"]) == 1
    assert "REJECTION" in result["messages"][0]["content"]
    return "violation handled and cleared"
check("handle_violation_node", test_handle_violation)

def test_nudge():
    state = {
        "messages": [],
        "turn": 1,
        "input_log": "",
    }
    result = nudge_agent_node(state)
    assert len(result["messages"]) == 1
    return "nudge added"
check("nudge_agent_node", test_nudge)

def test_nudge_force_output():
    state = {
        "messages": [
            {"role": "user", "content": "produce final output now"},
            {"role": "user", "content": "produce final output now"},
        ],
        "turn": 5,
        "input_log": "",
    }
    result = nudge_agent_node(state)
    last_msg = result["messages"][-1]["content"]
    assert "FINAL OUTPUT REQUIRED NOW" in last_msg
    return "force output after 2 nudges"
check("nudge_agent_node (force)", test_nudge_force_output)


# ===================================================
# 10. CONVERTER MODULE
# ===================================================
print("\n10. CONVERTER MODULE")
print("=" * 50)

from converter import parse_specs_from_output

def test_parse_specs_missing():
    result = parse_specs_from_output(999999)
    assert result is None
    return "None for missing file"
check("parse_specs_from_output (missing file)", test_parse_specs_missing)


# ===================================================
# 11. JSON PARSING
# ===================================================
print("\n11. JSON PARSING")
print("=" * 50)

from utils import parse_json_response

def test_json_clean():
    result = parse_json_response('{"key": "value"}')
    assert result.get("key") == "value"
    return "clean JSON"
check("parse_json_response (clean)", test_json_clean)

def test_json_with_markdown():
    result = parse_json_response('```json\n{"key": "value"}\n```')
    assert result.get("key") == "value"
    return "markdown-wrapped JSON"
check("parse_json_response (markdown)", test_json_with_markdown)

def test_json_trailing_comma():
    result = parse_json_response('{"key": "value",}')
    assert result.get("key") == "value"
    return "trailing comma handled"
check("parse_json_response (trailing comma)", test_json_trailing_comma)

def test_json_array():
    result = parse_json_response('[{"name": "test"}]')
    assert "results" in result
    return "array wrapped"
check("parse_json_response (array)", test_json_array)


# ===================================================
# 12. DATA AGGREGATION
# ===================================================
print("\n12. DATA AGGREGATION")
print("=" * 50)

from skills import aggregate_ds1, aggregate_ds2, aggregate_ds3

def test_agg_ds1_empty():
    assert aggregate_ds1([]) == []
    return "empty input -> empty output"
check("aggregate_ds1 (empty)", test_agg_ds1_empty)

def test_agg_ds1():
    raw = [
        {"spec_name": "Color", "option_value": "Red", "prod_count": 10},
        {"spec_name": "Color", "option_value": "Blue", "prod_count": 5},
        {"spec_name": "Size",  "option_value": "L",    "prod_count": 1},
    ]
    result = aggregate_ds1(raw)
    assert len(result) == 1
    assert result[0]["spec_name"] == "Color"
    assert result[0]["total_product_count"] == 15
    return f"{len(result)} aggregated specs"
check("aggregate_ds1 (with data)", test_agg_ds1)

def test_agg_ds2():
    raw = [{"spec_name": "Material", "option_value": "Steel"} for _ in range(6)]
    result = aggregate_ds2(raw, min_count=5)
    assert len(result) == 1
    return f"{len(result)} specs above threshold"
check("aggregate_ds2 (threshold)", test_agg_ds2)

def test_agg_ds3():
    raw = [
        {"spec_name": "Weight", "spec_option": "1kg", "impression": "100"},
        {"spec_name": "Weight", "spec_option": "2kg", "impression": "50"},
        {"spec_name": "Color",  "spec_option": "Red", "impression": "10"},
    ]
    result = aggregate_ds3(raw, min_impressions=50)
    assert len(result) == 1
    assert result[0]["spec_name"] == "Weight"
    return f"{len(result)} specs above impression threshold"
check("aggregate_ds3 (impressions)", test_agg_ds3)


# ===================================================
# 13. COMPLETE FLOW SIMULATION (no LLM call)
# ===================================================
print("\n13. COMPLETE FLOW SIMULATION")
print("=" * 50)

def test_full_flow_tool_execution():
    """Simulate: agent produces tool call -> check_output -> router -> execute -> return -> agent"""
    from nodes import check_output_node, execute_tool_node, return_results_node

    # Step 1: Agent produced a READ_SKILL response
    state = {
        "last_response": "[READ_SKILL] critic [END]",
        "skills_read": [],
        "messages": [{"role": "assistant", "content": "[READ_SKILL] critic [END]"}],
        "turn": 1,
        "max_turns": 30,
        "trace": None,
        "mcat_id": 123,
        "category_name": "Test",
        "fetch_cache": {},
        "input_log": "",
        "violations": None,
        "last_tool_results": None,
    }

    # Step 2: check_output sees it's not final
    state = check_output_node(state)
    assert not state.get("is_complete"), "Should not be complete"
    assert state.get("violations") is None
    assert state.get("last_tool_results") is None

    # Step 3: Router should route to execute_tool
    route = should_continue(state)
    assert route == "execute_tool", f"Expected execute_tool, got {route}"

    # Step 4: execute_tool runs the skill read
    state = execute_tool_node(state)
    assert state.get("last_tool_results") is not None, "Should have tool results"
    assert len(state["last_tool_results"]) == 1
    assert "critic" in state["skills_read"], "critic should be tracked"

    # Step 5: return_results adds to messages and clears
    state = return_results_node(state)
    assert state["last_tool_results"] is None, "Should be cleared"
    assert len(state["messages"]) == 2  # original + results
    assert "Result 1" in state["messages"][-1]["content"]

    return "full tool flow works end-to-end"
check("full tool execution flow", test_full_flow_tool_execution)

def test_full_flow_violation():
    """Simulate: agent produces final output with violation -> rejection -> agent"""
    from nodes import check_output_node, handle_violation_node

    state = {
        "last_response": 'Based on domain_expert and critic analysis: {"finalized_primary_specs": {}, "finalized_tertiary_specs": {}, "generated_by": "agent"}',
        "skills_read": [],  # Empty! domain_expert and critic cited but not read
        "messages": [],
        "turn": 3,
        "max_turns": 30,
        "violations": None,
        "last_tool_results": None,
    }

    # check_output detects final output and validates
    state = check_output_node(state)
    assert state.get("violations") is not None, "Should have violations"
    assert len(state["violations"]) >= 2, f"Expected >=2 violations, got {len(state.get('violations', []))}"
    assert not state.get("is_complete"), "Should not be complete due to violations"

    # Router routes to handle_violation
    route = should_continue(state)
    assert route == "handle_violation", f"Expected handle_violation, got {route}"

    # handle_violation sends rejection
    state["input_log"] = ""
    state = handle_violation_node(state)
    assert state["violations"] is None, "Violations should be cleared"
    assert "REJECTION" in state["messages"][-1]["content"]

    return "violation detection and handling works"
check("full violation flow", test_full_flow_violation)

def test_full_flow_valid_output():
    """Simulate: agent produces valid final output -> finalize"""
    from nodes import check_output_node

    state = {
        "last_response": '{"finalized_primary_specs": {}, "finalized_tertiary_specs": {}, "generated_by": "agent"}',
        "skills_read": [],
        "messages": [],
        "turn": 5,
        "max_turns": 30,
        "violations": None,
        "last_tool_results": None,
    }

    state = check_output_node(state)
    assert state.get("is_complete"), "Should be complete"
    assert state.get("final_output") is not None

    route = should_continue(state)
    assert route == "finalize", f"Expected finalize, got {route}"

    return "valid output -> finalize works"
check("full valid output flow", test_full_flow_valid_output)


# ===================================================
# 14. ENV VARIABLES
# ===================================================
print("\n14. ENVIRONMENT VARIABLES")
print("=" * 50)

from dotenv import load_dotenv
load_dotenv()

required_vars = [
    "LLM_GATEWAY_URL",
    "LLM_GATEWAY_API_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_BASE_URL",
]
for var in required_vars:
    val = os.getenv(var, "")
    if val:
        check(f"env: {var}", lambda v=val: f"set ({len(v)} chars)")
    else:
        check(f"env: {var}", lambda: (_ for _ in ()).throw(Exception("NOT SET")))


# ===================================================
# 15. DASHBOARD IMPORT
# ===================================================
print("\n15. DASHBOARD PARSE FUNCTIONS")
print("=" * 50)

def test_dashboard_parse():
    from dashboard import parse_output
    raw = """
==================================================
TURN 1
==================================================

--- RAW THINKING ---
I need to analyze the specs for this category.
--- END THINKING ---

--- RESPONSE ---
Let me start by reading the relevant skills.

[READ_SKILL] domain_expert [END]
"""
    result = parse_output(raw)
    assert len(result["turns"]) >= 1, "Should parse at least 1 turn"
    assert result["turns"][0]["thinking"] != "", "Should have thinking"
    return f"{len(result['turns'])} turns parsed"

try:
    check("parse_output (dashboard)", test_dashboard_parse)
except Exception:
    print("  [SKIP] dashboard.py requires streamlit (OK)")


# ===================================================
# FINAL SUMMARY
# ===================================================
print("\n" + "=" * 50)
print(f"RESULTS: {PASS} passed, {FAIL} failed")
print("=" * 50)

if FAIL > 0:
    sys.exit(1)
else:
    print("\nAll tests passed! Agent is ready for production.")
