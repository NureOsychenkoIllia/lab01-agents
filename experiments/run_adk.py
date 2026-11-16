"""Експеримент частини В для ADK-агента.

Запуск з каталогу adk-agent:
    uv run python ../experiments/run_adk.py --repeats 1 --pause 5
"""

import argparse
import asyncio
import json
import os
import time
from pathlib import Path

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import MODEL, root_agent

ROOT = Path(__file__).resolve().parents[1]
QUERIES = json.loads((ROOT / "experiments" / "queries.json").read_text(encoding="utf-8"))
RESULTS = ROOT / "experiments" / "results"
TRACES = RESULTS / "traces"


def model_label() -> str:
    if os.getenv("ADK_LLM_BACKEND", "gemini").strip().lower() == "local":
        return f"local:{os.getenv('LOCAL_MODEL', 'openai/spark')}"
    return MODEL


async def run_once(query: dict, repeat: int, label: str) -> dict:
    session_service = InMemorySessionService()
    session = await session_service.create_session(user_id="experiment", app_name="app")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="app")
    message = types.Content(role="user", parts=[types.Part.from_text(text=query["query"])])

    started = time.perf_counter()
    events = [
        event
        async for event in runner.run_async(
            new_message=message,
            user_id="experiment",
            session_id=session.id,
        )
    ]
    elapsed = round(time.perf_counter() - started, 2)

    llm_calls = 0
    tools = []
    answer_parts = []
    for event in events:
        content = event.content
        parts = list(content.parts or []) if content else []
        if event.model_version:
            llm_calls += 1
        for part in parts:
            if part.function_call:
                tools.append(
                    {
                        "tool": part.function_call.name,
                        "arguments": dict(part.function_call.args or {}),
                    }
                )
            if part.text:
                answer_parts.append(part.text)

    TRACES.mkdir(parents=True, exist_ok=True)
    trace_path = TRACES / f"adk_{label}_{query['type']}_r{repeat}.json"
    trace_path.write_text(
        json.dumps([event.model_dump(mode="json") for event in events], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "system": "adk",
        "model": model_label(),
        "type": query["type"],
        "query": query["query"],
        "repeat": repeat,
        "seconds": elapsed,
        "llm_calls": llm_calls,
        "actions": len(tools),
        "stop_reason": "final_text" if answer_parts else "no_text",
        "answer": "\n".join(answer_parts).strip(),
        "tools": tools,
        "trace": str(trace_path.relative_to(ROOT)),
    }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--pause", type=float, default=5.0)
    parser.add_argument("--label", default="gemini")
    args = parser.parse_args()

    out = RESULTS / f"run_adk_{args.label}_{time.strftime('%Y%m%d_%H%M%S')}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f"model={model_label()} repeats={args.repeats} out={out}")

    for repeat in range(1, args.repeats + 1):
        for query in QUERIES:
            result = await run_once(query, repeat, args.label)
            with out.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")
            print(
                f"[adk] {query['type']} r{repeat}: llm={result['llm_calls']} "
                f"tools={result['actions']} {result['seconds']} s"
            )
            await asyncio.sleep(args.pause)


if __name__ == "__main__":
    asyncio.run(main())
