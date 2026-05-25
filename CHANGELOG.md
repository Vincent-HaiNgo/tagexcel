# Changelog

All notable changes to tagexcel will be documented in this file.

## [1.0.0] - 2026-05-25

### Added

- Initial public release
- File import for CSV, Excel (.xls, .xlsx) with automatic encoding detection
- Data parsing: whitespace stripping, null sentinel detection, duplicate removal, type inference, Vietnamese diacritics normalization, date parsing
- Join/Merge: left, right, inner, and outer joins with AI-assisted configuration
- Data Cleanup: delete duplicates, null rows, null columns, specific rows/columns with undo
- Pivot Table: interactive builder with drag-and-drop field zones and AI-suggested configurations
- Statistical Analysis: per-column statistics, box plots, histograms, scatter plots, radar charts, correlation analysis
- Custom Reports: mathematical, statistical, and financial functions (NPV, IRR, ROI, CAGR, payback period, future value, present value) with group-by
- Business Dashboard: KPI cards, revenue trends, category distributions, anomaly alerts
- AI Chatbox: natural language data operations, chat history (SQLite), saved workflows, operation plan accept/reject
- Export to Excel (.xlsx, .xls), CSV, and HTML
- Dual language support: English and Vietnamese
- Light and dark themes with Qt Fusion style
- Secure credential storage via Windows DPAPI encryption
