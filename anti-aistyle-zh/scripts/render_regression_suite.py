#!/usr/bin/env python3
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE_PATHS = sorted(ROOT.glob("assets/*regression_fixtures.json"))
DEFAULT_PUNCTUATION_TOKENS = ["，", "。", "；", "：", "？", "！", "“", "”", "‘", "’", "（", "）", "《", "》", "、", "——", "…"]
SENTENCE_SPLIT_RE = re.compile(r"[。！？!?；;\n]+")
PROCESS_TERMS = ["诊断", "执行回执", "manifest", "结构层 hard fail", "异构配额表", "主模板覆盖率"]
FACT_DETAIL_RE = re.compile(r"(\d+[点时]|早上|清晨|中午|下午|傍晚|收工前|路|街|院|楼|站|机构|医院|学校|公司)")


def discover_fixture_paths(cli_paths):
    if not cli_paths:
        return DEFAULT_FIXTURE_PATHS

    paths = []
    for raw_path in cli_paths:
        path = Path(raw_path)
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        paths.append(path)
    return paths


def load_fixture(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if "cases" not in data or not isinstance(data["cases"], list):
        raise ValueError(f"{path}: fixtures must contain a 'cases' list")

    for case in data["cases"]:
        if "id" not in case or "category" not in case:
            raise ValueError(f"{path}: invalid fixture case: {case}")
        case["_suite_name"] = data["suite_name"]
        case["_fixture_path"] = str(path)

    return data


def load_fixtures(paths):
    suites = []
    seen_ids = set()
    for path in paths:
        suite = load_fixture(path)
        suites.append(suite)
        for case in suite["cases"]:
            if case["id"] in seen_ids:
                raise ValueError(f"duplicate fixture id: {case['id']}")
            seen_ids.add(case["id"])
    return suites


def flatten_cases(suites):
    cases = []
    for suite in suites:
        cases.extend(suite["cases"])
    return cases


def filter_cases(cases, case_id=None, category=None, suite=None, group=None):
    selected = cases
    if case_id:
        if isinstance(case_id, (list, tuple, set)):
            wanted = set(case_id)
            selected = [case for case in selected if case["id"] in wanted]
        else:
            selected = [case for case in selected if case["id"] == case_id]
    if category:
        selected = [case for case in selected if case["category"] == category]
    if suite:
        selected = [case for case in selected if case["_suite_name"] == suite]
    if group:
        selected = [case for case in selected if group in case.get("groups", [])]
    return selected


def render_summary(suites):
    print("fixture suites:")
    for suite in suites:
        counts = {}
        for case in suite["cases"]:
            counts[case["category"]] = counts.get(case["category"], 0) + 1
        print(f"- suite: {suite['suite_name']}")
        print(f"  version: {suite['version']}")
        print(f"  fixture: {suite['cases'][0]['_fixture_path'] if suite['cases'] else 'n/a'}")
        print(f"  required input: {suite['default_call_policy']['only_required_input']}")
        print("  optional controls: " + ", ".join(suite["default_call_policy"]["optional_controls"]))
        print("  case counts:")
        for key in sorted(counts):
            print(f"    - {key}: {counts[key]}")


def render_case(case):
    print(f"## {case['id']} [{case['category']}]")
    print(f"suite: {case['_suite_name']}")
    print(f"text_type: {case['text_type']}")
    print(f"call_mode: {case.get('call_mode', 'default_only')}")
    print("risk_tags: " + ", ".join(case.get("risk_tags", [])))
    print(f"preferred_output_mode: {case.get('preferred_output_mode', '默认')}")
    print()
    print("prompt:")
    print(build_prompt(case))
    if "input" in case:
        print("目标文本：")
        print(case["input"])
    else:
        print("目标文本批次：")
        for item in case["input_batch"]:
            print(f"- {item}")
    print()
    content_assertions, process_assertions = assertion_sections(case["assertions"])
    if process_assertions:
        if content_assertions:
            print("content assertions:")
            for key, value in content_assertions.items():
                print(f"- {key}: {value}")
            print()
        print("process assertions:")
        for key, value in process_assertions.items():
            print(f"- {key}: {value}")
    else:
        print("assertions:")
        for key, value in content_assertions.items():
            print(f"- {key}: {value}")
    print()


def build_prompt(case):
    call_mode = case.get("call_mode", "default_only")
    if call_mode == "use_preferred_output_mode":
        return (
            "请用 $anti-aistyle-zh 处理下面中文文本。"
            f"只额外指定一个可选控制项：输出模式 = {case.get('preferred_output_mode', '默认')}。"
            "不要再补其他控制项。"
        )
    if call_mode == "validation_receipt":
        return (
            "请用 $anti-aistyle-zh 处理下面中文文本。"
            "这次任务属于控制项验证 / 过程审计。"
            "默认输出仍以最终成稿为主，但在最终内容之后附最短执行回执。"
            "不要再补其他控制项。"
        )
    if call_mode in {"audit", "regression"}:
        return (
            "请用 $anti-aistyle-zh 处理下面中文文本。"
            f"这次任务属于{'回归验证' if call_mode == 'regression' else '过程审计'}。"
            "默认输出仍以最终成稿为主，但在最终内容之后附最短执行回执。"
            "不要再补其他控制项。"
        )
    return "请用 $anti-aistyle-zh 处理下面中文文本。除了目标文本，不额外提供任何控制项。"


def load_output(path):
    return Path(path).read_text(encoding="utf-8")


def extract_nonempty_lines(text):
    return [line.strip() for line in text.splitlines() if line.strip()]


def extract_sentences(text):
    sentences = []
    for chunk in SENTENCE_SPLIT_RE.split(text):
        cleaned = chunk.strip().strip("\"'“”‘’()（）")
        if cleaned:
            sentences.append(cleaned)
    return sentences


def count_patterns(text, patterns):
    return sum(text.count(pattern) for pattern in patterns)


def check_patterns(text, key, patterns, should_exist, failures):
    for pattern in patterns:
        exists = pattern in text
        if should_exist and not exists:
            failures.append(f"{key}: missing `{pattern}`")
        if not should_exist and exists:
            failures.append(f"{key}: found forbidden `{pattern}`")


def check_any_patterns(text, key, patterns, failures):
    if patterns and not any(pattern in text for pattern in patterns):
        joined = ", ".join(f"`{pattern}`" for pattern in patterns)
        failures.append(f"{key}: need at least one of {joined}")


def check_batch_diversity(text, failures):
    lines = extract_nonempty_lines(text)
    if len(lines) < 2:
        failures.append("batch_diversity: need at least 2 non-empty lines")
        return
    opening_tokens = [line[:6] for line in lines]
    closing_tokens = [line[-6:] for line in lines]
    if len(set(opening_tokens)) == 1:
        failures.append("batch_diversity: repeated opening pattern")
    if len(set(closing_tokens)) == 1:
        failures.append("batch_diversity: repeated closing pattern")


def assertion_sections(assertions):
    if isinstance(assertions, dict) and (
        isinstance(assertions.get("content"), dict) or isinstance(assertions.get("process"), dict)
    ):
        return assertions.get("content", {}), assertions.get("process", {})
    return assertions, {}


def should_check_process_assertions(case):
    return (
        case.get("call_mode") == "validation_receipt"
        or case.get("preferred_output_mode") == "分层审计"
        or case.get("call_mode") in {"audit", "regression"}
    )


def effective_assertions(case):
    content_assertions, process_assertions = assertion_sections(case["assertions"])
    merged = dict(content_assertions)
    if should_check_process_assertions(case):
        for key, value in process_assertions.items():
            if key in merged and isinstance(merged[key], list) and isinstance(value, list):
                merged[key] = merged[key] + value
            elif key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = {**merged[key], **value}
            else:
                merged[key] = value
    return merged


def check_max_added_details(case, output_text, assertions, failures):
    if "input" not in case:
        return
    max_added = assertions.get("max_added_details")
    if max_added is None:
        return
    input_len = len(case["input"])
    output_len = len(output_text)
    if output_len > input_len + max_added * 20:
        failures.append(
            f"max_added_details: output too long for allowed added details "
            f"({output_len} > {input_len} + {max_added}*20)"
        )


def check_min_nonempty_lines(output_text, assertions, failures):
    minimum = assertions.get("min_nonempty_lines")
    if minimum is None:
        return
    line_count = len(extract_nonempty_lines(output_text))
    if line_count < minimum:
        failures.append(f"min_nonempty_lines: need at least {minimum}, got {line_count}")


def check_min_char_ratio(case, output_text, assertions, failures):
    if "input" not in case:
        return
    minimum = assertions.get("min_char_ratio")
    if minimum is None:
        return
    input_len = len(case["input"])
    output_len = len(output_text)
    if input_len == 0:
        return
    ratio = output_len / input_len
    if ratio < minimum:
        failures.append(f"min_char_ratio: need at least {minimum}, got {ratio:.3f}")


def check_nonincreasing_patterns(case, output_text, assertions, failures):
    if "input" not in case:
        return
    patterns = assertions.get("nonincreasing_patterns", [])
    if not patterns:
        return
    input_text = case["input"]
    for pattern in patterns:
        before = input_text.count(pattern)
        after = output_text.count(pattern)
        if after > before:
            failures.append(
                f"nonincreasing_patterns: `{pattern}` increased from {before} to {after}"
            )


def check_nonincreasing_pattern_groups(case, output_text, assertions, failures):
    if "input" not in case:
        return
    groups = assertions.get("nonincreasing_pattern_groups", [])
    if not groups:
        return
    input_text = case["input"]
    for group in groups:
        label = group.get("label", "pattern_group")
        patterns = group.get("patterns", [])
        before = count_patterns(input_text, patterns)
        after = count_patterns(output_text, patterns)
        if after > before:
            failures.append(
                f"nonincreasing_pattern_groups[{label}]: increased from {before} to {after}"
            )


def check_max_total_pattern_groups(output_text, assertions, failures):
    groups = assertions.get("max_total_pattern_groups", [])
    if not groups:
        return
    for group in groups:
        label = group.get("label", "pattern_group")
        patterns = group.get("patterns", [])
        max_total = group.get("max_total")
        if max_total is None:
            continue
        total = count_patterns(output_text, patterns)
        if total > max_total:
            failures.append(
                f"max_total_pattern_groups[{label}]: need <= {max_total}, got {total}"
            )


def check_min_punctuation_kinds(output_text, assertions, failures):
    minimum = assertions.get("min_punctuation_kinds")
    if minimum is None:
        return
    punctuation_tokens = assertions.get("punctuation_tokens", DEFAULT_PUNCTUATION_TOKENS)
    present = [token for token in punctuation_tokens if token in output_text]
    kind_count = len(set(present))
    if kind_count < minimum:
        failures.append(f"min_punctuation_kinds: need at least {minimum}, got {kind_count}")


def check_sentence_prefix_repeat(output_text, assertions, failures):
    config = assertions.get("sentence_prefix_repeat")
    if not config:
        return
    prefix_len = config.get("prefix_len", 4)
    max_repeat = config.get("max_repeat")
    if max_repeat is None:
        return
    sentences = extract_sentences(output_text)
    prefixes = [sentence[:prefix_len] for sentence in sentences if len(sentence) >= prefix_len]
    if not prefixes:
        return
    counts = Counter(prefixes)
    repeated_prefix, repeat_count = counts.most_common(1)[0]
    if repeat_count > max_repeat:
        failures.append(
            f"sentence_prefix_repeat: `{repeated_prefix}` repeated {repeat_count} times, need <= {max_repeat}"
        )


def evaluate_case(case, output_text):
    failures = []
    assertions = effective_assertions(case)
    check_patterns(output_text, "remove_patterns", assertions.get("remove_patterns", []), False, failures)
    check_patterns(output_text, "forbid_patterns", assertions.get("forbid_patterns", []), False, failures)
    check_patterns(output_text, "require_patterns", assertions.get("require_patterns", []), True, failures)
    check_patterns(
        output_text, "must_preserve_patterns", assertions.get("must_preserve_patterns", []), True, failures
    )
    check_patterns(output_text, "preserve_keywords", assertions.get("preserve_keywords", []), True, failures)
    check_patterns(
        output_text, "batch_forbid_patterns", assertions.get("batch_forbid_patterns", []), False, failures
    )
    check_any_patterns(output_text, "require_any_patterns", assertions.get("require_any_patterns", []), failures)
    check_min_nonempty_lines(output_text, assertions, failures)
    check_max_added_details(case, output_text, assertions, failures)
    check_min_char_ratio(case, output_text, assertions, failures)
    check_nonincreasing_patterns(case, output_text, assertions, failures)
    check_nonincreasing_pattern_groups(case, output_text, assertions, failures)
    check_max_total_pattern_groups(output_text, assertions, failures)
    check_min_punctuation_kinds(output_text, assertions, failures)
    check_sentence_prefix_repeat(output_text, assertions, failures)

    if assertions.get("require_diverse_openings") or assertions.get("require_diverse_closings"):
        check_batch_diversity(output_text, failures)

    return failures


def lint_case(case):
    warnings = []
    assertions = case.get("assertions", {})
    content_assertions, process_assertions = assertion_sections(assertions)
    call_mode = case.get("call_mode", "default_only")

    if call_mode == "default_only":
        require_patterns = content_assertions.get("require_patterns", []) + content_assertions.get("require_any_patterns", [])
        for pattern in require_patterns:
            if any(term in pattern for term in PROCESS_TERMS):
                warnings.append(f"default_only content requires process term `{pattern}`")
    if process_assertions and not should_check_process_assertions(case) and not case.get("process_documentation_only"):
        warnings.append("process assertions are present but this case mode will not check them")
    if content_assertions.get("max_added_details") is not None and "input" not in case:
        warnings.append("max_added_details is only supported for single-text `input` cases")

    for pattern in content_assertions.get("remove_patterns", []):
        if FACT_DETAIL_RE.search(pattern):
            warnings.append(f"remove_patterns may contain factual detail `{pattern}`; confirm it is template shell, not evidence")

    return warnings


def lint_fixtures(cases):
    rows = []
    for case in cases:
        warnings = lint_case(case)
        if warnings:
            rows.append((case, warnings))
    return rows


def list_suites(suites):
    for suite in suites:
        print(suite["suite_name"])


def main():
    parser = argparse.ArgumentParser(description="Render anti-aistyle regression fixtures.")
    parser.add_argument("--summary", action="store_true", help="Print suite summary.")
    parser.add_argument("--fixtures", action="append", help="Load a specific fixture file. Can be repeated.")
    parser.add_argument("--suite", help="Select cases from one suite name.")
    parser.add_argument("--list-suites", action="store_true", help="Print available suite names.")
    parser.add_argument("--id", dest="case_id", action="append", help="Render one case by id. Can be repeated.")
    parser.add_argument("--category", help="Render cases by category.")
    parser.add_argument("--group", help="Render cases by group tag.")
    parser.add_argument("--check-output", help="Evaluate a single output file against the selected case.")
    parser.add_argument("--lint-fixtures", action="store_true", help="Warn about fixture design issues.")
    args = parser.parse_args()

    fixture_paths = discover_fixture_paths(args.fixtures)
    if not fixture_paths:
        print("no fixture files found", file=sys.stderr)
        return 1

    suites = load_fixtures(fixture_paths)
    cases = flatten_cases(suites)

    if args.list_suites:
        list_suites(suites)
        return 0

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

    if args.summary or (not args.case_id and not args.category and not args.suite and not args.group):
        render_summary(suites)
        if not args.case_id and not args.category and not args.suite and not args.group:
            return 0

    selected = filter_cases(cases, args.case_id, args.category, args.suite, args.group)
    if not selected:
        print("no matching cases", file=sys.stderr)
        return 1
    if args.check_output and len(selected) != 1:
        print("--check-output requires exactly one selected case", file=sys.stderr)
        return 1

    if args.check_output:
        output_text = load_output(args.check_output)
        failures = evaluate_case(selected[0], output_text)
        print(f"case: {selected[0]['id']}")
        print(f"suite: {selected[0]['_suite_name']}")
        print(f"result: {'PASS' if not failures else 'FAIL'}")
        if failures:
            print("failures:")
            for failure in failures:
                print(f"- {failure}")
            return 1
        return 0

    for index, case in enumerate(selected):
        if index:
            print("---")
        render_case(case)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
