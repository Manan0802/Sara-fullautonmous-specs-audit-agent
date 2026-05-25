"""
Data aggregation helpers for spec-audit-agent.
Skills are now .md knowledge files — NOT sub-agents.
This file only contains data aggregation logic (no LLM calls).
"""
import json
from collections import defaultdict


# ──────────────────────────────────────────────────────────────────────
# Public aggregation functions (used by agent.py)
# ──────────────────────────────────────────────────────────────────────

def aggregate_ds1(ds1_raw: list) -> list:
    """Aggregate Buyer Call Data by spec_name. Returns sorted by product count."""
    if not ds1_raw:
        return []
    # Already aggregated check
    if isinstance(ds1_raw[0], dict) and "total_product_count" in ds1_raw[0]:
        return ds1_raw
    if isinstance(ds1_raw[0], dict) and "spec_name" in ds1_raw[0] and "option_value" not in ds1_raw[0]:
        return ds1_raw

    specs = defaultdict(lambda: {"total_product_count": 0, "example_values": []})
    for row in ds1_raw:
        if not isinstance(row, dict):
            continue
        spec = row.get("spec_name", "").strip()
        val = row.get("option_value", "").strip()
        count = int(row.get("prod_count", 0))
        if not spec:
            continue
        specs[spec]["total_product_count"] += count
        if val and val not in specs[spec]["example_values"] and len(specs[spec]["example_values"]) < 5:
            specs[spec]["example_values"].append(val)
    result = [
        {"spec_name": k, "total_product_count": v["total_product_count"], "example_values": v["example_values"]}
        for k, v in specs.items()
    ]
    result = [r for r in result if r["total_product_count"] > 2]
    return sorted(result, key=lambda x: x["total_product_count"], reverse=True)


def aggregate_ds2(ds2_raw: list, min_count: int = 5) -> list:
    """Aggregate Custom Specs by spec_name. Returns sorted by count."""
    if not ds2_raw:
        return []
    specs = defaultdict(lambda: {"count": 0, "options": []})
    for row in ds2_raw:
        if not isinstance(row, dict):
            continue
        spec = row.get("spec_name", "").strip()
        val = row.get("option_value", "").strip()
        if not spec:
            continue
        specs[spec]["count"] += 1
        if val and val not in specs[spec]["options"] and len(specs[spec]["options"]) < 5:
            specs[spec]["options"].append(val)
    result = [
        {"spec_name": k, "count": v["count"], "options": v["options"]}
        for k, v in specs.items()
    ]
    result = [r for r in result if r["count"] >= min_count]
    return sorted(result, key=lambda x: x["count"], reverse=True)


def aggregate_ds3(ds3_raw: list, min_impressions: int = 50, top_n: int = 10) -> list:
    """Aggregate Buyer Search Data by spec_name. Returns top N by impressions."""
    if not ds3_raw:
        return []
    # Already aggregated check
    if isinstance(ds3_raw[0], dict) and "total_impressions" in ds3_raw[0]:
        return ds3_raw

    specs = defaultdict(lambda: {"total_impressions": 0, "options": []})
    for row in ds3_raw:
        if not isinstance(row, dict):
            continue
        spec = row.get("spec_name") or row.get("Spec Name", "")
        spec = str(spec).strip()
        val = row.get("spec_option") or row.get("Spec Option", "")
        val = str(val).strip()
        try:
            imp = int(float(row.get("impression") or row.get("Impression", 0)))
        except (ValueError, TypeError):
            imp = 0
        if not spec:
            continue
        specs[spec]["total_impressions"] += imp
        if val and val not in specs[spec]["options"] and len(specs[spec]["options"]) < 5:
            specs[spec]["options"].append(val)
    result = [
        {"spec_name": k, "total_impressions": v["total_impressions"], "options": v["options"]}
        for k, v in specs.items()
    ]
    result = [r for r in result if r["total_impressions"] >= min_impressions]
    return sorted(result, key=lambda x: x["total_impressions"], reverse=True)[:top_n]
