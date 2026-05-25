import os
import json
import re


def load_prompt(filename: str) -> str:
    path = os.path.join("prompts", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def parse_json_response(text: str) -> dict:
    import re, json
    text = re.sub(r"```json|```", "", text).strip()
    text = re.sub(r",\s*([}\]])", r"\1", text)
    try:
        parsed = json.loads(text)
        # If array returned, wrap it
        if isinstance(parsed, list):
            return {"results": parsed}
        return parsed
    except Exception:
        pass
    # Try finding JSON object
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            cleaned = re.sub(r",\s*([}\]])", r"\1", match.group())
            return json.loads(cleaned)
        except Exception:
            pass
    # Try finding JSON array
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            return {"results": json.loads(match.group())}
        except Exception:
            pass
    return {"error": "parse_failed", "raw": text[:500]}


def save_input_txt(mcat_id, category_name, seller_specs_raw: dict):
    with open("input.txt", "w", encoding="utf-8") as f:
        f.write(f"category_id: {mcat_id}\n")
        f.write(f"category_name: {category_name}\n")
        f.write(f"seller_specs:\n{json.dumps(seller_specs_raw, indent=2)}")
    print("input.txt saved.")




def save_dataa_txt(ds0, ds1, ds2, ds3, ds4, ds5, mcat_id):
    data_dump = {
        'DS-0 (Platform Specs)': ds0,
        'DS-1 (Buyer Call Data)': ds1,
        'DS-2 (Custom Specs)': ds2,
        'DS-3 (Buyer Search Data)': ds3,
        'DS-4 (Fill Rate Data)': ds4,
        'DS-5 (Option Fill Rate Data)': ds5
    }
    os.makedirs("data", exist_ok=True)
    path = os.path.join("data", f"data_{mcat_id}.txt")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data_dump, f, indent=4, ensure_ascii=False)
    print(f"data/data_{mcat_id}.txt saved.")
