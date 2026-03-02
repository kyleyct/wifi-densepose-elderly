#!/usr/bin/env python3
"""
歷史數據分析模組 — 模擬測試
生成 7 天模擬數據，並展示日報、週報、異常偵測功能
"""
import sys
import os
import importlib.util

# 直接載入模組
spec = importlib.util.spec_from_file_location(
    "analytics",
    "/home/user/workspace/wifi-densepose/v1/src/analytics.py"
)
analytics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analytics)

DB_PATH = "/home/user/workspace/activity_history.db"

# 刪除舊資料庫
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

print("╔══════════════════════════════════════════════════════╗")
print("║  歷史數據分析模組 — 模擬測試                         ║")
print("╚══════════════════════════════════════════════════════╝\n")

# 初始化
db = analytics.ActivityDatabase(DB_PATH)
engine = analytics.AnalyticsEngine(db)

# ---- 生成模擬數據 ----
print("【步驟 1】生成 7 天模擬歷史數據...")
analytics.generate_sample_data(db, days=7)

cursor = db.conn.cursor()
cursor.execute("SELECT COUNT(*) FROM activities")
act_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM alerts")
alert_count = cursor.fetchone()[0]
print(f"  ✓ 已生成 {act_count} 條活動記錄")
print(f"  ✓ 已生成 {alert_count} 條警報記錄")

# ---- 每日報告 ----
print("\n\n【步驟 2】生成今日安全報告")
from datetime import datetime, timedelta
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
daily = engine.generate_daily_report(yesterday)
print(analytics.format_daily_report_text(daily))

# ---- 每週報告 ----
print("\n【步驟 3】生成每週趨勢報告")
weekly = engine.generate_weekly_report()
print(analytics.format_weekly_report_text(weekly))

# ---- 異常偵測 ----
print("\n【步驟 4】執行異常行為偵測")
anomalies = engine.detect_anomalies(days=7)
print(analytics.format_anomalies_text(anomalies))

# ---- 完成 ----
print("=" * 55)
print("  ✅ 歷史數據分析模組測試完成！")
print("=" * 55)
print()
print("已建立功能：")
print("  1. SQLite 資料庫自動記錄活動和警報")
print("  2. 每日安全報告（含安全評級、活動分佈、區域分析）")
print("  3. 每週趨勢報告（含每日明細、趨勢分析）")
print("  4. 異常行為偵測（活動量下降、夜間活動、跌倒趨勢、浴室停留）")
print("  5. 自動安全建議生成")

db.close()
