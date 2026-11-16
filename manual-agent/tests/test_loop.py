"""Тести циклу без звернень до API: рішення моделі підміняє сценарій."""

from agent.loop import run_agent


def scripted(decisions):
    queue = iter(decisions)

    def decide(goal, observations, step, max_steps):
        return next(queue)

    return decide


def test_lookup_then_finish():
    decide = scripted(
        [
            {
                "action": "lookup_http_method",
                "arguments": {"name": "patch"},
                "decision_summary": "Потрібні дані про PATCH.",
            },
            {
                "action": "finish",
                "arguments": {"answer": "PATCH змінює ресурс частково."},
                "decision_summary": "Даних достатньо.",
            },
        ]
    )
    state = run_agent("Що робить PATCH?", decide=decide)
    assert state.stop_reason == "finish"
    assert state.llm_calls == 2
    assert state.actions == 1
    assert state.observations[0].startswith("patch:")


def test_two_actions_in_one_trajectory():
    decide = scripted(
        [
            {"action": "lookup_http_method", "arguments": {"name": "put"}},
            {"action": "check_property", "arguments": {"method": "put", "property": "idempotent"}},
            {"action": "finish", "arguments": {"answer": "PUT ідемпотентний."}},
        ]
    )
    state = run_agent("Чи ідемпотентний PUT?", decide=decide)
    assert state.actions == 2
    assert state.observations[1].startswith("put: idempotent=yes")
    assert state.stop_reason == "finish"


def test_stops_at_max_steps():
    def endless(goal, observations, step, max_steps):
        return {"action": "lookup_http_method", "arguments": {"name": "get"}}

    state = run_agent("Зациклитися", decide=endless, max_steps=3, max_actions=10)
    assert state.stop_reason == "max_steps"
    assert state.step == 3


def test_stops_at_max_llm_calls():
    def endless(goal, observations, step, max_steps):
        return {"action": "lookup_http_method", "arguments": {"name": "get"}}

    state = run_agent("Зациклитися", decide=endless, max_steps=10, max_llm_calls=2, max_actions=10)
    assert state.stop_reason == "max_llm_calls"
    assert state.llm_calls == 2


def test_stops_at_max_actions():
    def endless(goal, observations, step, max_steps):
        return {"action": "lookup_http_method", "arguments": {"name": "get"}}

    state = run_agent("Зациклитися", decide=endless, max_steps=10, max_llm_calls=10, max_actions=2)
    assert state.stop_reason == "max_actions"
    assert state.actions == 2


def test_invalid_action_becomes_observation():
    decide = scripted(
        [
            {"action": "rm_rf", "arguments": {}},
            {"action": "finish", "arguments": {"answer": "ok"}},
        ]
    )
    state = run_agent("Тест", decide=decide)
    assert state.observations[0].startswith("ERROR: unknown action")
    assert state.stop_reason == "finish"
