#!/bin/sh
# Збірка звіту: typst створює PDF поруч із .typ, root — корінь репозиторію,
# щоб лістинги в додатках читалися з manual-agent/, adk-agent/ і experiments/.
set -e
cd "$(dirname "$0")/../report"
typst compile --root .. "ЛБ1_ШІуПІ_Осиченко.typ"
echo "written report/ЛБ1_ШІуПІ_Осиченко.pdf"
