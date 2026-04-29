#!/usr/bin/env bash
set -euo pipefail

echo "### Starting project setup"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Require the same Python version used by the hosting environment
if command -v python3.12 >/dev/null 2>&1; then
    PYTHON_BIN="python3.12"
else
    echo "Error: python3.12 is required for this project and was not found on PATH."
    echo "Please install Python 3.12 and run this script again."
    exit 1
fi

echo "### Using interpreter: $PYTHON_BIN"

# Recreate broken venv if needed
if [ -d ".venv" ]; then
    if [ ! -x ".venv/bin/python" ]; then
        echo "### Existing .venv looks broken. Recreating it."
        rm -rf .venv
    fi
fi

# Create venv if missing
if [ ! -d ".venv" ]; then
    echo "### Creating virtual environment"
    "$PYTHON_BIN" -m venv .venv
fi

echo "### Activating virtual environment"
# shellcheck disable=SC1091
source .venv/bin/activate

VENV_PYTHON="$(pwd)/.venv/bin/python"
VENV_PIP="$(pwd)/.venv/bin/pip"

echo "### Upgrading pip tools"
"$VENV_PYTHON" -m pip install --upgrade pip setuptools wheel

if [ -f "requirements.txt" ]; then
    echo "### Installing dependencies"
    "$VENV_PIP" install -r requirements.txt
else
    echo "Error: requirements.txt not found."
    exit 1
fi

# Create .env if needed
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    echo "### Creating .env from .env.example"
    cp .env.example .env
elif [ ! -f ".env" ]; then
    echo "### Creating empty .env"
    touch .env
fi

echo "### Running migrations"
"$VENV_PYTHON" manage.py migrate

# Optional: collect static if Django project uses it
echo "### Collecting static files"
"$VENV_PYTHON" manage.py collectstatic --noinput || true

# Optional: seed data if your project has this command
if "$VENV_PYTHON" manage.py help | grep -q "seed"; then
    echo "### Running seed command"
    "$VENV_PYTHON" manage.py seed || true
fi

echo "### Setup complete"
echo "### To activate later, run: source .venv/bin/activate"
echo "### Run Development Server"
echo "### source .venv/bin/activate"
echo "### python manage.py runserver"
