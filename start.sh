#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

if [[ ! -f "venv/bin/activate" ]]; then
  echo "Virtual environment not found at venv/. Create it first:"
  echo "python3 -m venv venv && source venv/bin/activate && pip install -e ."
  exit 1
fi

source venv/bin/activate

required_modules=(fastapi uvicorn langchain_core langgraph)
optional_modules=(multipart)

find_missing_modules() {
  python - "$@" <<'PY'
import importlib.util
import sys

missing = []
for module in sys.argv[1:]:
    if module == "multipart":
        # Accept either modern or legacy import path.
        has_modern = importlib.util.find_spec("python_multipart") is not None
        has_legacy = importlib.util.find_spec("multipart") is not None
        if not (has_modern or has_legacy):
            missing.append("multipart")
        continue
    if importlib.util.find_spec(module) is None:
        missing.append(module)

print(" ".join(missing))
PY
}

missing_required="$(find_missing_modules "${required_modules[@]}")"
if [[ -n "${missing_required}" ]]; then
  echo "Missing required runtime dependencies: ${missing_required}"
  echo "Attempting install: pip install -e ."
  if ! pip install -e .; then
    echo "Dependency install failed."
  fi

  missing_required="$(find_missing_modules "${required_modules[@]}")"
  if [[ -n "${missing_required}" ]]; then
    echo "Startup blocked. Still missing required modules: ${missing_required}"
    echo "Once network is available, run: source venv/bin/activate && pip install -e ."
    exit 1
  fi
fi

missing_optional="$(find_missing_modules "${optional_modules[@]}")"
if [[ -n "${missing_optional}" ]]; then
  echo "Optional module(s) missing: ${missing_optional}"
  echo "/audio/transcribe file uploads will return a fallback response until installed."
fi

exec uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
