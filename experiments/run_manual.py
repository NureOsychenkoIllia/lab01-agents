"""Експеримент частини В для власного агента і базової лінії one-shot.

Запуск з кореня репозиторію:
    uv run --project manual-agent python experiments/run_manual.py --system both --repeats 3
"""

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "manual-agent"))

from agent.loop import MAX_ACTIONS, MAX_LLM_CALLS, MAX_STEPS, run_agent  # noqa: E402
from agent.reasoning import MODEL  # noqa: E402
from baseline import one_shot_answer  # noqa: E402

QUERIES = json.loads((ROOT / "experiments" / "queries.json").read_text(encoding="utf-8"))
RESULTS = ROOT / "experiments" / "results"
TRACES = RESULTS / "traces"


def record(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def run_oneshot(query: dict, repeat: int, out: Path) -> None:
    started = time.perf_counter()
    error = None
    try:
        answer = one_shot_answer(query["query"])
    except Exception as exc:  # відмова API — теж результат вимірювання
        answer, error = "", repr(exc)
    record(
        out,
        {
            "system": "oneshot",
            "model": MODEL,
            "type": query["type"],
            "query": query["query"],
            "repeat": repeat,
            "seconds": round(time.perf_counter() - started, 2),
            "llm_calls": 0 if error else 1,
            "actions": 0,
            "stop_reason": "api_error" if error else "single_call",
            "answer": answer,
            "error": error,
            "tools": [],
        },
    )


def run_agent_once(query: dict, repeat: int, out: Path) -> None:
    started = time.perf_counter()
    state = run_agent(query["query"])
    elapsed = round(time.perf_counter() - started, 2)
    TRACES.mkdir(parents=True, exist_ok=True)
    trace_path = TRACES / f"manual_{query['type']}_r{repeat}.json"
    trace_path.write_text(
        json.dumps(
            {
                "goal": state.goal,
                "model": MODEL,
                "limits": {
                    "max_steps": MAX_STEPS,
                    "max_actions": MAX_ACTIONS,
                    "max_llm_calls": MAX_LLM_CALLS,
                },
                "stop_reason": state.stop_reason,
                "steps": state.step,
                "llm_calls": state.llm_calls,
                "actions": state.actions,
                "trace": state.trace,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    tools = [
        {"action": step["action"], "arguments": step["arguments"]}
        for step in state.trace
        if step["action"] in {"lookup_http_method", "check_property"}
    ]
    record(
        out,
        {
            "system": "manual",
            "model": MODEL,
            "type": query["type"],
            "query": query["query"],
            "repeat": repeat,
            "seconds": elapsed,
            "llm_calls": state.llm_calls,
            "actions": state.actions,
            "stop_reason": state.stop_reason,
            "answer": state.final_answer,
            "tools": tools,
            "trace": str(trace_path.relative_to(ROOT)),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", choices=["oneshot", "manual", "both"], default="both")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--pause", type=float, default=5.0)
    parser.add_argument("--types", default="A,B,C,D,E", help="які типи запитів виконувати")
    parser.add_argument("--out", default=None, help="файл результатів (типово новий)")
    args = parser.parse_args()

    selected = [query for query in QUERIES if query["type"] in args.types.split(",")]
    out = Path(args.out) if args.out else RESULTS / f"run_manual_{time.strftime('%Y%m%d_%H%M%S')}.jsonl"
    print(f"model={MODEL} repeats={args.repeats} out={out}")
    for repeat in range(1, args.repeats + 1):
        for query in selected:
            if args.system in {"oneshot", "both"}:
                run_oneshot(query, repeat, out)
                print(f"[one-shot] {query['type']} r{repeat} done")
                time.sleep(args.pause)
            if args.system in {"manual", "both"}:
                run_agent_once(query, repeat, out)
                print(f"[manual] {query['type']} r{repeat} done")
                time.sleep(args.pause)


if __name__ == "__main__":
    main()
