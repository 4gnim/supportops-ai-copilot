"""Small, deterministic retrieval evaluation; it does not call the LLM."""

import json
from pathlib import Path

from supportops.config import settings
from supportops.service import RAGService


def load_cases(path: Path) -> list[dict]:
    cases = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            cases.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_number} of {path}") from exc
    if not cases:
        raise ValueError(f"No evaluation cases found in {path}")
    return cases


def main() -> None:
    cases = load_cases(settings.evaluation_dataset_path)
    service = RAGService()
    hits = 0
    print(f"Evaluating retrieval on {len(cases)} questions (top_k={settings.top_k})\n")

    for index, case in enumerate(cases, start=1):
        query = case["question"]
        expected_sources = set(case["expected_sources"])
        results = service.retrieve(query, k=settings.top_k)
        found_sources = {item["source"] for item in results}
        hit = bool(expected_sources & found_sources)
        hits += int(hit)
        print(f"{index:02d}. {'PASS' if hit else 'FAIL'} | {query}")
        print(f"    expected: {', '.join(sorted(expected_sources))}")
        print(f"    retrieved: {', '.join(sorted(found_sources)) or '(none)'}")

    hit_rate = hits / len(cases)
    print(f"\nSource Hit@{settings.top_k}: {hits}/{len(cases)} = {hit_rate:.1%}")
    print("This is a small diagnostic set, not proof of production quality.")


if __name__ == "__main__":
    main()
