#!/usr/bin/env bash
set -u

cd "$(dirname "${BASH_SOURCE[0]}")"

echo "--- 1. Activate virtual environment if available ---"
if [ -f "./venv/bin/activate" ]; then
  # shellcheck source=/dev/null
  source "./venv/bin/activate"
  echo "Activated ./venv/bin/activate"
else
  echo "WARNING: virtual environment not found at ./venv/bin/activate. Using system Python."
fi

echo "--- 2. Run src/gee.py ---"
GEE_PROJECT_ID="${GEE_PROJECT_ID:-YOUR_PROJECT_ID}"
if [ "${GEE_PROJECT_ID}" = "YOUR_PROJECT_ID" ]; then
  echo "WARNING: GEE_PROJECT_ID is not set. Using placeholder YOUR_PROJECT_ID."
fi

if python3 src/gee.py --project "${GEE_PROJECT_ID}" --output-dir data --verbose --update; then
  echo "SUCCESS: src/gee.py completed."
else
  echo "ERROR: src/gee.py failed. Exiting."
  exit 1
fi

echo "--- 3. Run src/plot_tanks.py ---"
if python3 src/plot_tanks.py --data-dir data --output-dir plots; then
  echo "SUCCESS: src/plot_tanks.py completed."
else
  echo "WARNING: src/plot_tanks.py failed. Continuing after warning."
fi

echo "======================================================"
echo "All done."
