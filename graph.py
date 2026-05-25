"""
LangGraph Graph Builder for SARA Agent.

Defines the state graph structure, nodes, and conditional routing logic.
"""
from langgraph.graph import StateGraph, END
from state import SaraState
from nodes import (
    initialize_node,
    agent_reasoning_node,
    check_output_node,
    execute_tool_node,
    return_results_node,
    handle_violation_node,
    nudge_agent_node,
    finalize_node,
)


def should_continue(state: SaraState) -> str:
    """
    Router function that determines which node to visit next.

    Implements the control flow logic from the original agent:
    - Check turn limit
    - Check for completion
    - Handle violations
    - Route tool executions
    - Handle nudges
    """

    # Hard limit: max turns reached
    if state["turn"] >= state["max_turns"]:
        print(f"\n[ROUTER] Max turns ({state['max_turns']}) reached. Finalizing...")
        return "finalize"

    # Success: final output validated and complete
    if state.get("is_complete"):
        print("[ROUTER] Agent complete. Finalizing...")
        return "finalize"

    # Violations detected: reject and force correction
    if state.get("violations"):
        print("[ROUTER] Violations detected. Routing to handle_violation...")
        return "handle_violation"

    # Tool results ready: return to agent for next reasoning step
    if state.get("last_tool_results"):
        print("[ROUTER] Tool results ready. Routing to return_results...")
        return "return_results"

    # Check if LLM response contains tool calls → execute them
    last_response = state.get("last_response", "")
    has_tool_call = any([
        "[READ_SKILL]" in last_response,
        "[SEARCH_SKILLS]" in last_response,
        "[WEB_SEARCH]" in last_response,
        "RUN_WEB_SEARCH" in last_response,
        "[FETCH_" in last_response,
    ])

    if has_tool_call:
        print("[ROUTER] Tool call detected. Routing to execute_tool...")
        return "execute_tool"

    # No tools and no final output: nudge agent
    if not state.get("is_complete"):
        print("[ROUTER] No tools, no output. Routing to nudge...")
        return "nudge"

    # Fallback: continue reasoning
    print("[ROUTER] Continuing agent reasoning...")
    return "agent_reasoning"


def build_sara_graph():
    """
    Build and compile the SARA agent graph.

    Graph structure:
        START → initialize → agent_reasoning → check_output → [Router]
                                    ↑                             |
                                    |              ╔══════════════╩══════════════╗
                                    |              ║                             ║
                                    └──────────────╫─ finalize (END)            ║
                                                   ║─ handle_violation           ║
                                                   ║─ execute_tool → return_results
                                                   ║─ nudge                      ║
                                                   ╚═════════════════════════════╝
    """
    graph = StateGraph(SaraState)

    # Add all nodes
    graph.add_node("initialize", initialize_node)
    graph.add_node("agent_reasoning", agent_reasoning_node)
    graph.add_node("check_output", check_output_node)
    graph.add_node("execute_tool", execute_tool_node)
    graph.add_node("return_results", return_results_node)
    graph.add_node("handle_violation", handle_violation_node)
    graph.add_node("nudge", nudge_agent_node)
    graph.add_node("finalize", finalize_node)

    # Set entry point
    graph.set_entry_point("initialize")

    # Linear edges
    graph.add_edge("initialize", "agent_reasoning")
    graph.add_edge("agent_reasoning", "check_output")
    graph.add_edge("execute_tool", "return_results")

    # After tool results, violations, or nudges → go back to agent for new LLM call
    # This prevents re-checking the old response (which would re-trigger tool execution)
    graph.add_edge("return_results", "agent_reasoning")
    graph.add_edge("handle_violation", "agent_reasoning")
    graph.add_edge("nudge", "agent_reasoning")

    # Conditional routing from check_output
    graph.add_conditional_edges(
        "check_output",
        should_continue,
        {
            "finalize": "finalize",
            "handle_violation": "handle_violation",
            "return_results": "return_results",
            "execute_tool": "execute_tool",
            "nudge": "nudge",
            "agent_reasoning": "agent_reasoning",
        }
    )

    # Finalize leads to END
    graph.add_edge("finalize", END)

    # Compile and return
    return graph.compile()
