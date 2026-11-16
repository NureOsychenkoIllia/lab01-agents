import argparse
import json
import time
from pathlib import Path

from agent.loop import MAX_ACTIONS, MAX_LLM_CALLS, MAX_STEPS, run_agent
from agent.reasoning import MODEL
from baseline import one_shot_answer


def save_trace(state, limits: dict[str, int]) -> Path:
    Path("traces").mkdir(exist_ok=True)
    path = Path("traces") / f"trace_{time.strftime('%Y%m%d_%H%M%S')}.json"
    payload = {
        "goal": state.goal,
        "model": MODEL,
        "limits": limits,
        "stop_reason": state.stop_reason,
        "steps": state.step,
        "llm_calls": state.llm_calls,
        "actions": state.actions,
        "final_answer": state.final_answer,
        "trace": state.trace,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Мінімальний AI-агент (ЛР 1, методи HTTP)")
    parser.add_argument("goal", help="мета агента в лапках")
    parser.add_argument("--mode", choices=["agent", "oneshot"], default="agent")
    parser.add_argument("--max-steps", type=int, default=MAX_STEPS)
    parser.add_argument("--max-actions", type=int, default=MAX_ACTIONS)
    parser.add_argument("--max-llm-calls", type=int, default=MAX_LLM_CALLS)
    args = parser.parse_args()

    print(f"MODEL: {MODEL}")
    started = time.perf_counter()

    if args.mode == "oneshot":
        print(one_shot_answer(args.goal))
        print(f"\n[one-shot] LLM calls: 1, time: {time.perf_counter() - started:.2f} s")
        return

    limits = {
        "max_steps": args.max_steps,
        "max_actions": args.max_actions,
        "max_llm_calls": args.max_llm_calls,
    }
    state = run_agent(
        args.goal,
        max_steps=args.max_steps,
        max_actions=args.max_actions,
        max_llm_calls=args.max_llm_calls,
    )

    print("\nFINAL ANSWER:\n" + (state.final_answer or ""))
    print(
        f"\n[agent] steps: {state.step}, LLM calls: {state.llm_calls}, "
        f"actions: {state.actions}, stop: {state.stop_reason}, "
        f"time: {time.perf_counter() - started:.2f} s"
    )
    print(f"trace saved: {save_trace(state, limits)}")


if __name__ == "__main__":
    main()
