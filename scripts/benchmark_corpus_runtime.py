#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MCP_ROOT = ROOT / "mcp"
if str(MCP_ROOT) not in sys.path:
    sys.path.insert(0, str(MCP_ROOT))

from legal_texts.dataset import NormalizedDataset  # noqa: E402
from legal_texts.errors import LegalTextError  # noqa: E402
from legal_texts.search import SearchService  # noqa: E402


SCHEMA_VERSION = "corpus-runtime-benchmark.v1"
DEFAULT_QUERIES = ("personenbezogene", "daten", "schutz", "werbung", "widerrufsrecht")


def package_size_bytes(package_dir: Path) -> int:
    return sum(path.stat().st_size for path in package_dir.rglob("*") if path.is_file())


def estimate_size_bytes(value: Any, seen: set[int] | None = None) -> int:
    seen = seen or set()
    object_id = id(value)
    if object_id in seen:
        return 0
    seen.add(object_id)
    size = sys.getsizeof(value)
    if isinstance(value, dict):
        size += sum(estimate_size_bytes(key, seen) + estimate_size_bytes(item, seen) for key, item in value.items())
    elif isinstance(value, (list, tuple, set, frozenset)):
        size += sum(estimate_size_bytes(item, seen) for item in value)
    elif hasattr(value, "__dict__"):
        size += estimate_size_bytes(vars(value), seen)
    return size


def percentile_95(samples: list[float]) -> float:
    if not samples:
        return 0.0
    if len(samples) == 1:
        return samples[0]
    return statistics.quantiles(samples, n=20, method="inclusive")[18]


def build_migration_decisions(
    *,
    load_time_ms: float,
    search_p95_ms: float,
    memory_mb: float,
    thresholds: dict[str, float],
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    if load_time_ms > thresholds["max_load_ms"]:
        decisions.append(
            {
                "decision": "review_dataset_loading_strategy",
                "reason": "load_time_ms exceeds threshold",
                "observed": round(load_time_ms, 3),
                "threshold": thresholds["max_load_ms"],
            }
        )
    if search_p95_ms > thresholds["max_search_p95_ms"]:
        decisions.append(
            {
                "decision": "consider_external_or_persisted_search_index",
                "reason": "sampled_search_p95_ms exceeds threshold",
                "observed": round(search_p95_ms, 3),
                "threshold": thresholds["max_search_p95_ms"],
            }
        )
    if memory_mb > thresholds["max_memory_mb"]:
        decisions.append(
            {
                "decision": "consider_memory_mapped_or_chunked_runtime_loading",
                "reason": "estimated_memory_mb exceeds threshold",
                "observed": round(memory_mb, 3),
                "threshold": thresholds["max_memory_mb"],
            }
        )
    return decisions


def run_benchmark(
    package_dir: Path,
    *,
    queries: list[str] | None = None,
    thresholds: dict[str, float] | None = None,
) -> tuple[dict[str, Any], int]:
    thresholds = thresholds or {
        "max_load_ms": 120000.0,
        "max_search_p95_ms": 1000.0,
        "max_memory_mb": 2048.0,
    }
    queries = queries or list(DEFAULT_QUERIES)
    validation_errors: list[str] = []
    dataset: NormalizedDataset | None = None
    search: SearchService | None = None
    load_time_ms = 0.0
    search_timings: list[dict[str, Any]] = []

    start = time.perf_counter()
    try:
        dataset = NormalizedDataset.load(package_dir, require_search_index=True)
    except LegalTextError as exc:
        validation_errors.append(exc.message)
        validation_errors.extend(str(item) for item in exc.details.get("errors", []))
    except Exception as exc:  # noqa: BLE001 - converted into structured benchmark output.
        validation_errors.append(f"{type(exc).__name__}: {exc}")
    finally:
        load_time_ms = (time.perf_counter() - start) * 1000

    if dataset is not None:
        search = SearchService(dataset)
        for query in queries:
            query_start = time.perf_counter()
            try:
                result = search.search_laws(query)
                error = None
                result_count = result["count"]
            except LegalTextError as exc:
                error = exc.code
                result_count = 0
            elapsed = (time.perf_counter() - query_start) * 1000
            search_timings.append(
                {
                    "query": query,
                    "elapsed_ms": round(elapsed, 3),
                    "result_count": result_count,
                    "error": error,
                }
            )

    search_p95_ms = percentile_95([item["elapsed_ms"] for item in search_timings])
    dataset_memory_bytes = estimate_size_bytes(dataset) if dataset is not None else 0
    search_memory_bytes = estimate_size_bytes(search) if search is not None else 0
    memory_bytes = dataset_memory_bytes + search_memory_bytes
    dataset_memory_mb = dataset_memory_bytes / (1024 * 1024)
    search_memory_mb = search_memory_bytes / (1024 * 1024)
    memory_mb = memory_bytes / (1024 * 1024)
    migration_decisions = build_migration_decisions(
        load_time_ms=load_time_ms,
        search_p95_ms=search_p95_ms,
        memory_mb=memory_mb,
        thresholds=thresholds,
    )
    if validation_errors:
        status = "failed"
    elif migration_decisions:
        status = "passed_with_migration_decisions"
    else:
        status = "passed"

    benchmark = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "package_dir": str(package_dir),
        "environment": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "pid": os.getpid(),
        },
        "thresholds": thresholds,
        "status": status,
        "record_counts": {
            "laws": len(dataset.laws) if dataset is not None else 0,
            "norms": len(dataset.norms) if dataset is not None else 0,
            "source_limitations": len(dataset.source_limitations) if dataset is not None else 0,
            "relationships": len(dataset.relationships) if dataset is not None else 0,
        },
        "package_size_bytes": package_size_bytes(package_dir) if package_dir.exists() else 0,
        "load_time_ms": round(load_time_ms, 3),
        "sampled_search": {
            "queries": queries,
            "timings": search_timings,
            "p95_ms": round(search_p95_ms, 3),
        },
        "dataset_memory_bytes": dataset_memory_bytes,
        "dataset_memory_mb": round(dataset_memory_mb, 3),
        "search_memory_bytes": search_memory_bytes,
        "search_memory_mb": round(search_memory_mb, 3),
        "combined_memory_bytes": memory_bytes,
        "combined_memory_mb": round(memory_mb, 3),
        "estimated_memory_bytes": memory_bytes,
        "estimated_memory_mb": round(memory_mb, 3),
        "migration_decisions": migration_decisions,
        "validation_errors": validation_errors,
    }
    return benchmark, 0 if not validation_errors else 1


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark normalized corpus runtime loading and search.")
    parser.add_argument("--package-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--query", action="append", dest="queries")
    parser.add_argument("--max-load-ms", type=float, default=120000.0)
    parser.add_argument("--max-search-p95-ms", type=float, default=1000.0)
    parser.add_argument("--max-memory-mb", type=float, default=2048.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    benchmark, exit_code = run_benchmark(
        args.package_dir,
        queries=args.queries,
        thresholds={
            "max_load_ms": args.max_load_ms,
            "max_search_p95_ms": args.max_search_p95_ms,
            "max_memory_mb": args.max_memory_mb,
        },
    )
    write_json(args.output, benchmark)
    if exit_code:
        for error in benchmark["validation_errors"]:
            print(error, file=sys.stderr)
        for decision in benchmark["migration_decisions"]:
            print(f"{decision['decision']}: {decision['reason']}", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
