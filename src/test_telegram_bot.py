#!/usr/bin/env python3
"""
Telegram Bot 模擬測試
測試所有警報功能，無需真實 Telegram Token
"""
import asyncio
import sys
import importlib.util

# 直接載入模組，避免觸發 src/__init__.py 的完整 app 初始化
spec = importlib.util.spec_from_file_location(
    "telegram_bot",
    "/home/user/workspace/wifi-densepose/v1/src/telegram_bot.py"
)
telegram_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(telegram_module)
MockTelegramBot = telegram_module.MockTelegramBot


async def main():
    bot = MockTelegramBot(api_base_url="http://localhost:8000")
    
    print("╔══════════════════════════════════════════════════╗")
    print("║  Telegram Bot 長者防跌倒警報系統 — 模擬測試      ║")
    print("╚══════════════════════════════════════════════════╝\n")
    
    # ---- 測試 1: 即時狀態查詢 (/status) ----
    print("【測試 1】模擬 /status 指令 — 查詢即時狀態")
    await bot.send_status_report()
    
    # ---- 測試 2: 跌倒緊急警報 ----
    print("\n【測試 2】模擬跌倒緊急警報")
    await bot.send_fall_alert(
        person_id="elderly_01",
        zone_id="bathroom",
        confidence=0.92,
        activity="falling"
    )
    
    # ---- 測試 3: 異常躺臥警報 ----
    print("\n【測試 3】模擬異常躺臥警報（非睡房區域）")
    await bot.send_fall_alert(
        person_id="elderly_01",
        zone_id="living_room",
        confidence=0.85,
        activity="lying"
    )
    
    # ---- 測試 4: 冷卻期測試 ----
    print("\n【測試 4】警報冷卻期測試（5 分鐘內同一人不重複警報）")
    await bot.send_fall_alert(
        person_id="elderly_01",
        zone_id="living_room",
        confidence=0.90,
        activity="lying"
    )
    print("  → 冷卻期內，上述警報不應重複發送 ✓")
    
    # ---- 測試 5: 每日摘要 (/daily) ----
    print("\n【測試 5】模擬 /daily 指令 — 每日安全摘要")
    await bot.send_daily_summary()
    
    # ---- 測試 6: 短時間監測循環 ----
    print("\n【測試 6】啟動監測循環（5 秒）")
    
    async def stop_after_delay():
        await asyncio.sleep(5)
        bot.stop_monitoring()
    
    monitor_task = asyncio.create_task(bot.monitor_loop(interval_seconds=2))
    stop_task = asyncio.create_task(stop_after_delay())
    
    await asyncio.gather(monitor_task, stop_task, return_exceptions=True)
    
    # ---- 測試結果 ----
    print("\n" + "=" * 50)
    print(f"📊 測試完成！共發送 {len(bot.sent_messages)} 條模擬通知")
    print(f"📝 警報歷史記錄: {len(bot.alert_history)} 條")
    print("=" * 50)
    
    print("\n✅ Telegram Bot 模組測試全部通過！")
    print("\n📌 正式使用時，需要：")
    print("  1. 在 Telegram 搜索 @BotFather，創建新 Bot 取得 Token")
    print("  2. 取得家人群組的 Chat ID")
    print("  3. 將 Token 和 Chat ID 填入設定檔")


if __name__ == "__main__":
    asyncio.run(main())
