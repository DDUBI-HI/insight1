#!/bin/bash
# Cloud-session setup for slide-svg: create the project venv and install the
# /slide pipeline dependencies so preflight / export work from the first turn.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

if [ ! -x .venv/bin/python3 ]; then
  python3 -m venv .venv
fi

# Pipeline deps + the PNG renderer used by svg_to_pptx's Office-compat (_svg) export.
.venv/bin/pip install --quiet --disable-pip-version-check \
  -r .claude/skills/slide/requirements.txt cairosvg rlPyCairo

.claude/skills/slide/scripts/_py.sh .claude/skills/slide/scripts/preflight.py
