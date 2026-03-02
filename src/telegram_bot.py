#!/usr/bin/env python3
"""
Telegram Bot 長者防跌倒警報系統
Elderly Fall Detection Alert System via Telegram

功能：
1. 跌倒即時警報通知
2. 躺臥過久異常通知
3. 手動查詢長者狀態
4. 每日活動摘要報告
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class TelegramAlertBot:
    """Telegram 警報機器人"""
    
    def __init__(self, bot_token: str, chat_ids: List[str], api_base_url: str = "http://localhost:8000"):
        """
        初始化 Telegram Bot
        
        Args:
            bot_token: Telegram Bot API Token (從 @BotFather 取得)
            chat_ids: 接收通知的 Telegram Chat ID 列表（家人群組）
            api_base_url: WiFi DensePose API 位址
        """
        self.bot_token = bot_token
        self.chat_ids = chat_ids
        self.api_base_url = api_base_url
        self.telegram_api = f"https://api.telegram.org/bot{bot_token}"
        
        # 警報設定
        self.alert_cooldown_minutes = 5  # 同一類型警報冷卻時間
        self.lying_alert_delay_seconds = 60  # 躺臥多久才觸發警報
        self.fall_confidence_threshold = 0.75  # 跌倒信心度閾值
        
        # 狀態追蹤
        self.last_alerts: Dict[str, datetime] = {}  # 上次警報時間
        self.alert_history: List[Dict] = []  # 警報歷史
        self.monitoring = False
        
    async def send_message(self, text: str, parse_mode: str = "HTML", chat_id: Optional[str] = None):
        """發送 Telegram 訊息"""
        target_ids = [chat_id] if chat_id else self.chat_ids
        
        async with aiohttp.ClientSession() as session:
            for cid in target_ids:
                try:
                    payload = {
                        "chat_id": cid,
                        "text": text,
                        "parse_mode": parse_mode
                    }
                    async with session.post(
                        f"{self.telegram_api}/sendMessage",
                        json=payload
                    ) as resp:
                        if resp.status == 200:
                            logger.info(f"訊息已發送至 {cid}")
                        else:
                            error = await resp.text()
                            logger.error(f"發送失敗 {cid}: {error}")
                except Exception as e:
                    logger.error(f"發送錯誤 {cid}: {e}")
    
    def _check_cooldown(self, alert_type: str) -> bool:
        """檢查警報冷卻期"""
        if alert_type not in self.last_alerts:
            return True
        
        elapsed = (datetime.now() - self.last_alerts[alert_type]).total_seconds()
        return elapsed > (self.alert_cooldown_minutes * 60)
    
    def _record_alert(self, alert_type: str, details: Dict):
        """記錄警報"""
        self.last_alerts[alert_type] = datetime.now()
        self.alert_history.append({
            "type": alert_type,
            "timestamp": datetime.now().isoformat(),
            "details": details
        })
        # 只保留最近 100 條記錄
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
    
    async def send_fall_alert(self, person_id: str, zone_id: str, confidence: float, activity: str):
        """
        發送跌倒警報
        
        緊急程度分級：
        - 🚨🚨🚨 跌倒 (falling) — 最高優先級
        - 🚨 躺臥過久 (lying) — 高優先級  
        - ⚠️ 異常行為 — 中優先級
        """
        alert_key = f"fall_{person_id}"
        
        if not self._check_cooldown(alert_key):
            logger.info(f"警報冷卻中，跳過 {alert_key}")
            return
        
        now = datetime.now()
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        zone_names = {
            "living_room": "客廳",
            "bedroom": "睡房",
            "bathroom": "浴室",
            "kitchen": "廚房",
            "zone_1": "區域一",
            "zone_2": "區域二",
            "zone_3": "區域三",
            "zone_4": "區域四",
        }
        zone_name = zone_names.get(zone_id, zone_id)
        
        if activity == "falling":
            message = (
                f"🚨🚨🚨 <b>緊急警報：偵測到跌倒！</b>\n\n"
                f"⏰ 時間：{time_str}\n"
                f"📍 地點：{zone_name}\n"
                f"👤 人員：{person_id}\n"
                f"📊 信心度：{confidence:.1%}\n"
                f"🔴 狀態：跌倒中\n\n"
                f"<b>請立即確認長者安全！</b>\n"
                f"如有需要請撥打 999 緊急求助"
            )
        elif activity == "lying":
            message = (
                f"🚨 <b>警報：偵測到異常躺臥</b>\n\n"
                f"⏰ 時間：{time_str}\n"
                f"📍 地點：{zone_name}\n"
                f"👤 人員：{person_id}\n"
                f"📊 信心度：{confidence:.1%}\n"
                f"🟡 狀態：躺臥（非睡房區域）\n\n"
                f"長者可能在非睡房區域躺臥，請確認是否需要協助"
            )
        else:
            message = (
                f"⚠️ <b>注意：偵測到異常行為</b>\n\n"
                f"⏰ 時間：{time_str}\n"
                f"📍 地點：{zone_name}\n"
                f"👤 人員：{person_id}\n"
                f"📊 信心度：{confidence:.1%}\n"
                f"🟠 狀態：{activity}\n\n"
                f"請稍後確認長者狀態"
            )
        
        await self.send_message(message)
        self._record_alert(alert_key, {
            "person_id": person_id,
            "zone_id": zone_id,
            "confidence": confidence,
            "activity": activity
        })
        logger.info(f"跌倒警報已發送: {person_id} in {zone_id}")
    
    async def get_current_status(self) -> Dict:
        """從 API 取得目前狀態"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.api_base_url}/api/v1/pose/current") as resp:
                    return await resp.json()
            except Exception as e:
                logger.error(f"取得狀態失敗: {e}")
                return {}
    
    async def get_zone_summary(self) -> Dict:
        """取得區域摘要"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.api_base_url}/api/v1/pose/zones/summary") as resp:
                    return await resp.json()
            except Exception as e:
                logger.error(f"取得區域摘要失敗: {e}")
                return {}
    
    async def get_activities(self, limit: int = 20) -> Dict:
        """取得最近活動"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.api_base_url}/api/v1/pose/activities?limit={limit}"
                ) as resp:
                    return await resp.json()
            except Exception as e:
                logger.error(f"取得活動失敗: {e}")
                return {}
    
    async def get_stats(self) -> Dict:
        """取得統計數據"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.api_base_url}/api/v1/pose/stats") as resp:
                    return await resp.json()
            except Exception as e:
                logger.error(f"取得統計失敗: {e}")
                return {}
    
    async def send_status_report(self, chat_id: Optional[str] = None):
        """發送目前狀態報告（回應 /status 指令）"""
        status = await self.get_current_status()
        zones = await self.get_zone_summary()
        
        if not status or not zones:
            await self.send_message("❌ 無法取得系統狀態，請檢查系統是否正常運行", chat_id=chat_id)
            return
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        zone_names = {
            "living_room": "客廳", "bedroom": "睡房",
            "bathroom": "浴室", "kitchen": "廚房",
            "zone_1": "區域一", "zone_2": "區域二",
            "zone_3": "區域三", "zone_4": "區域四",
        }
        
        persons_info = ""
        for person in status.get("persons", []):
            activity_map = {
                "standing": "站立 🧍", "sitting": "坐下 🪑",
                "walking": "行走 🚶", "lying": "躺臥 🛏️",
                "falling": "跌倒 ⚠️"
            }
            act = activity_map.get(person["activity"], person["activity"])
            persons_info += f"  👤 {person['person_id']}: {act} ({person['confidence']:.0%})\n"
        
        zones_info = ""
        for zone_id, zone_data in zones.get("zones", {}).items():
            name = zone_names.get(zone_id, zone_id)
            zones_info += f"  🏠 {name}: {zone_data['occupancy']} 人\n"
        
        message = (
            f"📊 <b>長者監測狀態報告</b>\n"
            f"⏰ {now}\n\n"
            f"<b>目前偵測人員：</b>\n"
            f"{persons_info}\n"
            f"<b>房間佔用：</b>\n"
            f"{zones_info}\n"
            f"總人數：{zones.get('total_persons', 0)}\n"
            f"活躍區域：{zones.get('active_zones', 0)} 個"
        )
        
        await self.send_message(message, chat_id=chat_id)
    
    async def send_daily_summary(self, chat_id: Optional[str] = None):
        """發送每日摘要報告"""
        stats = await self.get_stats()
        activities = await self.get_activities(limit=50)
        
        if not stats:
            await self.send_message("❌ 無法生成每日摘要", chat_id=chat_id)
            return
        
        s = stats.get("statistics", {})
        
        # 統計跌倒和躺臥事件
        fall_events = 0
        lying_events = 0
        for act in activities.get("activities", []):
            if act["activity"] == "falling":
                fall_events += 1
            elif act["activity"] == "lying":
                lying_events += 1
        
        activity_dist = s.get("activity_distribution", {})
        dist_text = ""
        label_map = {"standing": "站立", "sitting": "坐下", "walking": "行走", "lying": "躺臥"}
        for act, ratio in activity_dist.items():
            bar = "█" * int(ratio * 20)
            dist_text += f"  {label_map.get(act, act):4s} {bar} {ratio:.1%}\n"
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 判斷安全等級
        if fall_events > 0:
            safety = "🔴 需關注 — 偵測到跌倒事件"
        elif lying_events > 3:
            safety = "🟡 留意 — 多次躺臥偵測"
        else:
            safety = "🟢 正常 — 未偵測到異常"
        
        alert_count = len([a for a in self.alert_history 
                          if a["timestamp"].startswith(today)])
        
        message = (
            f"📋 <b>每日安全摘要報告</b>\n"
            f"📅 日期：{today}\n\n"
            f"<b>安全狀態：</b>{safety}\n\n"
            f"<b>統計數據（過去 24 小時）：</b>\n"
            f"  📊 總偵測次數：{s.get('total_detections', 0)}\n"
            f"  ✅ 成功率：{s.get('success_rate', 0):.1%}\n"
            f"  📈 平均信心度：{s.get('average_confidence', 0):.1%}\n"
            f"  ⚡ 平均回應時間：{s.get('average_processing_time_ms', 0):.0f}ms\n"
            f"  👥 偵測人數：{s.get('unique_persons', 0)}\n\n"
            f"<b>事件統計：</b>\n"
            f"  🚨 跌倒事件：{fall_events} 次\n"
            f"  🛏️ 異常躺臥：{lying_events} 次\n"
            f"  📢 發送警報：{alert_count} 次\n\n"
            f"<b>活動分佈：</b>\n"
            f"{dist_text}\n"
            f"💡 如有疑問，發送 /status 查詢即時狀態"
        )
        
        await self.send_message(message, chat_id=chat_id)
    
    async def monitor_loop(self, interval_seconds: int = 3):
        """
        持續監測循環
        定期檢查姿態數據，偵測到危險情況時發送警報
        """
        self.monitoring = True
        logger.info(f"開始監測循環，間隔 {interval_seconds} 秒")
        
        lying_tracker: Dict[str, datetime] = {}  # 追蹤躺臥開始時間
        
        while self.monitoring:
            try:
                data = await self.get_current_status()
                
                for person in data.get("persons", []):
                    person_id = person["person_id"]
                    activity = person["activity"]
                    confidence = person["confidence"]
                    zone_id = person.get("zone_id", "unknown")
                    
                    # 偵測跌倒 — 立即警報
                    if activity == "falling" and confidence >= self.fall_confidence_threshold:
                        await self.send_fall_alert(person_id, zone_id, confidence, "falling")
                    
                    # 追蹤躺臥
                    elif activity == "lying" and zone_id not in ["bedroom"]:
                        if person_id not in lying_tracker:
                            lying_tracker[person_id] = datetime.now()
                        else:
                            lying_duration = (datetime.now() - lying_tracker[person_id]).total_seconds()
                            if lying_duration >= self.lying_alert_delay_seconds:
                                if confidence >= self.fall_confidence_threshold:
                                    await self.send_fall_alert(
                                        person_id, zone_id, confidence, "lying"
                                    )
                                lying_tracker.pop(person_id, None)
                    else:
                        lying_tracker.pop(person_id, None)
                
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"監測循環錯誤: {e}")
                await asyncio.sleep(interval_seconds)
    
    def stop_monitoring(self):
        """停止監測"""
        self.monitoring = False
        logger.info("監測已停止")


class TelegramCommandHandler:
    """處理 Telegram Bot 指令"""
    
    def __init__(self, bot: TelegramAlertBot):
        self.bot = bot
        self.last_update_id = 0
        self.commands = {
            "/start": self._cmd_start,
            "/status": self._cmd_status,
            "/daily": self._cmd_daily,
            "/help": self._cmd_help,
            "/alerts": self._cmd_alerts,
        }
    
    async def _cmd_start(self, chat_id: str, _args: str):
        message = (
            "👋 <b>歡迎使用長者防跌倒監測系統</b>\n\n"
            "本機器人會在偵測到以下情況時通知您：\n"
            "🔴 跌倒事件 — 立即通知\n"
            "🟡 異常躺臥 — 非睡房區域躺臥超時\n\n"
            "可用指令：\n"
            "/status — 查詢目前狀態\n"
            "/daily — 查看每日摘要\n"
            "/alerts — 查看最近警報\n"
            "/help — 使用說明"
        )
        await self.bot.send_message(message, chat_id=chat_id)
    
    async def _cmd_status(self, chat_id: str, _args: str):
        await self.bot.send_status_report(chat_id=chat_id)
    
    async def _cmd_daily(self, chat_id: str, _args: str):
        await self.bot.send_daily_summary(chat_id=chat_id)
    
    async def _cmd_help(self, chat_id: str, _args: str):
        message = (
            "📖 <b>使用說明</b>\n\n"
            "<b>自動通知：</b>\n"
            "• 系統 24 小時自動監測\n"
            "• 偵測到跌倒會立即通知所有家人\n"
            "• 非睡房區域躺臥超過 60 秒會發出警告\n"
            "• 每日晚間自動發送安全摘要\n\n"
            "<b>手動查詢：</b>\n"
            "/status — 即時狀態（長者在哪、在做什麼）\n"
            "/daily — 今日活動摘要報告\n"
            "/alerts — 最近 10 條警報記錄\n\n"
            "<b>警報說明：</b>\n"
            "🚨🚨🚨 = 偵測到跌倒（最緊急）\n"
            "🚨 = 異常躺臥（需關注）\n"
            "⚠️ = 其他異常行為\n\n"
            "如遇緊急情況請撥打 999"
        )
        await self.bot.send_message(message, chat_id=chat_id)
    
    async def _cmd_alerts(self, chat_id: str, _args: str):
        recent = self.bot.alert_history[-10:]
        
        if not recent:
            await self.bot.send_message(
                "✅ 暫無警報記錄\n\n系統運作正常，未偵測到異常事件。",
                chat_id=chat_id
            )
            return
        
        message = "🔔 <b>最近警報記錄</b>\n\n"
        for alert in reversed(recent):
            ts = alert["timestamp"][:19].replace("T", " ")
            details = alert["details"]
            icon = "🚨" if details.get("activity") == "falling" else "⚠️"
            message += (
                f"{icon} {ts}\n"
                f"   {details.get('person_id', '?')} | "
                f"{details.get('zone_id', '?')} | "
                f"{details.get('activity', '?')}\n\n"
            )
        
        await self.bot.send_message(message, chat_id=chat_id)
    
    async def poll_updates(self):
        """輪詢 Telegram 更新（長輪詢）"""
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    params = {
                        "offset": self.last_update_id + 1,
                        "timeout": 30
                    }
                    async with session.get(
                        f"{self.bot.telegram_api}/getUpdates",
                        params=params
                    ) as resp:
                        data = await resp.json()
                    
                    for update in data.get("result", []):
                        self.last_update_id = update["update_id"]
                        message = update.get("message", {})
                        text = message.get("text", "")
                        chat_id = str(message.get("chat", {}).get("id", ""))
                        
                        if text.startswith("/"):
                            parts = text.split(maxsplit=1)
                            cmd = parts[0].lower()
                            args = parts[1] if len(parts) > 1 else ""
                            
                            handler = self.commands.get(cmd)
                            if handler:
                                await handler(chat_id, args)
                            else:
                                await self.bot.send_message(
                                    f"❓ 未知指令: {cmd}\n發送 /help 查看可用指令",
                                    chat_id=chat_id
                                )
                
                except Exception as e:
                    logger.error(f"輪詢錯誤: {e}")
                    await asyncio.sleep(5)


# ============================================================
# 模擬測試模式（無需真實 Telegram Bot Token）
# ============================================================

class MockTelegramBot(TelegramAlertBot):
    """模擬 Telegram Bot，用於本地測試"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        super().__init__(
            bot_token="MOCK_TOKEN_FOR_TESTING",
            chat_ids=["MOCK_CHAT_ID"],
            api_base_url=api_base_url
        )
        self.sent_messages: List[str] = []
    
    async def send_message(self, text: str, parse_mode: str = "HTML", chat_id: Optional[str] = None):
        """模擬發送 — 只打印到控制台"""
        # 移除 HTML 標記以便控制台顯示
        import re
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        self.sent_messages.append(clean_text)
        print(f"\n{'='*50}")
        print(f"📱 Telegram 通知 (模擬)")
        print(f"{'='*50}")
        print(clean_text)
        print(f"{'='*50}\n")
