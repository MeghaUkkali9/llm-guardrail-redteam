from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from red_team.evaluators import EvalResult


def print_console_summary(results: list[EvalResult]) -> None:
    by_category: dict[str, list[EvalResult]] = defaultdict(list)
    for r in results:
        by_category[r.category].append(r)

    print("\n=== Red Team Results ===\n")
    total_passed = sum(1 for r in results if r.passed)
    print(f"Overall: {total_passed}/{len(results)} passed\n")

    for category, cat_results in by_category.items():
        passed = sum(1 for r in cat_results if r.passed)
        print(f"{category}: {passed}/{len(cat_results)}")
        for r in cat_results:
            if not r.passed:
                print(f"  FAIL [{r.test_id}] {r.prompt[:70]!r} — {r.reason}")
    print()


def write_markdown_report(results: list[EvalResult], path: Path) -> None:
    by_category: dict[str, list[EvalResult]] = defaultdict(list)
    for r in results:
        by_category[r.category].append(r)

    total_passed = sum(1 for r in results if r.passed)
    lines = [
        "# Red Team Report",
        "",
        f"Run at: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"**Overall: {total_passed}/{len(results)} passed**",
        "",
        "| Category | Pass rate |",
        "|---|---|",
    ]
    for category, cat_results in by_category.items():
        passed = sum(1 for r in cat_results if r.passed)
        lines.append(f"| {category} | {passed}/{len(cat_results)} |")

    lines.append("")
    lines.append("## Failures")
    lines.append("")
    failures = [r for r in results if not r.passed]
    if not failures:
        lines.append("None — every test case behaved as expected.")
    for r in failures:
        lines.append(f"### {r.test_id} ({r.category})")
        lines.append(f"- **Prompt:** {r.prompt}")
        lines.append(f"- **Expected:** {r.expect}")
        lines.append(f"- **Reason:** {r.reason}")
        lines.append(f"- **Answer:** {r.answer[:300]}")
        lines.append("")

    lines.append("## All results")
    lines.append("")
    lines.append("| ID | Category | Expected | Result | Reason |")
    lines.append("|---|---|---|---|---|")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        reason = r.reason.replace("|", "/")[:80]
        lines.append(f"| {r.test_id} | {r.category} | {r.expect} | {status} | {reason} |")

    path.write_text("\n".join(lines))
