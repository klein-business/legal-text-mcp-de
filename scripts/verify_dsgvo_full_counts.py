#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from legal_texts.validation import validate_generated_package  # type: ignore[import-not-found]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate full DSGVO article and recital counts for a generated package."
    )
    parser.add_argument("--package", required=True, help="Generated package directory to validate.")
    parser.add_argument("--policy", required=True, help="DSGVO source/count policy JSON.")
    parser.add_argument(
        "--output", required=True, help="Path where the dsgvo-full-counts.v1 artifact should be written."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    package_dir = Path(args.package)
    policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
    artifact = validate_dsgvo_full_counts(package_dir, policy)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if artifact["validation_errors"]:
        for error in artifact["validation_errors"]:
            print(error, file=sys.stderr)
        return 1
    return 0


def validate_dsgvo_full_counts(package_dir: Path, policy: dict[str, Any]) -> dict[str, Any]:
    errors = [f"package: {error}" for error in validate_generated_package(package_dir, require_search_index=True)]
    required_policy_fields = (
        "celex",
        "cellar_work",
        "expression",
        "language",
        "document",
        "version_policy",
        "consolidation_policy",
        "content_hash",
        "article_count",
        "recital_count",
    )
    for field in required_policy_fields:
        if not policy.get(field):
            errors.append(f"policy missing {field}")
    norms = json.loads((package_dir / "norms.json").read_text(encoding="utf-8"))
    laws = json.loads((package_dir / "laws.json").read_text(encoding="utf-8"))
    dsgvo_laws = [law for law in laws if law.get("canonical_id") == "dsgvo_eu_2016_679"]
    if not dsgvo_laws:
        errors.append("missing dsgvo_eu_2016_679 law")
        source_metadata = {}
    else:
        source_metadata = dsgvo_laws[0].get("source", {}).get("source_metadata", {})
    article_count = sum(1 for norm in norms if norm.get("law_id") == "dsgvo_eu_2016_679" and norm.get("unit") == "art")
    recital_count = sum(
        1 for norm in norms if norm.get("law_id") == "dsgvo_eu_2016_679" and norm.get("unit") == "recital"
    )
    expected_article_count = policy.get("article_count")
    expected_recital_count = policy.get("recital_count")
    if expected_article_count is not None and article_count != expected_article_count:
        errors.append(f"article_count {article_count} does not match expected {expected_article_count}")
    if expected_recital_count is not None and recital_count != expected_recital_count:
        errors.append(f"recital_count {recital_count} does not match expected {expected_recital_count}")
    for field in (
        "celex",
        "cellar_work",
        "expression",
        "language",
        "document",
        "version_policy",
        "consolidation_policy",
    ):
        if source_metadata.get(field) != policy.get(field):
            errors.append(
                f"source metadata {field} {source_metadata.get(field)} does not match expected {policy.get(field)}"
            )
    source_content_hash = dsgvo_laws[0].get("source", {}).get("content_hash") if dsgvo_laws else None
    if policy.get("content_hash") and source_content_hash != policy.get("content_hash"):
        errors.append("source content_hash does not match policy")
    norm_ids = {norm["norm_id"] for norm in norms if norm.get("law_id") == "dsgvo_eu_2016_679"}
    boundary_samples: dict[str, dict[str, list[str]]] = {
        "articles": {"expected": [], "found": [], "missing": []},
        "recitals": {"expected": [], "found": [], "missing": []},
    }
    for norm_id in policy.get("boundary_samples", {}).get("articles", []):
        boundary_samples["articles"]["expected"].append(norm_id)
        if norm_id not in norm_ids:
            boundary_samples["articles"]["missing"].append(norm_id)
            errors.append(f"missing boundary article {norm_id}")
        else:
            boundary_samples["articles"]["found"].append(norm_id)
    for norm_id in policy.get("boundary_samples", {}).get("recitals", []):
        boundary_samples["recitals"]["expected"].append(norm_id)
        if norm_id not in norm_ids:
            boundary_samples["recitals"]["missing"].append(norm_id)
            errors.append(f"missing boundary recital {norm_id}")
        else:
            boundary_samples["recitals"]["found"].append(norm_id)
    expected_counts = {"articles": expected_article_count, "recitals": expected_recital_count}
    actual_counts = {"articles": article_count, "recitals": recital_count}
    selected_source = {
        "celex": source_metadata.get("celex"),
        "cellar_work": source_metadata.get("cellar_work"),
        "expression": source_metadata.get("expression"),
        "language": source_metadata.get("language"),
        "document": source_metadata.get("document"),
        "version_policy": source_metadata.get("version_policy"),
        "consolidation_policy": source_metadata.get("consolidation_policy"),
        "content_hash": source_content_hash,
    }
    return {
        "schema_version": "dsgvo-full-counts.v1",
        "package": str(package_dir),
        "policy": {
            "celex": policy.get("celex"),
            "cellar_work": policy.get("cellar_work"),
            "expression": policy.get("expression"),
            "language": policy.get("language"),
            "document": policy.get("document"),
            "version_policy": policy.get("version_policy"),
            "consolidation_policy": policy.get("consolidation_policy"),
            "content_hash": policy.get("content_hash"),
        },
        "selected_source": selected_source,
        "expected_counts": expected_counts,
        "actual_counts": actual_counts,
        "counts": actual_counts,
        "boundary_samples": boundary_samples,
        "validation_errors": errors,
    }


if __name__ == "__main__":
    raise SystemExit(main())
