"""Зведення результатів експерименту в таблицю для звіту.

Запуск з кореня репозиторію:
    uv run --project manual-agent python experiments/summarize.py
"""

import glob
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "experiments" / "results"


def load_records() -> list[dict]:
    records = []
    for path in sorted(glob.glob(str(RESULTS / "run_*.jsonl"))):
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    records.append(json.loads(line))
    return records


def tool_signature(record: dict) -> str:
    names = []
    for tool in record["tools"]:
        name = tool.get("tool") or tool.get("action")
        names.append(f"{name}({json.dumps(tool['arguments'], ensure_ascii=False, sort_keys=True)})")
    return "; ".join(names)


def main() -> None:
    records = load_records()
    scores = json.loads((RESULTS / "scores.json").read_text(encoding="utf-8"))
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for record in records:
        groups[(record["model"], record["system"], record["type"])].append(record)

    order = {"oneshot": 0, "manual": 1, "adk": 2}
    lines = [
        "| Тип | Система | Модель | Правильність | Обґрунтованість | Галюцинація | Виклики LLM | Дії | Час, с | Відтворюваність |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for key in sorted(groups, key=lambda k: (k[2], order.get(k[1], 9), k[0], k[1])):
        model, system, qtype = key
        runs = sorted(groups[key], key=lambda r: r["repeat"])
        score = scores.get(f"{model.replace('.', '_')}/{system}/{qtype}", {})
        signatures = {tool_signature(run) for run in runs}
        answers = {(run["answer"] or "").strip() for run in runs}
        if len(signatures) > 1:
            reproducibility = f"{len(signatures)} траєкторії"
        elif len(answers) > 1:
            reproducibility = "траєкторія однакова, текст різний"
        else:
            reproducibility = "повна"
        if len(runs) == 1:
            reproducibility = "—"
        llm = statistics.mean(run["llm_calls"] for run in runs)
        actions = statistics.mean(run["actions"] for run in runs)
        seconds = statistics.mean(run["seconds"] for run in runs)
        lines.append(
            f"| {qtype} | {system} | {model} | {score.get('correctness', '—')} | "
            f"{score.get('grounded', '—')} | {score.get('hallucination', '—')} | "
            f"{llm:g} | {actions:g} | {seconds:.2f} | {reproducibility} |"
        )

    table = "\n".join(lines)
    (RESULTS / "summary.md").write_text(table + "\n", encoding="utf-8")
    print(table)


if __name__ == "__main__":
    main()
