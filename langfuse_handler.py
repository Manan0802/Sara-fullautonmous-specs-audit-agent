import os
import json
from datetime import datetime
from langfuse import Langfuse


def get_langfuse_client() -> Langfuse:
    """Initialize and return Langfuse client with credentials from environment."""
    return Langfuse(
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        host=os.getenv("LANGFUSE_BASE_URL"),
    )


def get_master_prompt(langfuse: Langfuse) -> str:
    """
    Fetch the Master Prompt from Langfuse prompt management.
    Returns None if fetch fails (agent will use local file fallback).
    """
    try:
        prompt = langfuse.get_prompt("Master Prompt", type="text")
        print(f"OK - Prompt fetched from Langfuse - version {prompt.version}")
        return prompt.compile()
    except Exception as e:
        print(f"WARNING - Langfuse prompt fetch failed: {e} - using local file")
        return None


def create_trace(langfuse: Langfuse, mcat_id: int, category_name: str):
    """Create a new Langfuse trace for this audit run."""
    return langfuse.trace(
        name=f"spec_audit_{mcat_id}",
        session_id=f"batch_{datetime.now().strftime('%Y%m%d')}",
        input=f"Audit request for {category_name} (mcat_id: {mcat_id})",
        output="Spec audit in progress",
        metadata={
            "mcat_id":       mcat_id,
            "category_name": category_name,
        },
        tags=["spec-audit", "gemini-2.5-pro"],
    )


def log_turn(trace, turn: int, thinking: str, response: str,
             prompt_tokens: int, completion_tokens: int, model: str):
    """Log a single master agent turn to Langfuse."""
    trace.generation(
        name=f"turn_{turn}",
        model=model,
        input=thinking if thinking else "No thinking — direct response",
        output=response if response else "No response",
        usage={
            "input":  prompt_tokens,
            "output": completion_tokens,
            "unit":   "TOKENS",
            "input_cost":  prompt_tokens * 0.00000125,  # Gemini 2.5 Pro pricing
            "output_cost": completion_tokens * 0.000010,
        },
        metadata={"turn": turn},
    )


def log_skill_read(trace, turn: int, skill_name: str, content: str = ""):
    """Log a skill read operation to Langfuse."""
    trace.span(
        name=f"skill_read_{skill_name}",
        input=skill_name,
        output=content if content else "Skill content loaded",
        metadata={
            "turn":       turn,
            "skill_name": skill_name,
        },
    )


def log_web_search(trace, turn: int, query: str, results: dict):
    """Log a web search operation to Langfuse."""
    trace.span(
        name=f"web_search",
        input=query,
        output=json.dumps(results, indent=2) if results else "No results",
        metadata={"turn": turn, "query": query},
    )


def log_data_fetch(trace, turn: int, data_source: str, row_count: int, data=None):
    """Log a data fetch operation to Langfuse (NEW for post-fetching architecture)."""
    
    # Try to provide a good chunk of data without crashing due to sheer limit
    output_repr = f"Fetched {row_count} rows"
    if data:
        data_str = json.dumps(data, indent=2)
        # 50,000 characters is a very generous chunk that won't lag the dashboard 
        if len(data_str) > 50000:
            output_repr = data_str[:50000] + f"\n\n... [TRUNCATED - {len(data_str) - 50000} characters omitted for display]"
        else:
            output_repr = data_str

    trace.span(
        name=f"data_fetch_{data_source}",
        input=data_source,
        output=output_repr,
        metadata={
            "turn":        turn,
            "data_source": data_source,
            "row_count":   row_count,
        },
    )


def finalise_trace(trace, mcat_id: int, total_tokens: int,
                   turns: int, skills_read: list):
    """Update trace with final summary information."""
    trace.update(
        output=f"Audit complete — {turns} turns, {total_tokens} tokens, skills: {', '.join(skills_read) if skills_read else 'none'}",
        metadata={
            "total_tokens":  total_tokens,
            "total_turns":   turns,
            "skills_used":   skills_read,
            "skills_count":  len(skills_read),
        },
    )
