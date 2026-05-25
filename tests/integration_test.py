"""
End-to-end integration test for all tagexcel core engines using a real Excel file.
Run with venv Python only.
"""
import sys
import json
import io
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
venv_python = project_root / "venv" / "Scripts" / "python.exe"
current_exe = Path(sys.executable).resolve()
expected_exe = venv_python.resolve()
if current_exe != expected_exe:
    print(f"FATAL: Must run with venv Python: {expected_exe}", file=sys.stderr)
    sys.exit(1)

import pandas as pd
import numpy as np

FILE_PATH = r"C:\vhn_drives\workshop\wrk_temp\eg_transaction_list.xlsx"

def test_all():
    results = {"passed": 0, "failed": 0, "errors": []}

    def check(condition, name):
        try:
            safe_name = str(name).encode("ascii", errors="replace").decode("ascii")
        except Exception:
            safe_name = name
        if condition:
            results["passed"] += 1
            print(f"  [PASS] {safe_name}")
        else:
            results["failed"] += 1
            msg = f"  [FAIL] {safe_name}"
            print(msg)
            results["errors"].append(msg)

    # ===== 1. DataManager: Load file =====
    print("\n=== DataManager ===")
    from core.data_manager import DataManager
    dm = DataManager()
    dm.add_file(FILE_PATH)
    df = dm.df_working
    check(df is not None, "DataManager.add_file loads xlsx")
    check(isinstance(df, pd.DataFrame), "df_working is a DataFrame")
    check(len(df) > 0, f"DataFrame has rows: {len(df)}")
    check(len(df.columns) > 0, f"DataFrame has columns: {len(df.columns)}")
    summary = dm.get_summary()
    check(summary["filename"] is not None, "get_summary returns filename")
    check(summary["rows"] == len(df), "get_summary rows match DataFrame")
    check(summary["columns"] == len(df.columns), "get_summary columns match")

    # Test set_active
    loaded = dm.get_loaded_files()
    check(len(loaded) > 0, f"get_loaded_files returns files: {loaded}")
    dm.set_active(loaded[0])
    check(dm.active_file == loaded[0], "set_active works")
    check(dm.df_working is not None, "df_working persists after set_active")

    # Test reset_working and update_working
    original_len = len(dm.df_working)
    dm.update_working(dm.df_working.head(10))
    check(len(dm.df_working) == 10, "update_working changes df_working")
    dm.reset_working()
    check(len(dm.df_working) == original_len, "reset_working restores original")
    dm.set_active(loaded[0])

    # ===== 2. ParserEngine: Parse data =====
    print("\n=== ParserEngine ===")
    from core.parser_engine import ParserEngine
    pe = ParserEngine()
    check(pe is not None, "ParserEngine instantiated")

    df_parsed, log = pe.parse(df)
    check(isinstance(df_parsed, pd.DataFrame), "parse returns DataFrame")
    check(isinstance(log, list), "parse returns log list")
    check(len(log) > 0, f"parse produced {len(log)} log entries")
    for entry in log:
        check(isinstance(entry, str), f"log entry is str: {entry[:80]}...")

    # Test execute_plan for all operations
    print("  Testing execute_plan operations...")
    plan_df = dm.df_working.copy()

    # drop_nulls
    r, l = pe.execute_plan(plan_df, [{"operation": "drop_nulls", "column": plan_df.columns[0]}])
    check(isinstance(r, pd.DataFrame), "execute_plan drop_nulls returns DataFrame")
    check(len(l) > 0, "execute_plan drop_nulls returns log")

    # fill_nulls
    num_cols = plan_df.select_dtypes(include=["number"]).columns.tolist()
    if num_cols:
        r, l = pe.execute_plan(plan_df, [{"operation": "fill_nulls", "column": num_cols[0], "params": {"value": "0"}}])
        check(isinstance(r, pd.DataFrame), "execute_plan fill_nulls returns DataFrame")

    # drop_duplicates
    r, l = pe.execute_plan(plan_df, [{"operation": "drop_duplicates"}])
    check(isinstance(r, pd.DataFrame), "execute_plan drop_duplicates returns DataFrame")

    # coerce_type
    for col_name in plan_df.columns:
        if pd.api.types.is_object_dtype(plan_df[col_name]) or pd.api.types.is_string_dtype(plan_df[col_name]):
            r, l = pe.execute_plan(plan_df, [{"operation": "coerce_type", "column": col_name, "params": {"dtype": "float"}}])
            check(isinstance(r, pd.DataFrame), f"execute_plan coerce_type {col_name} returns DataFrame")
            break

    # normalize_text
    str_cols = plan_df.select_dtypes(include=["object", "string"]).columns.tolist()
    if str_cols:
        r, l = pe.execute_plan(plan_df, [{"operation": "normalize_text", "column": str_cols[0]}])
        check(isinstance(r, pd.DataFrame), "execute_plan normalize_text returns DataFrame")

    # parse_dates
    if str_cols:
        r, l = pe.execute_plan(plan_df, [{"operation": "parse_dates", "column": str_cols[0]}])
        check(isinstance(r, pd.DataFrame), "execute_plan parse_dates returns DataFrame")

    # drop_column
    r, l = pe.execute_plan(plan_df, [{"operation": "drop_column", "column": plan_df.columns[0]}])
    check(len(r.columns) < len(plan_df.columns), "execute_plan drop_column reduces columns")

    # rename_column
    old_col = plan_df.columns[0]
    r, l = pe.execute_plan(plan_df, [{"operation": "rename_column", "column": old_col, "params": {"new_name": "RENAMED_TEST"}}])
    check("RENAMED_TEST" in r.columns, "execute_plan rename_column renames column")

    # ===== 3. AnalysisEngine: Compute statistics =====
    print("\n=== AnalysisEngine ===")
    from core.analysis_engine import compute_statistics, render_statistics_html, build_stats_summary_for_ai
    stats = compute_statistics(dm.df_working)
    check(isinstance(stats, dict), "compute_statistics returns dict")
    check("overview" in stats, "stats has overview")
    check("column_types" in stats, "stats has column_types")
    check("columns" in stats, "stats has columns")
    check("missing_patterns" in stats, "stats has missing_patterns")
    check("correlation" in stats, "stats has correlation")
    ov = stats["overview"]
    check(isinstance(ov["rows"], int), "overview.rows is int")
    check(isinstance(ov["columns"], int), "overview.columns is int")
    check(isinstance(ov["duplicates"], int), "overview.duplicates is int")
    check(isinstance(ov["memory_kb"], (int, float)), "overview.memory_kb is number")

    for theme in ("light", "dark"):
        html = render_statistics_html(stats, df=dm.df_working, theme=theme)
        check(isinstance(html, str) and len(html) > 100, f"render_statistics_html({theme}) returns HTML")
        check("<html" in html.lower(), f"render_statistics_html({theme}) contains <html>")
        check("</html>" in html.lower(), f"render_statistics_html({theme}) contains </html>")

    summary_ai = build_stats_summary_for_ai(stats)
    check(isinstance(summary_ai, dict), "build_stats_summary_for_ai returns dict")
    check("overview" in summary_ai, "build_stats_summary_for_ai has overview")

    # ===== 4. DashboardEngine =====
    print("\n=== DashboardEngine ===")
    from core.dashboard_engine import compute_dashboard, render_dashboard_html, _detect_roles
    roles = _detect_roles(dm.df_working)
    check(isinstance(roles, dict), "_detect_roles returns dict")
    check(len(roles) > 0, f"_detect_roles found {len(roles)} role mappings")
    print(f"  Detected roles: {len(roles)} columns classified")

    dash_data = compute_dashboard(dm.df_working)
    check(isinstance(dash_data, dict), "compute_dashboard returns dict")
    check("kpi" in dash_data, "dashboard has kpi")
    check("revenue" in dash_data, "dashboard has revenue")
    check("alerts" in dash_data, "dashboard has alerts")
    check("roles" in dash_data, "dashboard has roles")

    for theme in ("light", "dark"):
        html = render_dashboard_html(dash_data, dm.df_working, theme=theme)
        check(isinstance(html, str) and len(html) > 100, f"render_dashboard_html({theme}) returns HTML")

    # ===== 5. ReportEngine =====
    print("\n=== ReportEngine ===")
    from core.report_engine import compute_report, render_report_html, build_report_summary_for_ai
    num_cols_all = dm.df_working.select_dtypes(include=["number"]).columns.tolist()
    if num_cols_all:
        config = {
            "columns": num_cols_all[:3],
            "functions": ["sum", "avg", "min", "max", "count", "median", "std", "variance"],
            "group_by": None,
            "rate": 10.0,
        }
        report = compute_report(dm.df_working, config)
        check(isinstance(report, dict), "compute_report returns dict")
        check("rows" in report, "report has rows")
        check("functions" in report, "report has functions")
        check(len(report["rows"]) > 0, "report has row data")

        for theme in ("light", "dark"):
            html = render_report_html(report, theme=theme)
            check(isinstance(html, str) and len(html) > 100, f"render_report_html({theme}) returns HTML")

        summary_rpt = build_report_summary_for_ai(report)
        check(isinstance(summary_rpt, dict), "build_report_summary_for_ai returns dict")

    # Test finance functions
    if num_cols_all:
        fn_config = {
            "columns": [num_cols_all[0]],
            "functions": ["NPV", "IRR", "ROI", "CAGR", "payback", "fv", "pv"],
            "group_by": None,
            "rate": 10.0,
        }
        fn_report = compute_report(dm.df_working, fn_config)
        check(isinstance(fn_report, dict), "compute_report finance functions return dict")

    # ===== 6. Chart Utilities =====
    print("\n=== ChartUtils ===")
    from utils.chart_utils import fig_to_b64, chart_pie, chart_line, chart_scatter, chart_radar
    from matplotlib.figure import Figure
    fig = Figure(figsize=(4, 3))
    ax = fig.add_subplot(111)
    ax.plot([1, 2, 3], [4, 5, 6])
    b64 = fig_to_b64(fig)
    check(isinstance(b64, str) and b64.startswith("data:image/png;base64,"), "fig_to_b64 returns base64 PNG")

    str_cols = dm.df_working.select_dtypes(include=["object", "string"]).columns.tolist()
    if str_cols:
        pie = chart_pie(dm.df_working[str_cols[0]].dropna().astype(str).head(50), "Test Pie")
        check(isinstance(pie, str) and ("data:image" in pie or pie == ""), "chart_pie returns image or empty")

    # chart_line
    if num_cols_all:
        series = dm.df_working[num_cols_all[0]].dropna().head(20)
        x_labels = [str(i) for i in range(len(series))]
        line = chart_line(x_labels, series, "Test Line")
        check(isinstance(line, str), "chart_line returns string")

    # chart_scatter
    if len(num_cols_all) >= 2:
        scat = chart_scatter(
            dm.df_working[num_cols_all[0]].dropna(),
            dm.df_working[num_cols_all[1]].dropna(),
            "Test Scatter", corr=0.85
        )
        check(isinstance(scat, str), "chart_scatter returns string")

    # chart_radar
    if len(num_cols_all) >= 3:
        radar = chart_radar(
            ["A", "B", "C"],
            {"Metric1": [1.0, 2.0, 3.0], "Metric2": [2.0, 3.0, 1.0]},
            "Test Radar"
        )
        check(isinstance(radar, str), "chart_radar returns string")

    # ===== 7. HTML Templates =====
    print("\n=== HTML Templates ===")
    from utils.html_templates import (
        page_start, page_end, stat_box, card, section_header,
        styled_table, badge, alert_row, timestamp_label, row, col, wrap_ai_html,
    )
    for theme in ("light", "dark"):
        ps = page_start("Test Page", theme)
        check("<!DOCTYPE html>" in ps, f"page_start({theme}) has DOCTYPE")
        check("<style>" in ps, f"page_start({theme}) has <style>")

    pe_html = page_end()
    check("</body>" in pe_html, "page_end closes body")

    sb = stat_box("100", "Test Label", "teal", chr(9670), "light")
    check("stat-box" in sb, "stat_box has stat-box class")

    cd = card("Header", "<p>Body</p>", chr(9670), "light")
    check("card-header" in cd, "card has card-header")

    sh = section_header("Section", chr(9670), "light")
    check("section-h3" in sh, "section_header has section-h3")

    st = styled_table(["Col1", "Col2"], [["a", "b"], ["c", "d"]], "light")
    check("<table" in st, "styled_table has <table>")

    b = badge("TEST", "red")
    check("badge-red" in b, "badge red has badge-red class")

    ar = alert_row("Warning!", "warn")
    check("alert-warn" in ar, "alert_row warn has alert-warn class")

    tl = timestamp_label("2024-01-01")
    check("Generated" in tl, "timestamp_label has Generated")

    r = row("<td>Test</td>")
    check("<table" in r, "row wraps in <table>")
    check("<tr>" in r, "row wraps in <tr>")

    c = col("<p>Test</p>", width=6)
    check("<td" in c, "col wraps in <td>")
    check("50%" in c, "col width=6 is 50%")

    wrapped = wrap_ai_html("<h2>Hello</h2><p>World</p>", "Test", "light")
    check("<!DOCTYPE html>" in wrapped, "wrap_ai_html has DOCTYPE")
    check("<h2>Hello</h2>" in wrapped, "wrap_ai_html preserves content")

    # ===== 8. ChatHistoryDB =====
    print("\n=== ChatHistoryDB ===")
    from core.chat_history_db import ChatHistoryDB
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_chat.db")
        db = ChatHistoryDB(db_path)
        sid = db.create_session("Test Integration Session")
        check(sid > 0, "chat_db create_session returns valid ID")
        mid = db.add_message(sid, "user", "Hello, AI!")
        check(mid > 0, "chat_db add_message returns valid ID")
        mid2 = db.add_message(sid, "assistant", "Hello, user!", operations_json='[{"op": "test"}]', accepted=1)
        check(mid2 > 0, "chat_db add_message with operations returns valid ID")
        msgs = db.get_messages(sid)
        check(len(msgs) == 2, f"chat_db get_messages returns 2 messages (got {len(msgs)})")
        sessions = db.get_sessions()
        check(len(sessions) == 1, "chat_db get_sessions returns 1 session")

        db.update_message_accepted(mid2, 0)
        msgs2 = db.get_messages(sid)
        check(msgs2[1]["accepted"] == 0, "chat_db update_message_accepted works")

        db.delete_session(sid)
        check(len(db.get_sessions()) == 0, "chat_db delete_session removes session")
        db.close()

    # ===== 9. WorkflowManager =====
    print("\n=== WorkflowManager ===")
    from core.workflow_manager import WorkflowManager
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_wf.db")
        wm = WorkflowManager(db_path)
        ops = json.dumps([{"step": 1, "action": "parse", "params": {}}])
        wid = wm.save_workflow("Test WF", "Integration test workflow", ops)
        check(wid > 0, "workflow save_workflow returns valid ID")
        wfs = wm.get_workflows()
        check(len(wfs) == 1, "workflow get_workflows returns 1")
        wf = wm.get_workflow(wid)
        check(wf is not None, "workflow get_workflow returns data")
        check(wf["name"] == "Test WF", "workflow name matches")
        wm.delete_workflow(wid)
        check(len(wm.get_workflows()) == 0, "workflow delete removes workflow")
        wm.close()

    # ===== 10. I18n =====
    print("\n=== I18n ===")
    from utils.i18n import tr, set_language, get_language
    orig_lang = get_language()
    set_language("EN")
    check(tr("app_title") == "tagexcel", "i18n EN app_title")
    set_language("VI")
    vi_title = tr("app_title")
    check(vi_title == "tagexcel", "i18n VI app_title")
    check(tr("tab_files") != "Files", "i18n VI tab_files is translated")
    set_language("EN")
    check(tr("tab_files") == "Files", "i18n EN restored")
    set_language(orig_lang)

    # ===== 11. Export Utils (just function exists, no file write) =====
    print("\n=== Export Utils ===")
    from utils.export_utils import save_html_file, export_dataframe
    check(callable(save_html_file), "save_html_file is callable")
    check(callable(export_dataframe), "export_dataframe is callable")

    # ===== 12. Security =====
    print("\n=== Security ===")
    from utils.security import save_credentials, load_credentials
    check(callable(save_credentials), "save_credentials is callable")
    check(callable(load_credentials), "load_credentials is callable")
    creds = load_credentials()
    check(isinstance(creds, (dict, type(None))), "load_credentials returns dict or None")

    # ===== 13. Config =====
    print("\n=== Config ===")
    from utils.config import APP_NAME, DATA_DIR, PAGE_SIZE, MAX_PIVOT_CELLS, SUPPORTED_EXTENSIONS
    check(APP_NAME == "tagexcel", "config APP_NAME")
    check(PAGE_SIZE == 100, "config PAGE_SIZE")
    check(MAX_PIVOT_CELLS == 5_000_000, "config MAX_PIVOT_CELLS")
    check(".csv" in SUPPORTED_EXTENSIONS, "config SUPPORTED_EXTENSIONS includes .csv")

    # ===== 14. Pivot Table engine via PivotDialog config =====
    print("\n=== PivotTable Engine ===")
    num_alias = dm.df_working.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = dm.df_working.select_dtypes(include=["object", "string"]).columns.tolist()
    if cat_cols and num_alias:
        pivot_config = {
            "rows": [cat_cols[0]],
            "columns": [],
            "filters": [],
            "values": [(num_alias[0], "sum"), (num_alias[0], "count")],
        }
        pivot_df = pd.pivot_table(
            dm.df_working,
            values=[v[0] for v in pivot_config["values"]],
            index=pivot_config["rows"] if pivot_config["rows"] else None,
            aggfunc={v[0]: v[1] for v in pivot_config["values"]},
        )
        check(isinstance(pivot_df, pd.DataFrame), "pandas pivot_table returns DataFrame")
        check(len(pivot_df) > 0, "pivot_table has rows")

    # ===== 15. Shared utilities =====
    print("\n=== Shared Utilities ===")
    from utils.shared import strip_code_fence, try_parse_json_plan, build_df_schema, BASE_URL
    check(strip_code_fence("plain text") == "plain text", "strip_code_fence passes plain text through")
    check(strip_code_fence("```json\n{\"a\":1}\n```") == "{\"a\":1}", "strip_code_fence strips code fence")
    check(strip_code_fence("```\nhello\n```") == "hello", "strip_code_fence strips simple fence")

    parsed = try_parse_json_plan('{"description":"test","plan":[{"step":1,"action":"parse","params":{}}]}')
    check(parsed is not None, "try_parse_json_plan parses valid JSON plan")
    check(parsed["plan"][0]["action"] == "parse", "try_parse_json_plan extracts plan correctly")

    non_plan = try_parse_json_plan("Just a regular chat message")
    check(non_plan is None, "try_parse_json_plan returns None for non-plan text")

    schema = build_df_schema(dm.df_working)
    check("total_rows" in schema, "build_df_schema has total_rows")
    check("total_columns" in schema, "build_df_schema has total_columns")
    check("columns" in schema, "build_df_schema has columns")
    check(len(schema["columns"]) > 0, "build_df_schema returns column info")
    check("name" in schema["columns"][0], "build_df_schema columns have name")
    check("dtype" in schema["columns"][0], "build_df_schema columns have dtype")
    check("samples" in schema["columns"][0], "build_df_schema columns have samples")

    # ===== 16. edge cases =====
    print("\n=== Edge Cases ===")
    empty_df = pd.DataFrame()
    stats_empty = compute_statistics(empty_df)
    check(isinstance(stats_empty, dict), "compute_statistics empty df returns dict")
    html_empty = render_statistics_html(stats_empty, df=empty_df, theme="light")
    check(isinstance(html_empty, str), "render_statistics_html empty df returns HTML")

    dash_empty = compute_dashboard(empty_df)
    check(isinstance(dash_empty, dict), "compute_dashboard empty df returns dict")

    rpt_empty = compute_report(empty_df, {"columns": [], "functions": []})
    check(len(rpt_empty["rows"]) == 0, "compute_report empty config returns 0 rows")

    pe_empty, log_empty = pe.parse(empty_df)
    check(isinstance(pe_empty, pd.DataFrame), "parse empty df returns DataFrame")
    check(len(pe_empty) == 0, "parse empty df has 0 rows")

    build_df_schema(empty_df)

    # ===== SUMMARY =====
    print("\n" + "=" * 60)
    print(f"RESULTS: {results['passed']} passed, {results['failed']} failed")
    if results["failed"] > 0:
        print("FAILURES:")
        for err in results["errors"]:
            print(f"  {err}")
    print("=" * 60)
    return results["failed"] == 0


if __name__ == "__main__":
    success = test_all()
    sys.exit(0 if success else 1)
