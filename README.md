# tagexcel

A desktop data processing application for Windows 10/11. Load, clean, analyze, transform, and visualize spreadsheet data with AI-assisted operations -- all in a native GUI.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)

## Features

- **File Import** -- Load CSV, Excel (.xls, .xlsx) files with automatic encoding detection
- **Data Parsing** -- Clean data: strip whitespace, detect null sentinels, remove duplicates, infer types, normalize Vietnamese diacritics (Unicode NFC), parse dates
- **Join/Merge** -- Left, right, inner, and outer joins between two dataframes with AI-assisted configuration
- **Data Cleanup** -- Delete duplicate rows, null rows, null columns, or specific rows/columns with undo support
- **Pivot Table** -- Interactive pivot table builder with drag-and-drop field zones and AI-suggested configurations
- **Statistical Analysis** -- Per-column statistics (numeric distributions, text analysis, correlations), box plots, histograms, scatter plots, and radar charts
- **Custom Reports** -- Build reports with mathematical, statistical, and financial functions (NPV, IRR, ROI, CAGR, payback period, future value, present value) with group-by support
- **Business Dashboard** -- KPI cards, revenue trend charts, category distributions, and anomaly alerts
- **AI Chatbox** -- Chat interface that executes data operations (parse, join, delete, pivot, analyze, report, dashboard, export) with chat history, saved workflows, and operation plan accept/reject
- **Export** -- Export results to Excel (.xlsx, .xls), CSV, or HTML
- **Dual Language** -- English and Vietnamese (auto-detected from locale)
- **Light & Dark Themes** -- System-native Qt Fusion style

## Requirements

- Windows 10 or 11 (64-bit)
- Python 3.13+ (for running from source)

## Installation

### Option 1: Portable Build (Recommended)

Download the latest zip from [Releases](https://github.com/Vincent-HaiNgo/tagexcel/releases), extract it, and double-click `tagexcel.exe`.

### Option 2: Run from Source

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Usage

1. Launch tagexcel
2. Use the **Files** tab to load your spreadsheet data
3. Navigate through tabs to clean, join, pivot, analyze, or build reports
4. Use the **Chatbox** tab to describe operations in natural language (requires an OpenAI-compatible API endpoint)
5. Configure your AI provider in **Settings**
6. Export results via the Export button on any tab

## Tech Stack

- [Python 3.13](https://www.python.org/)
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) -- GUI framework
- [pandas](https://pandas.pydata.org/) -- Data manipulation
- [matplotlib](https://matplotlib.org/) -- Charts and visualizations
- [openpyxl](https://openpyxl.readthedocs.io/) / [python-calamine](https://github.com/dimastbk/python-calamine) -- Excel I/O

## License

MIT -- see [LICENSE](LICENSE) file for details.
