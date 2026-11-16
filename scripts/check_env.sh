#!/bin/sh
# Контрольна перевірка середовища (таблиця 3.1 методичних вказівок).
echo "OS: $(. /etc/os-release && echo "$PRETTY_NAME")"
git --version
uv --version
uv python list | grep -m 2 "cpython-3.12"
typst --version
agents-cli --version
(cd adk-agent && uv run python -c "import importlib.metadata as m; print('google-adk', m.version('google-adk'))")
(cd manual-agent && uv run python -c "import sys; print('python', sys.version.split()[0])")
git check-ignore -v manual-agent/.env adk-agent/.env
