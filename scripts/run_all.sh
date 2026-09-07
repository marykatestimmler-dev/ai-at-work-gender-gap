#!/usr/bin/env bash
# Reproduce everything from the raw Census file. Requires python3 (see requirements.txt) and node with the `docx` package.
set -e; cd "$(dirname "$0")/.."
python3 scripts/00_download_data.py
python3 scripts/01_build_analytic_file.py
python3 scripts/01b_build_tables.py
python3 scripts/02_gender_analysis.py
python3 scripts/02b_build_gender_tables.py
python3 scripts/03_charts_main.py
python3 scripts/04_charts_gender.py
python3 scripts/05_chart_linkedin.py
node scripts/06_build_main_report.js
node scripts/07_build_gender_addendum.js
echo "done"
