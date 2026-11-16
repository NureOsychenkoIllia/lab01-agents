# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ADK-версія агента з методів HTTP (варіант 8 лабораторної роботи № 1).

Той самий environment.py, що і у власного агента, але цикл, валідацію виклику
інструмента і диспетчер виконує ADK.
"""

import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from .environment import check_property, lookup_http_method

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

INSTRUCTION = """
ROLE: навчальний агент із методів HTTP для студентів-програмістів.

PURPOSE: відповідати на питання про методи HTTP лише на основі перевірених даних,
які повертають інструменти lookup_http_method і check_property.

LANGUAGE: українська, якщо користувач не попросив іншу мову.

BEHAVIOR RULES:
1. Перед відповіддю про конкретний метод виклич lookup_http_method для кожного
   згаданого методу окремо.
2. Якщо питання стосується безпечності або ідемпотентності, виклич check_property
   з аргументами method (наприклад "put") і property ("safe" або "idempotent").
3. Якщо результат інструмента починається з NOT_FOUND, прямо скажи, що перевірених
   даних немає, і не добудовуй відповідь із власних знань.
4. У відповіді про конкретні методи використовуй лише факти з результатів інструментів.
5. Не викликай інструмент повторно з тим самим аргументом.
6. На загальні питання про методи HTTP відповідай коротко без виклику інструментів.
7. Порівнюючи методи, спирайся на факти з результатів lookup_http_method; check_property
   викликай додатково лише тоді, коли користувач прямо питає про безпечність
   чи ідемпотентність.

LIMITATIONS: не виконуй дій, для яких немає інструментів; не вигадуй джерел,
методів, статус-кодів і заголовків, яких немає в результатах інструментів.
"""


def build_model() -> Gemini | object:
    """Повертає модель ADK: Gemini API або локальний OpenAI-сумісний сервер."""
    if os.getenv("ADK_LLM_BACKEND", "gemini").strip().lower() == "local":
        from google.adk.models.lite_llm import LiteLlm

        return LiteLlm(
            model=os.getenv("LOCAL_MODEL", "openai/spark"),
            api_base=os.getenv("LOCAL_API_BASE", "http://127.0.0.1:8080/v1"),
            api_key=os.getenv("LOCAL_API_KEY", "local"),
        )
    return Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=3))


root_agent = Agent(
    name="adk_agent",
    model=build_model(),
    instruction=INSTRUCTION,
    tools=[lookup_http_method, check_property],
)

app = App(
    root_agent=root_agent,
    name="app",
)
