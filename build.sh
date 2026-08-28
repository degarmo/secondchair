#!/usr/bin/env bash
# Render build step.
set -o errexit

pip install uv
uv sync --frozen

cd frontend && npm ci && npm run build && cd ..

uv run python manage.py collectstatic --no-input
uv run python manage.py migrate
