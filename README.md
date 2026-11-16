# lab01-agents

Лабораторна робота № 1 з дисципліни «Штучний інтелект у ПІ»: власний цикл агента
Observe → Reason → Act → Evaluate і той самий агент на Google ADK.

Предметна область — **методи HTTP** (варіант 8). Середовище містить сім перевірених об'єктів
(GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS) із посиланнями на RFC 9110 і RFC 5789. Метод
TRACE навмисно відсутній — він слугує запитом типу D, на якому перевіряється поведінка агента
за відсутності даних.

## Структура

```
manual-agent/     власний цикл без agent framework (agent/, tests/, baseline.py, main.py)
adk-agent/        той самий агент на Google ADK (app/agent.py, app/environment.py)
experiments/      запити, раннери трьох систем, результати й трасування
report/           звіт Typst (ЛБ1_ШІуПІ_Осиченко.typ), рисунки й PDF
scripts/          перевірка середовища і збірка звіту
AGENT-CARD.md     паспорт агента
```

## Швидкий старт

```sh
# власний агент: ключ у manual-agent/.env (GEMINI_API_KEY, GEMINI_MODEL)
cd manual-agent
cp .env.example .env       # вписати ключ
uv run python main.py "Порівняй POST, PUT і PATCH"
uv run python main.py "Що таке методи HTTP?" --mode oneshot
uv run pytest -q

# ADK-агент: ключ у adk-agent/.env
cd ../adk-agent
agents-cli playground      # веб-інтерфейс на http://localhost:8080
agents-cli run "Чи ідемпотентний PATCH?"
agents-cli lint
uv run pytest tests/unit tests/integration
```

## Експеримент

```sh
uv run --project manual-agent python experiments/run_manual.py --system both --repeats 3 --pause 8
cd adk-agent && uv run python ../experiments/run_adk.py --repeats 3 --pause 8
uv run --project manual-agent python experiments/summarize.py   # → experiments/results/summary.md
```

Результати й трасування зберігаються в `experiments/results/`. Локальна модель підключається
через LiteLlm: `ADK_LLM_BACKEND=local LOCAL_MODEL=openai/spark LOCAL_API_BASE=http://127.0.0.1:8095/v1`.

## Звіт

```sh
sh scripts/build_report.sh        # → report/ЛБ1_ШІуПІ_Осиченко.pdf
```

Ключ API зберігається лише у `.env` (права 600, файл у `.gitignore`); у репозиторії є тільки
`.env.example` з порожнім значенням.
