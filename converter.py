import os
import re
import json
import pandas as pd

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1hdDrDy5ODTC1uI_4wh26SLflQuW65NKv8_oKYfXFF6c/export?format=csv"
UPLOAD_DIR    = "upload_ready"
OUTPUT_DIR    = "output"

os.makedirs(UPLOAD_DIR, exist_ok=True)


def load_mapping() -> dict:
    df = pd.read_csv(SHEET_CSV_URL)
    df = df.dropna(subset=["glcat_mcat_id", "prime_pmcat_id_2"])
    df["glcat_mcat_id"]    = df["glcat_mcat_id"].astype(int)
    df["prime_pmcat_id_2"] = df["prime_pmcat_id_2"].astype(int)
    mapping = {}
    for _, row in df.iterrows():
        mapping[int(row["glcat_mcat_id"])] = {
            "pmcat_id":   int(row["prime_pmcat_id_2"]),
            "pmcat_name": str(row["prime_pmcat_name_2"]),
        }
    print(f"Mapping loaded: {len(mapping)} mcat entries")
    return mapping


def parse_specs_from_output(mcat_id: int) -> dict | None:
    path = os.path.join(OUTPUT_DIR, f"output_{mcat_id}.md")
    if not os.path.exists(path):
        print(f"Output file not found: {path}")
        return None
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    # Find last JSON block with finalized_specs
    matches = list(re.finditer(
        r'```json\s*(\{[^`]*?"generated_by"[^`]*?\})\s*```', raw, re.DOTALL
    ))
    if not matches:
        print(f"No specs JSON found in output_{mcat_id}.md")
        return None
    try:
        return json.loads(matches[-1].group(1))
    except Exception:
        text = re.sub(r',\s*([}\]])', r'\1', matches[-1].group(1))
        try:
            return json.loads(text)
        except Exception as e:
            print(f"JSON parse error for {mcat_id}: {e}")
            return None


def convert(mcat_id: int, category_name: str, mapping: dict) -> str | None:
    if mcat_id not in mapping:
        print(f"mcat_id {mcat_id} not found in mapping sheet")
        return None

    info  = mapping[mcat_id]
    specs = parse_specs_from_output(mcat_id)
    if not specs:
        return None

    upload_json = {
    "pmcat_id": info["pmcat_id"],
    "pmcat_name": info["pmcat_name"],
    "generated_by": "Spec_Audit_Orchestrator_Agent",
    "mcats": [
        {
            "category_name": category_name,
            "mcat_id": mcat_id,
            "generated_by": "Spec_Audit_Orchestrator_Agent",
            "finalized_specs": specs.get("finalized_specs", {}),
        }
    ]
}
    

    out_path = os.path.join(UPLOAD_DIR, f"upload_{mcat_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(upload_json, f, indent=2, ensure_ascii=False)
    print(f"Upload JSON saved: {out_path}")
    return out_path

