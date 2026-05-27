#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_MD="${SCRIPT_DIR}/EVALUATION_REPORT.md"
OUTPUT_PDF="${SCRIPT_DIR}/EVALUATION_REPORT.pdf"

if [[ ! -f "${INPUT_MD}" ]]; then
  echo "Missing ${INPUT_MD}. Generate the Markdown report first."
  exit 1
fi

if command -v pandoc >/dev/null 2>&1; then
  if command -v xelatex >/dev/null 2>&1; then
    pandoc "${INPUT_MD}" -o "${OUTPUT_PDF}" --pdf-engine=xelatex
    echo "Generated ${OUTPUT_PDF} with pandoc + xelatex."
    exit 0
  fi

  echo "pandoc is installed, but xelatex is missing."
  echo "Install a LaTeX engine or export the Markdown to PDF from VS Code."
  exit 1
fi

cat <<EOF
Pandoc is not installed.

Recommended options on this machine:
1. Install pandoc and a LaTeX engine, then rerun this script.
2. Open ${INPUT_MD} in VS Code and use a Markdown-to-PDF extension.
3. Print the rendered Markdown page to PDF from a browser or editor.
EOF

exit 1
