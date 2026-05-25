"""
Spec Audit Agent — CLI entry point.
LangGraph implementation.
"""
import json
from data_fetchers import fetch_ds0
from agent_langgraph import run_agent
from utils import save_input_txt


def main():
    print("=== Spec Audit Agent ===\n")
    mcat_id = int(input("Enter category_id: ").strip())
    category_name = input("Enter category name: ").strip()

    print(f"\nFetching DS-0 seller specs for mcat_id {mcat_id}...")
    ds0 = fetch_ds0(mcat_id)
    print(f"DS-0 fetched: {len(ds0['current_specs'])} specs found.")

    # Auto-save input.txt with raw seller specs
    save_input_txt(mcat_id, category_name, ds0["raw"])

    print(f"\nStarting audit for: {category_name} (mcat_id: {mcat_id})\n")
    output = run_agent(mcat_id, category_name, ds0)

    print("\n=== Audit Complete ===")
    print("Check output.txt for full raw output.")


if __name__ == "__main__":
    # Can still run directly
    main()
