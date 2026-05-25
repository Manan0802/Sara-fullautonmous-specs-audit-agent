"""
Data fetchers for spec-audit-agent.
Each function catches all exceptions and returns [] or raises clearly.
"""
import re
import io
import csv
import json
import requests

def get_mcat_id(row):
    for key in row.keys():
        normalized = key.strip().lower().replace(" ", "_")
        if normalized in ["mcat_id", "category_id", "mcat id", "categoryid"]:
            return str(row[key]).strip()
    return ""

# ──────────────────────────────────────────────────────────────────────
# DS-0: Current platform spec sheet (3-hop fetch)
# ──────────────────────────────────────────────────────────────────────

def fetch_ds0(mcat_id) -> dict:
    """
    3-hop fetch to get current platform spec sheet.
    Raises on failure (caller must handle).
    """
    # Hop 1 — get presigned-url metadata
    hop1_url = f"https://get-presigned-url-for-mcat-w2yrp7i6za-el.a.run.app/?mcat_id={mcat_id}"
    resp1 = requests.get(hop1_url, timeout=60)
    resp1.raise_for_status()
    meta = resp1.json()

    # Hop 2 — extract GCS URL with priority fallback
    gcs_url = _extract_gcs_url(meta)
    if not gcs_url:
        raise Exception("DS0: could not extract GCS URL")

    # Hop 3 — download & parse spec JSON from GCS
    resp3 = requests.get(gcs_url, timeout=60)
    resp3.raise_for_status()
    data = resp3.json()

    # Flatten specs from tiers
    primary   = (data.get("finalized_specs", {})
                     .get("finalized_primary_specs", {})
                     .get("specs", []) or [])
    secondary = (data.get("finalized_specs", {})
                     .get("finalized_secondary_specs", {})
                     .get("specs", []) or [])
    tertiary  = (data.get("finalized_specs", {})
                     .get("finalized_tertiary_specs", {})
                     .get("specs", []) or [])

    current_specs = []
    for tier_name, tier_list in [("Primary", primary),
                                  ("Secondary", secondary),
                                  ("Tertiary", tertiary)]:
        for s in tier_list:
            current_specs.append({
                "spec_name":  s.get("spec_name"),
                "options":    s.get("options", []),
                "input_type": s.get("input_type", "radio_button"),
                "tier":       tier_name,
            })

    return {
        "mcat_id":       data.get("mcat_id"),
        "mcat_name":     data.get("category_name"),
        "current_specs": current_specs,
        "raw":           data,
    }


def _extract_gcs_url(meta: dict) -> str | None:
    """Priority-based extraction of the GCS download URL."""
    # Priority 1: dict-style file_info
    try:
        url = meta["finalized_specs"]["file_info"]["url"]
        if url:
            return url
    except (KeyError, TypeError):
        pass

    # Priority 2: list-style file_info
    try:
        file_info = meta["finalized_specs"]["file_info"]
        if isinstance(file_info, list) and file_info:
            entry = file_info[0]
            url = entry.get("url") or entry.get("download_url")
            if url:
                return url
    except (KeyError, TypeError):
        pass

    # Priority 3: regex scan of full JSON string
    full_text = json.dumps(meta)
    match = re.search(r'https://storage\.googleapis\.com/[^\s"\']+', full_text)
    if match:
        return match.group(0)

    return None


# ──────────────────────────────────────────────────────────────────────
# DS-1: Buyer ISQ / call data
# ──────────────────────────────────────────────────────────────────────

def fetch_ds1_raw(mcat_id) -> list:
    """Fetch buyer ISQ data CSV and return option-level rows."""
    try:
        # Step 1 — metadata
        url = f"https://get-buyer-isq-details-w2yrp7i6za-el.a.run.app/?mcat_id={mcat_id}"
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        # Step 2 — locate CSV URL
        step_files = (data.get("steps", {})
                          .get("step_11_normalizer_output", {})
                          .get("root_files", []))
        norm_files = (data.get("normalization", {})
                          .get("final_stats", []))

        csv_url = None
        for f in step_files:
            if f.get("filename") == "updated_spec_value_counts_cumulative.csv":
                csv_url = f.get("url")
                break
        if not csv_url:
            for f in norm_files:
                if f.get("filename") == "final_spec_value_counts_cumulative.csv":
                    csv_url = f.get("url")
                    break

        if not csv_url:
            print("[DS-1] Warning: could not find CSV URL. Returning empty.")
            return []

        # Step 3 — download & parse CSV
        csv_resp = requests.get(csv_url, timeout=60)
        csv_resp.raise_for_status()
        reader = csv.DictReader(io.StringIO(csv_resp.text))

        # Step 4 — process rows
        results = []
        for row in reader:
            spec  = row.get("normalised_spec_name", "").strip()
            value = row.get("normalised_spec_value", "").strip()
            unit  = row.get("normalised_spec_value_unit", "").strip()
            if unit:
                value = f"{value} {unit}"
            count = int(float(row.get("prod_count", 0)))
            if spec and value:
                results.append({
                    "spec_name":    spec,
                    "option_value": value,
                    "prod_count":   count,
                })
        return results

    except Exception as e:
        print(f"[DS-1] Warning: {e}")
        return []


# ──────────────────────────────────────────────────────────────────────
# DS-2: Custom spec data (Google Sheet CSV export)
# ──────────────────────────────────────────────────────────────────────

def fetch_ds2_raw(mcat_id) -> list:
    """Fetch custom spec CSV and filter by mcat_id."""
    try:
        url = "https://docs.google.com/spreadsheets/d/1kApKRPgaVH0qlaKA-J0l2Yy5L2KmdaR7/export?format=csv"
        resp = requests.get(url, timeout=90)
        resp.raise_for_status()
        reader = csv.DictReader(io.StringIO(resp.text))

        results = []
        for row in reader:
            if get_mcat_id(row) == str(mcat_id):
                results.append({
                    "mcat_id":      row.get("mcat_id", "").strip(),
                    "mcat_name":    row.get("mcat_name", "").strip(),
                    "spec_name":    row.get("spec_name", "").strip(),
                    "option_value": row.get("option_value", "").strip(),
                })
        return results

    except Exception as e:
        print(f"[DS-2] Warning: {e}")
        return []


# ──────────────────────────────────────────────────────────────────────
# DS-3: Buyer search data (Google Sheet CSV export)
# ──────────────────────────────────────────────────────────────────────

def fetch_ds3_raw(category_name) -> list:
    """Fetch buyer search CSV and filter by category_name."""
    try:
        url = "https://docs.google.com/spreadsheets/d/1krL9KbJOjBpbsS7DXrVgRZgsiWkhrmD2HF8NOp_JzJ8/export?format=csv"
        resp = requests.get(url, timeout=90)
        resp.raise_for_status()
        reader = csv.DictReader(io.StringIO(resp.text))

        results = []
        for row in reader:
            if row.get("mcat_name", "").strip().lower() == category_name.strip().lower():
                results.append({
                    "mcat_name":   row.get("mcat_name", "").strip(),
                    "spec_name":   row.get("spec_name", "").strip(),
                    "spec_option": row.get("spec_option", "").strip(),
                    "impression":  (row.get("Impression") or row.get("impression", "")).strip(),
                })
        return results

    except Exception as e:
        print(f"[DS-3] Warning: {e}")
        return []


# ──────────────────────────────────────────────────────────────────────
# DS-4: Spec fill rate data (Google Sheet CSV export)
# ──────────────────────────────────────────────────────────────────────

def fetch_ds4_raw(mcat_id) -> list:
    """Fetch spec fill rate CSV and filter by mcat_id."""
    try:
        url = "https://docs.google.com/spreadsheets/d/1JF7Hh7DDCx9XieL4U4EoJLPQtdDxctl7wZYbfvAwb5I/export?format=csv"
        resp = requests.get(url, timeout=90)
        resp.raise_for_status()
        reader = csv.DictReader(io.StringIO(resp.text))

        results = []
        for row in reader:
            if get_mcat_id(row) == str(mcat_id):
                results.append({
                    "spec_name":      row.get("spec_name", "").strip(),
                    "spec_fill_rate": row.get("spec_fill_rate", "").strip(),
                    "product_count":  row.get("product_count", "").strip(),
                })
        return results

    except Exception as e:
        print(f"[DS-4] Warning: {e}")
        return []


# ──────────────────────────────────────────────────────────────────────
# DS-5: Option fill rate data (Google Sheet CSV export)
# ──────────────────────────────────────────────────────────────────────

def fetch_ds5_raw(mcat_id) -> list:
    """Fetch option fill rate CSV and filter by mcat_id."""
    try:
        url = "https://docs.google.com/spreadsheets/d/1bTB2AXhoydP282fWPxoFt9nZ8rj5iI3DSzpKQ9Cu194/export?format=csv"
        resp = requests.get(url, timeout=90)
        resp.raise_for_status()
        reader = csv.DictReader(io.StringIO(resp.text))

        results = []
        for row in reader:
            if get_mcat_id(row) == str(mcat_id):
                results.append({
                    "spec_name":         row.get("spec_name", "").strip(),
                    "spec_option_name":  row.get("spec_option_name", "").strip(),
                    "option_fill_rate":  row.get("option_fill_rate", "").strip(),
                })
        return results

    except Exception as e:
        print(f"[DS-5] Warning: {e}")
        return []
