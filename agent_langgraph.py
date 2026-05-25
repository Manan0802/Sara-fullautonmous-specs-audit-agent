"""
SARA Agent — LangGraph Implementation.

Entry point for running the SARA spec auditing agent using LangGraph.
This replaces the original agent.py while preserving all functionality.
"""
from typing import Dict, Any
from graph import build_sara_graph
from state import SaraState


def run_agent_langgraph(mcat_id: int, category_name: str, ds0: dict) -> str:
    """
    Run the SARA agent using LangGraph.

    Args:
        mcat_id: Market category ID
        category_name: Category name
        ds0: Initial platform specs data

    Returns:
        Complete agent output (7-section audit report)
    """

    # Build initial state
    initial_state: SaraState = {
        "mcat_id": mcat_id,
        "category_name": category_name,
        "ds0": ds0,
        "messages": [],
        "turn": 0,
        "max_turns": 30,
        "skills_read": [],
        "fetch_cache": {},
        "token_usage": [],
        "is_complete": False,
        "full_output": "",
        "raw_output": "",
        "input_log": "",
    }

    # Build and compile graph
    graph = build_sara_graph()

    print("\n" + "="*60)
    print("     SARA Agent - LangGraph Orchestration")
    print("="*60)
    print(f"\nCategory: {category_name} (ID: {mcat_id})")
    print(f"Max turns: 30")
    print(f"Framework: LangGraph + Gemini 2.5 Pro")
    print()

    # Run the graph
    try:
        final_state = graph.invoke(initial_state)

        # Return final output
        output = final_state.get("final_output", final_state.get("full_output", ""))

        print("\n" + "="*60)
        print("          EXECUTION COMPLETE")
        print("="*60)
        print(f"\nTotal turns: {final_state.get('turn', 0)}")
        print(f"Skills read: {len(final_state.get('skills_read', []))}")
        print(f"Data sources fetched: {len([k for k in final_state.get('fetch_cache', {}).keys() if not k.endswith('_raw')])}")

        return output

    except Exception as e:
        print(f"\nERROR during graph execution: {e}")
        import traceback
        traceback.print_exc()
        raise


# Backward compatibility alias
run_agent = run_agent_langgraph


if __name__ == "__main__":
    # Test run (requires proper input data)
    print("SARA Agent — LangGraph Implementation")
    print("Use main.py or dashboard.py to run the agent with proper data.")
