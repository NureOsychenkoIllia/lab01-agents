# manual-agent

Мінімальний AI-агент із власним циклом Observe → Reason → Act → Evaluate (лабораторна робота № 1,
варіант 8 — методи HTTP). Без agent framework: цикл, стан, валідатор і диспетчер написані вручну.

## Запуск

```sh
cp .env.example .env    # вписати GEMINI_API_KEY
uv run python main.py "Порівняй POST, PUT і PATCH"
uv run python main.py "Що таке методи HTTP?" --mode oneshot
uv run pytest -q
```
