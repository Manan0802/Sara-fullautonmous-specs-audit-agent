import time
from data_fetchers import fetch_ds0
from agent_langgraph import run_agent
from utils import save_input_txt

MCAT_LIST = [
    (15348, "Jar Candle"),
    (7103,  "Polycotton Fabric"),
    (14433, "Cat 6 Cable"),
    (9843,  "Marble Cutter"),
    (12018, "Dry Red Chilli"),
    (12096, "Aromatic Incense Sticks"),
    (1266,  "Centrifugal Blowers"),
    (10112, "Industrial Safety Helmets"),
    (18988, "Teak Wood Sofa"),
    (20944, "Laptop Keyboard"),
    (21428, "Alloy Steel Bars"),
    (24164, "Solid Carbide End Mills"),
    (38882, "Stretch Wrapping Machine"),
    (4786,  "Electric Angle Grinder"),
    (35716, "Pressure Transmitters"),
    (14970, "AC Servo Motor"), 
]

def run_batch():
    total = len(MCAT_LIST)
    passed = []
    failed = []

    for i, (mcat_id, category_name) in enumerate(MCAT_LIST, 1):
        print(f"\n{'#'*60}")
        print(f"# BATCH {i}/{total} — {category_name} (mcat_id: {mcat_id})")
        print(f"{'#'*60}\n")
        try:
            ds0 = fetch_ds0(mcat_id)
            print(f"DS-0 fetched: {len(ds0['current_specs'])} specs found.")
            save_input_txt(mcat_id, category_name, ds0["raw"])
            run_agent(mcat_id, category_name, ds0)
            print(f"\n✓ Done: {category_name} ({mcat_id})\n")
            passed.append((mcat_id, category_name))
        except Exception as e:
            print(f"\n✗ Failed: {category_name} ({mcat_id}) — {e}\n")
            failed.append((mcat_id, category_name, str(e)))

        if i < total:
            print("\n--- Waiting 60 seconds before next category ---")
            time.sleep(60)

    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE — {total} categories")
    print(f"✓ Passed: {len(passed)}")
    for m, n in passed:
        print(f"   {m} — {n}")
    if failed:
        print(f"✗ Failed: {len(failed)}")
        for m, n, e in failed:
            print(f"   {m} — {n} → {e}")
    print(f"{'='*60}")

if __name__ == "__main__":
    run_batch()
