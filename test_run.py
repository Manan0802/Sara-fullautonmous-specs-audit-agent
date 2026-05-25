from agent_langgraph import run_agent
from data_fetchers import fetch_ds0

def test():
    mcat_id = 68910
    category_name = "Protein Powder"
    print(f"Testing agent for {mcat_id} ({category_name})")
    
    ds0 = fetch_ds0(mcat_id)
    
    # Run the agent!
    run_agent(mcat_id, category_name, ds0)
    
if __name__ == "__main__":
    test()
