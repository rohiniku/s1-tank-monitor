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

echo "--- 4. Run src/ai_reporter.py (Gemini) ---"
if python3 src/ai_reporter.py --data-dir data --output-dir reports; then
  echo "SUCCESS: src/ai_reporter.py completed."
else
  echo "ERROR: src/ai_reporter.py failed. Exiting."
  exit 1
fi

echo "--- 5. Run src/build_page.py ---"
if python3 src/build_page.py --input-dir reports --plots-dir plots --artifacts-dir .; then
  echo "SUCCESS: src/build_page.py completed."
else
  echo "ERROR: src/build_page.py failed. Exiting."
  exit 1
fi

echo "======================================================"
echo "All done."
