"""Оркестрація: цикл Observe → Reason → Validate → Act → Update → Evaluate."""

import time
from collections.abc import Callable
from typing import Any

from .environment import check_property, lookup_http_method
from .errors import DecisionError
from .reasoning import get_decision
from .state import AgentState
from .validator import validate_decision

MAX_STEPS = 6
MAX_ACTIONS = 6
MAX_LLM_CALLS = 8

# Функцію рішень передають параметром: у тестах її замінює сценарій без LLM
DecideFn = Callable[[str, list[str], int, int], dict]


def execute_action(decision: dict, state: AgentState) -> str | None:
    """Dispatcher: перетворює перевірене рішення на виклик Python-функції."""
    action = decision["action"]
    args = decision["arguments"]

    if action == "lookup_http_method":
        state.actions += 1
        return lookup_http_method(args["name"])
    if action == "check_property":
        state.actions += 1
        return check_property(args["method"], args["property"])
    if action == "finish":
        state.final_answer = args["answer"]
        state.finished = True
        state.stop_reason = "finish"
        return None

    raise DecisionError(f"no handler for action {action!r}")


def print_step(record: dict) -> None:
    print(f"\nSTEP {record['step']}")
    print(f"  ACTION: {record['action']} {record['arguments'] or ''}")
    if record.get("decision_summary"):
        print(f"  DECISION: {record['decision_summary']}")
    if record["observation"] is not None:
        print(f"  OBSERVATION: {record['observation']}")


def stop_with(state: AgentState, reason: str, message: str) -> None:
    state.finished = True
    state.stop_reason = reason
    state.final_answer = message


def run_agent(
    goal: str,
    decide: DecideFn = get_decision,
    max_steps: int = MAX_STEPS,
    max_actions: int = MAX_ACTIONS,
    max_llm_calls: int = MAX_LLM_CALLS,
) -> AgentState:
    state = AgentState(goal=goal)

    while not state.finished:
        # EVALUATE (бюджет): усі ліміти перевіряють до нового виклику LLM
        if state.step >= max_steps:
            stop_with(
                state,
                "max_steps",
                f"Агент зупинився: вичерпано ліміт кроків ({max_steps}) без фінальної відповіді.",
            )
            break
        if state.llm_calls >= max_llm_calls:
            stop_with(
                state,
                "max_llm_calls",
                f"Агент зупинився: вичерпано ліміт викликів моделі ({max_llm_calls}).",
            )
            break
        if state.actions >= max_actions:
            stop_with(
                state,
                "max_actions",
                f"Агент зупинився: вичерпано ліміт дій у середовищі ({max_actions}).",
            )
            break

        state.step += 1
        record: dict[str, Any] = {"step": state.step}
        decision: dict | None = None
        started = time.perf_counter()

        try:
            state.llm_calls += 1  # OBSERVE + REASON
            decision = decide(state.goal, state.observations, state.step, max_steps)
            validate_decision(decision)  # VALIDATE
            observation = execute_action(decision, state)  # ACT
            record.update(
                action=decision["action"],
                arguments=decision["arguments"],
                decision_summary=decision.get("decision_summary", ""),
            )
        except DecisionError as exc:
            # Помилка стає спостереженням, і модель отримує шанс виправитися
            observation = f"ERROR: {exc}"
            record.update(
                action="rejected",
                arguments=None,
                decision_summary="",
                rejected=decision,
            )
        except Exception as exc:  # критична помилка: без мережі або ключа далі йти нікуди
            record.update(action="failed", arguments=None, decision_summary="", error=repr(exc))
            record["observation"] = None
            record["seconds"] = round(time.perf_counter() - started, 2)
            state.trace.append(record)
            stop_with(state, "llm_error", f"Агент зупинився: помилка виклику моделі ({exc}).")
            break

        record["observation"] = observation
        record["seconds"] = round(time.perf_counter() - started, 2)
        state.trace.append(record)

        if observation is not None:
            state.observations.append(observation)  # UPDATE STATE

        print_step(record)

    return state
