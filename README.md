# DataScope — Fresh Python + Streamlit Project

## Files
- `app.py` — complete app UI and logic
- `requirements.txt` — dependencies
- `START_DATASCOPE.bat` — installs dependencies and launches the app
- `DIAGNOSE.bat` — checks Python/Streamlit setup
- `.streamlit/config.toml` — theme and 200 MB upload limit
- `sample_data/sample_sales.csv` — test dataset

## Run on Windows
1. Extract this ZIP into a normal folder (not inside the ZIP preview).
2. Install Python 3.10+ if it is not installed: https://www.python.org/downloads/
3. During installation, tick **Add python.exe to PATH**.
4. Double-click `START_DATASCOPE.bat`. The first run needs internet to install packages.
5. Wait for Streamlit to open the app at `http://localhost:8501`.

## Test
Upload `sample_data/sample_sales.csv` first. It has numeric and text columns to test preview, quality, charts, correlation, and downloads.

## Features
- CSV, XLSX and XLS upload
- Dataset overview metrics and file information
- Searchable data preview and column information
- Missing values, blank cells, duplicates and per-column quality report
- Numeric descriptive statistics
- Quick snapshot of numeric, category and date columns
- Total, average, smallest and largest values for a selected numeric column
- Top-five category chart and monthly totals when a date column is recognized
- Interactive Plotly charts
- Correlation heatmap
- Download dataset CSV, quality report CSV and combined Excel report

## Important
This is a Streamlit app and requires Python. Excel files use `openpyxl` (`.xlsx`) and `xlrd` (`.xls`). Install the dependencies from `requirements.txt` and run the app once in the target environment before publishing.

Text dates are detected from recognizable date-like values and ambiguous dates are interpreted day-first (DD/MM) in the monthly trend. The Excel workbook contains Data, Quality Report, and Overview sheets; Excel export is unavailable when the dataset exceeds worksheet limits. Spreadsheet-formula-like text is prefixed with an apostrophe in downloads for safety.
