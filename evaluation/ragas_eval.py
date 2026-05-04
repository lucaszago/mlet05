"""Offline golden-set evaluation for the finance RAG agent.

This is a deterministic proxy for the Datathon evaluation step. It validates
grounded keyword coverage without requiring external LLM credentials.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from finance.agent import create_finance_agent
from finance.config import ProjectConfig


def evaluate(golden_set_path: Path, config_path: Path) -> dict[str, float]:
    """Evaluate keyword hit rate over the finance golden set."""
    config = ProjectConfig.from_yaml(str(config_path), env="dev")
    agent = create_finance_agent(config)
    total = 0
    hits = 0

    for line in golden_set_path.read_text().splitlines():
        item = json.loads(line)
        answer = agent.answer(item["question"]).answer.lower()
        expected_keywords = [keyword.lower() for keyword in item["expected_keywords"]]
        hits += sum(keyword in answer for keyword in expected_keywords)
        total += len(expected_keywords)

    return {"keyword_hit_rate": hits / total if total else 0.0}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden-set", default="data/golden_set/finance_qa.jsonl")
    parser.add_argument("--config", default="project_config.yml")
    args = parser.parse_args()
    metrics = evaluate(Path(args.golden_set), Path(args.config))
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
