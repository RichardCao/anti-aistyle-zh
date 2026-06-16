#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys

from render_regression_suite import (
    DEFAULT_FIXTURE_PATHS,
    discover_fixture_paths,
    evaluate_case,
    filter_cases,
    flatten_cases,
    lint_fixtures,
    load_fixtures,
    load_output,
)


DEFAULT_CANDIDATE_NAMES = [
    "{id}.md",
    "{id}.txt",
    "{id}.output.md",
    "{id}.out.md",
]

HOTLIST_GROUPS = [
    {
        "label": "negative_parallel",
        "patterns": ["不是", "而是", "不只是", "更是", "问题不在", "而在", "与其", "不如"],
        "warn_above": 2,
    },
    {
        "label": "summary_anchor",
        "patterns": ["真正", "本质", "核心", "关键在于", "说到底", "归根结底"],
        "warn_above": 2,
    },
    {
        "label": "engineering_abstract",
        "patterns": ["路径", "收口", "落地", "闭环", "对齐", "颗粒度", "边界"],
        "warn_above": 2,
    },
    {
        "label": "explanation_glue",
        "patterns": ["也就是说", "换句话说", "这背后", "从某种意义上", "从某个角度看"],
        "warn_above": 1,
    },
    {
        "label": "standard_transition",
        "patterns": ["首先", "其次", "最后", "一方面", "另一方面", "与此同时", "更重要的是"],
        "warn_above": 2,
    },
    {
        "label": "closing_stamp",
        "patterns": ["这就是", "的意义", "最终回到", "变得更加", "留下的不是"],
        "warn_above": 1,
    },
]


def resolve_manifest_path(raw_path):
    path = Path(raw_path)
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def load_manifest(path):
    data = json.loads(resolve_manifest_path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("manifest must be a JSON object mapping case id to output path")
    resolved = {}
    for case_id, raw_path in data.items():
        resolved[case_id] = str(resolve_manifest_path(raw_path))
    return resolved


def resolve_from_dir(case_id, outputs_dir, templates):
    for template in templates:
        candidate = outputs_dir / template.format(id=case_id)
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def resolve_output_path(case, args, manifest):
    if manifest and case["id"] in manifest:
        return Path(manifest[case["id"]])
    if args.outputs_dir:
        return resolve_from_dir(case["id"], Path(args.outputs_dir), args.filename_template)
    return None


def scan_hotlist(text):
    rows = []
    for group in HOTLIST_GROUPS:
        hits = []
        total = 0
        for pattern in group["patterns"]:
            count = text.count(pattern)
            if count:
                hits.append({"pattern": pattern, "count": count})
                total += count
        if total:
            rows.append(
                {
                    "label": group["label"],
                    "total": total,
                    "warn": total > group["warn_above"],
                    "hits": hits,
                }
            )
    return rows


def main():
    parser = argparse.ArgumentParser(description="Batch-check regression suite outputs.")
    parser.add_argument("--fixtures", action="append", help="Load a specific fixture file. Can be repeated.")
    parser.add_argument("--suite", help="Select one suite name.")
    parser.add_argument("--group", help="Filter cases by group tag.")
    parser.add_argument("--category", help="Filter cases by category.")
    parser.add_argument("--id", dest="case_id", action="append", help="Filter to one case id. Can be repeated.")
    parser.add_argument("--manifest", help="JSON object mapping case id to output path.")
    parser.add_argument("--outputs-dir", help="Directory containing output files named by case id.")
    parser.add_argument(
        "--filename-template",
        action="append",
        default=[],
        help="Filename template used with --outputs-dir, e.g. '{id}.md'. Can be repeated.",
    )
    parser.add_argument("--dry-run", action="store_true", help="List selected cases and resolved paths without checking.")
    parser.add_argument("--hotlist-scan", action="store_true", help="Report residual hotlist hits as warnings.")
    parser.add_argument("--json-out", help="Optional path to write JSON results.")
    parser.add_argument("--lint-fixtures", action="store_true", help="Warn about fixture design issues and exit.")
    args = parser.parse_args()

    fixture_paths = discover_fixture_paths(args.fixtures)
    if not fixture_paths:
        print("no fixture files found", file=sys.stderr)
        return 1

    suites = load_fixtures(fixture_paths)
    cases = flatten_cases(suites)

    if args.lint_fixtures:
        rows = lint_fixtures(cases)
        if not rows:
            print("fixture lint: no warnings")
            return 0
        print(f"fixture lint warnings: {sum(len(warnings) for _, warnings in rows)}")
        for case, warnings in rows:
            print(f"- {case['id']} [{case['_suite_name']}]")
            for warning in warnings:
                print(f"  - {warning}")
        return 0

    if not args.manifest and not args.outputs_dir:
        parser.error("one of --manifest or --outputs-dir is required")

    selected = filter_cases(cases, args.case_id, args.category, args.suite, args.group)
    if not selected:
        print("no matching cases", file=sys.stderr)
        return 1

    manifest = load_manifest(args.manifest) if args.manifest else {}
    templates = args.filename_template or DEFAULT_CANDIDATE_NAMES
    if args.outputs_dir:
        args.outputs_dir = str(resolve_manifest_path(args.outputs_dir))
    args.filename_template = templates

    results = []
    missing = 0
    failed = 0
    for case in selected:
        output_path = resolve_output_path(case, args, manifest)
        row = {
            "id": case["id"],
            "suite": case["_suite_name"],
            "category": case["category"],
            "output_path": str(output_path) if output_path else None,
        }

        if args.dry_run:
            row["status"] = "resolved" if output_path else "missing"
            results.append(row)
            continue

        if not output_path or not output_path.exists():
            row["status"] = "missing"
            row["failures"] = ["missing output file"]
            missing += 1
            results.append(row)
            continue

        output_text = load_output(output_path)
        failures = evaluate_case(case, output_text)
        row["status"] = "pass" if not failures else "fail"
        row["failures"] = failures
        if args.hotlist_scan:
            row["hotlist_hits"] = scan_hotlist(output_text)
        if failures:
            failed += 1
        results.append(row)

    if args.json_out:
        out_path = resolve_manifest_path(args.json_out)
        out_path.write_text(
            json.dumps(
                {
                    "fixture_paths": [str(path) for path in fixture_paths],
                    "selected_count": len(selected),
                    "missing": missing,
                    "failed": failed,
                    "results": results,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    print(f"selected: {len(selected)}")
    if args.dry_run:
        for row in results:
            print(f"- {row['id']}: {row['status']} -> {row['output_path']}")
        return 0

    print(f"missing: {missing}")
    print(f"failed: {failed}")
    for row in results:
        status = row["status"].upper()
        print(f"- {row['id']}: {status} -> {row['output_path']}")
        if row.get("failures"):
            for failure in row["failures"]:
                print(f"  - {failure}")
        if args.hotlist_scan and row.get("hotlist_hits"):
            for hit_group in row["hotlist_hits"]:
                mark = "WARN" if hit_group["warn"] else "info"
                details = ", ".join(f"{hit['pattern']}={hit['count']}" for hit in hit_group["hits"])
                print(f"  - hotlist {mark} {hit_group['label']}: total={hit_group['total']} ({details})")

    return 0 if missing == 0 and failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
