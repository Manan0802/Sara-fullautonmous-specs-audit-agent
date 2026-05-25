"""
LangGraph State Schema for SARA Agent.

Defines the state structure that flows through all graph nodes.
"""
from typing import TypedDict, List, Dict, Any, Optional


class SaraState(TypedDict, total=False):
    """
    State for SARA agent graph execution.

    This state is passed between all nodes and tracks:
    - Input context (mcat_id, category, specs)
    - Conversation history
    - Execution metadata (turn, skills read, etc.)
    - Tool results
    - Output and validation
    """

    # ── Input Context ──────────────────────────────────────────────
    mcat_id: int
    category_name: str
    ds0: dict  # Platform specs (initial data)

    # ── Conversation & Prompts ─────────────────────────────────────
    messages: List[Dict[str, str]]  # [{"role": "...", "content": "..."}]
    system_prompt: str

    # ── Execution State ────────────────────────────────────────────
    turn: int
    max_turns: int

    # ── Tracking ───────────────────────────────────────────────────
    skills_read: List[str]  # Names of skills that have been read
    fetch_cache: Dict[str, Any]  # {ds1: [...], ds1_raw: [...], ds2: [...], ...}
    token_usage: List[Dict[str, int]]  # [{turn, prompt_tokens, completion_tokens, total_tokens}]

    # ── Langfuse Observability ─────────────────────────────────────
    trace: Any  # Langfuse trace object
    langfuse: Any  # Langfuse client

    # ── Tool Execution ─────────────────────────────────────────────
    last_response: str  # Last LLM response text
    last_thinking: Optional[str]  # Last LLM thinking (internal reasoning)
    last_raw_json: Optional[dict]  # Raw LLM API response
    last_tool_results: Optional[List[Dict[str, str]]]  # Tool execution results

    # ── Output & Validation ────────────────────────────────────────
    final_output: Optional[str]  # Complete agent output (once validated)
    violations: Optional[List[str]]  # Validation errors
    is_complete: bool  # True when agent has produced valid final output

    # ── File Output ────────────────────────────────────────────────
    full_output: str  # Accumulated output log
    raw_output: str  # Raw API responses log
    input_log: str  # Input messages log
