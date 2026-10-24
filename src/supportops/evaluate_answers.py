"""Heuristic evaluation of RAG answer completeness."""

import json
import re
import time
from pathlib import Path
from typing import Any

from supportops.service import RAGService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "evaluation" / "golden_answers.jsonl"


def normalize(text: str) -> str:
    """Normalize text so punctuation and capitalization matter less."""
    text = re.sub(r"[^\w]+", " ", text.lower(), flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def load_cases(path: Path) -> list[dict[str, Any]]:
    """Read and validate the JSONL evaluation dataset."""
    cases = []

    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue

        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON on line {line_number} of {path}"
            ) from exc

        if "question" not in case or "required_checks" not in case:
            raise ValueError(
                f"Missing question or required_checks on line {line_number}"
            )

        cases.append(case)

    if not cases:
        raise ValueError(f"No evaluation cases found in {path}")

    return cases


def check_any(answer: str, terms: list[str]) -> bool:
    return any(normalize(term) in answer for term in terms)


def evaluate_case(
    answer_text: str,
    case: dict[str, Any],
) -> dict[str, Any]:
    """Check required answer points and known forbidden phrases."""
    answer = normalize(answer_text)
    checks = case["required_checks"]
    passed_checks = []

    for check in checks:
        all_terms = check.get("all", [])
        any_terms = check.get("any", [])

        passed_all = all(
            normalize(term) in answer for term in all_terms
        )
        passed_any = not any_terms or check_any(answer, any_terms)

        passed = passed_all and passed_any

        passed_checks.append(
            {
                "name": check["name"],
                "passed": passed,
            }
        )

    forbidden_found = [
        phrase
        for phrase in case.get("forbidden_phrases", [])
        if normalize(phrase) in answer
    ]

    total_checks = len(passed_checks)
    checks_passed = sum(
        int(check["passed"]) for check in passed_checks
    )
    coverage = checks_passed / total_checks if total_checks else 0.0

    return {
        "checks": passed_checks,
        "checks_passed": checks_passed,
        "checks_total": total_checks,
        "coverage": coverage,
        "forbidden_found": forbidden_found,
        "passed": coverage == 1.0 and not forbidden_found,
    }


def main() -> None:
    cases = load_cases(DATASET_PATH)
    service = RAGService()

    total_passed = 0
    total_coverage = 0.0
    total_latency = 0.0

    print(f"Evaluating answer quality on {len(cases)} questions\n")

    for index, case in enumerate(cases, start=1):
        start = time.perf_counter()

        result = service.answer(case["question"])

        latency = (time.perf_counter() - start) * 1000
        answer_text = result["answer"]

        evaluation = evaluate_case(answer_text, case)

        total_passed += int(evaluation["passed"])
        total_coverage += evaluation["coverage"]
        total_latency += latency

        status = "PASS" if evaluation["passed"] else "FAIL"

        print(f"{index:02d}. {status} | {case['question']}")
        print(
            f"    Required checks: "
            f"{evaluation['checks_passed']}/"
            f"{evaluation['checks_total']}"
        )
        print(f"    Coverage: {evaluation['coverage']:.1%}")
        print(f"    Latency: {latency:.0f} ms")

        for check in evaluation["checks"]:
            check_status = "OK" if check["passed"] else "MISSING"
            print(f"    [{check_status}] {check['name']}")

        if evaluation["forbidden_found"]:
            print(
                "    [WARNING] Forbidden phrases found: "
                + ", ".join(evaluation["forbidden_found"])
            )

        print("    Answer:")
        print(f"    {answer_text}\n")

    count = len(cases)

    print("=" * 60)
    print(f"Cases passing all checks: {total_passed}/{count}")
    print(f"Average checklist coverage: {total_coverage / count:.1%}")
    print(f"Average latency: {total_latency / count:.0f} ms")
    print(
        "\nNote: keyword-based checks are diagnostic heuristics. "
        "They do not prove correctness or faithfulness."
    )


if __name__ == "__main__":
    main()