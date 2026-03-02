#!/bin/bash
# WiFi DensePose 長者防跌倒系統 — 快速啟動腳本
# Quick Start Script for Elderly Fall Detection System

echo "=========================================="
echo "  WiFi DensePose 長者防跌倒系統"
echo "  Elderly Fall Detection System"
echo "=========================================="

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，請先安裝 Python 3.10+"
    exit 1
fi

echo "✓ Python3 已安裝: $(python3 --version)"

# 檢查依賴
echo ""
echo "📦 安裝依賴套件..."
pip install -q requests aiohttp

# 設定環境變數（模擬模式）
export MOCK_POSE_DATA=true
export SECRET_KEY="test-secret-key-for-dev"
export ENVIRONMENT="development"
export DEBUG="true"
export REDIS_ENABLED="false"
export REDIS_REQUIRED="false"
export ENABLE_AUTHENTICATION="false"
export ENABLE_RATE_LIMITING="false"
export DATABASE_URL=""
export ENABLE_DATABASE_FAILSAFE="true"

echo ""
echo "✓ 環境變數已設定（模擬模式）"
echo ""
echo "📌 可用的測試腳本："
echo "  python3 src/test_fall_detection.py  — 跌倒偵測模擬測試"
echo "  python3 src/test_telegram_bot.py    — Telegram Bot 測試"
echo "  python3 src/test_analytics.py       — 歷史數據分析測試"
echo ""
echo "📌 監控儀表板："
echo "  用瀏覽器開啟 dashboard/index.html（Demo 模式）"
echo ""
echo "=========================================="
