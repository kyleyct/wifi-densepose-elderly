#!/usr/bin/env python3
"""
歷史數據分析模組
Historical Data Analytics for Elderly Fall Detection

功能：
1. 活動數據收集與儲存 (SQLite)
2. 每日安全報告生成
3. 每週趨勢分析
4. 異常行為偵測
5. 風險評估與建議
"""

import json
import sqlite3
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class ActivityDatabase:
    """活動數據資料庫（SQLite）"""
    
    def __init__(self, db_path: str = "activity_history.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        cursor = self.conn.cursor()
        
        # 活動記錄表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                person_id TEXT NOT NULL,
                zone_id TEXT NOT NULL,
                activity TEXT NOT NULL,
                confidence REAL NOT NULL,
                duration_seconds INTEGER DEFAULT 0
            )
        """)
        
        # 警報記錄表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                person_id TEXT NOT NULL,
                zone_id TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                confidence REAL NOT NULL,
                resolved INTEGER DEFAULT 0,
                resolved_at TEXT
            )
        """)
        
        # 每日摘要表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                total_detections INTEGER,
                fall_events INTEGER,
                lying_alerts INTEGER,
                avg_confidence REAL,
                most_active_zone TEXT,
                activity_distribution TEXT,
                safety_rating TEXT,
                notes TEXT
            )
        """)
        
        self.conn.commit()
    
    def record_activity(self, person_id: str, zone_id: str, activity: str, 
                       confidence: float, duration: int = 0):
        """記錄活動"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO activities (timestamp, person_id, zone_id, activity, confidence, duration_seconds) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), person_id, zone_id, activity, confidence, duration)
        )
        self.conn.commit()
    
    def record_alert(self, person_id: str, zone_id: str, alert_type: str, 
                    severity: str, confidence: float):
        """記錄警報"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO alerts (timestamp, person_id, zone_id, alert_type, severity, confidence) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), person_id, zone_id, alert_type, severity, confidence)
        )
        self.conn.commit()
    
    def get_activities(self, start_date: str, end_date: str) -> List[dict]:
        """取得時間範圍內的活動"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM activities WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp DESC",
            (start_date, end_date)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_alerts(self, start_date: str, end_date: str) -> List[dict]:
        """取得時間範圍內的警報"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM alerts WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp DESC",
            (start_date, end_date)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        self.conn.close()


class AnalyticsEngine:
    """數據分析引擎"""
    
    def __init__(self, db: ActivityDatabase):
        self.db = db
        
        self.zone_names = {
            "living_room": "客廳", "bedroom": "睡房",
            "bathroom": "浴室", "kitchen": "廚房",
            "zone_1": "區域一", "zone_2": "區域二",
            "zone_3": "區域三", "zone_4": "區域四",
        }
        
        self.activity_names = {
            "standing": "站立", "sitting": "坐下",
            "walking": "行走", "lying": "躺臥",
            "falling": "跌倒"
        }
    
    def generate_daily_report(self, date: Optional[str] = None) -> Dict:
        """
        生成每日安全報告
        
        Args:
            date: 日期字串 (YYYY-MM-DD)，預設為今天
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        start = f"{date}T00:00:00"
        end = f"{date}T23:59:59"
        
        activities = self.db.get_activities(start, end)
        alerts = self.db.get_alerts(start, end)
        
        # 基本統計
        total = len(activities)
        activity_counts = defaultdict(int)
        zone_counts = defaultdict(int)
        confidence_sum = 0
        duration_sum = 0
        
        for act in activities:
            activity_counts[act["activity"]] += 1
            zone_counts[act["zone_id"]] += 1
            confidence_sum += act["confidence"]
            duration_sum += act.get("duration_seconds", 0)
        
        avg_confidence = confidence_sum / total if total > 0 else 0
        
        # 活動分佈
        distribution = {}
        for act, count in activity_counts.items():
            distribution[self.activity_names.get(act, act)] = {
                "count": count,
                "percentage": count / total * 100 if total > 0 else 0
            }
        
        # 最活躍區域
        most_active = max(zone_counts, key=zone_counts.get) if zone_counts else "N/A"
        
        # 警報統計
        fall_events = sum(1 for a in alerts if a["alert_type"] == "falling")
        lying_alerts = sum(1 for a in alerts if a["alert_type"] == "lying")
        
        # 安全評級
        if fall_events > 0:
            safety = "危險"
            safety_icon = "🔴"
            safety_desc = f"偵測到 {fall_events} 次跌倒事件，建議立即關注"
        elif lying_alerts > 3:
            safety = "留意"
            safety_icon = "🟡"
            safety_desc = f"偵測到 {lying_alerts} 次異常躺臥，建議觀察"
        else:
            safety = "正常"
            safety_icon = "🟢"
            safety_desc = "活動模式正常，未偵測到異常"
        
        # 時段分析
        hourly = defaultdict(int)
        for act in activities:
            hour = act["timestamp"][11:13]
            hourly[hour] += 1
        
        peak_hour = max(hourly, key=hourly.get) if hourly else "N/A"
        quiet_hours = [h for h in range(24) if f"{h:02d}" not in hourly or hourly[f"{h:02d}"] == 0]
        
        report = {
            "date": date,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "safety_rating": safety,
                "safety_icon": safety_icon,
                "safety_description": safety_desc,
                "total_detections": total,
                "average_confidence": round(avg_confidence, 3),
                "total_duration_minutes": round(duration_sum / 60, 1),
            },
            "alerts": {
                "total": len(alerts),
                "fall_events": fall_events,
                "lying_alerts": lying_alerts,
                "details": alerts[:10]  # 最近 10 條
            },
            "activity_distribution": distribution,
            "zone_analysis": {
                self.zone_names.get(z, z): count 
                for z, count in sorted(zone_counts.items(), key=lambda x: -x[1])
            },
            "temporal_analysis": {
                "peak_activity_hour": f"{peak_hour}:00",
                "quiet_hours": [f"{h:02d}:00" for h in quiet_hours[:5]],
                "hourly_distribution": dict(sorted(hourly.items())),
            },
            "recommendations": self._generate_recommendations(
                fall_events, lying_alerts, activity_counts, zone_counts
            )
        }
        
        return report
    
    def generate_weekly_report(self, end_date: Optional[str] = None) -> Dict:
        """生成每週趨勢報告"""
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        start_dt = end_dt - timedelta(days=6)
        
        daily_stats = []
        total_falls = 0
        total_lying = 0
        
        for i in range(7):
            day = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
            daily = self.generate_daily_report(day)
            daily_stats.append({
                "date": day,
                "detections": daily["summary"]["total_detections"],
                "falls": daily["alerts"]["fall_events"],
                "lying": daily["alerts"]["lying_alerts"],
                "safety": daily["summary"]["safety_rating"],
                "avg_confidence": daily["summary"]["average_confidence"]
            })
            total_falls += daily["alerts"]["fall_events"]
            total_lying += daily["alerts"]["lying_alerts"]
        
        # 趨勢計算
        first_half = sum(d["detections"] for d in daily_stats[:3])
        second_half = sum(d["detections"] for d in daily_stats[4:])
        
        if first_half > 0:
            trend = ((second_half - first_half) / first_half) * 100
        else:
            trend = 0
        
        if trend > 20:
            trend_text = "活動量明顯增加"
            trend_icon = "📈"
        elif trend < -20:
            trend_text = "活動量明顯減少（請注意）"
            trend_icon = "📉"
        else:
            trend_text = "活動量穩定"
            trend_icon = "➡️"
        
        # 週安全評級
        if total_falls > 2:
            week_safety = "需要關注"
            week_safety_icon = "🔴"
        elif total_falls > 0 or total_lying > 10:
            week_safety = "需要留意"
            week_safety_icon = "🟡"
        else:
            week_safety = "良好"
            week_safety_icon = "🟢"
        
        report = {
            "period": f"{start_dt.strftime('%Y-%m-%d')} 至 {end_date}",
            "generated_at": datetime.now().isoformat(),
            "weekly_summary": {
                "safety_rating": week_safety,
                "safety_icon": week_safety_icon,
                "total_falls": total_falls,
                "total_lying_alerts": total_lying,
                "activity_trend": trend_text,
                "activity_trend_icon": trend_icon,
                "trend_percentage": round(trend, 1),
            },
            "daily_breakdown": daily_stats,
            "insights": self._generate_weekly_insights(daily_stats, total_falls, total_lying),
        }
        
        return report
    
    def detect_anomalies(self, days: int = 7) -> List[Dict]:
        """
        異常行為偵測
        
        檢測：
        1. 活動量突然下降（可能表示身體不適）
        2. 夜間異常活動（可能表示睡眠問題）
        3. 同一地點長時間停留
        4. 跌倒頻率增加趨勢
        """
        anomalies = []
        end = datetime.now()
        start = end - timedelta(days=days)
        
        activities = self.db.get_activities(
            start.isoformat(), end.isoformat()
        )
        alerts = self.db.get_alerts(
            start.isoformat(), end.isoformat()
        )
        
        # 1. 活動量變化偵測
        daily_counts = defaultdict(int)
        for act in activities:
            day = act["timestamp"][:10]
            daily_counts[day] += 1
        
        if len(daily_counts) >= 3:
            counts = list(daily_counts.values())
            avg = sum(counts) / len(counts)
            
            for day, count in daily_counts.items():
                if count < avg * 0.5:
                    anomalies.append({
                        "type": "low_activity",
                        "severity": "medium",
                        "date": day,
                        "message": f"{day} 活動量偏低（{count} 次，平均 {avg:.0f} 次），建議關注長者身體狀況",
                        "icon": "📉"
                    })
        
        # 2. 夜間活動偵測 (23:00 - 05:00)
        night_activities = defaultdict(int)
        for act in activities:
            hour = int(act["timestamp"][11:13])
            if hour >= 23 or hour < 5:
                day = act["timestamp"][:10]
                night_activities[day] += 1
        
        for day, count in night_activities.items():
            if count > 5:
                anomalies.append({
                    "type": "night_activity",
                    "severity": "low",
                    "date": day,
                    "message": f"{day} 夜間活動頻繁（{count} 次），可能有睡眠問題",
                    "icon": "🌙"
                })
        
        # 3. 跌倒趨勢
        daily_falls = defaultdict(int)
        for alert in alerts:
            if alert["alert_type"] == "falling":
                day = alert["timestamp"][:10]
                daily_falls[day] += 1
        
        consecutive_days = 0
        for i in range(days):
            day = (end - timedelta(days=i)).strftime("%Y-%m-%d")
            if daily_falls.get(day, 0) > 0:
                consecutive_days += 1
            else:
                break
        
        if consecutive_days >= 2:
            anomalies.append({
                "type": "fall_trend",
                "severity": "high",
                "date": end.strftime("%Y-%m-%d"),
                "message": f"連續 {consecutive_days} 天偵測到跌倒事件，強烈建議就醫檢查",
                "icon": "🚨"
            })
        
        # 4. 浴室長時間停留
        bathroom_durations = []
        for act in activities:
            if act["zone_id"] in ["bathroom", "zone_3"]:
                bathroom_durations.append(act.get("duration_seconds", 0))
        
        if bathroom_durations:
            avg_bathroom = sum(bathroom_durations) / len(bathroom_durations)
            long_stays = [d for d in bathroom_durations if d > 600]  # > 10 分鐘
            
            if len(long_stays) > 2:
                anomalies.append({
                    "type": "long_bathroom_stay",
                    "severity": "medium",
                    "date": end.strftime("%Y-%m-%d"),
                    "message": f"浴室長時間停留 {len(long_stays)} 次（>10分鐘），注意長者安全",
                    "icon": "🚿"
                })
        
        return sorted(anomalies, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["severity"]])
    
    def _generate_recommendations(self, falls: int, lying: int, 
                                   activity_counts: dict, zone_counts: dict) -> List[str]:
        """生成安全建議"""
        recs = []
        
        if falls > 0:
            recs.append("🔴 今日偵測到跌倒事件，建議檢查長者身體狀況，考慮就醫評估")
        
        if lying > 3:
            recs.append("🟡 多次偵測到非睡房區域躺臥，建議確認長者是否感到不適")
        
        walking = activity_counts.get("walking", 0)
        total = sum(activity_counts.values())
        if total > 0 and walking / total < 0.1:
            recs.append("💡 行走活動比例偏低，建議鼓勵長者適度活動")
        
        bathroom = zone_counts.get("bathroom", 0) + zone_counts.get("zone_3", 0)
        if bathroom > total * 0.3:
            recs.append("💡 浴室使用頻率較高，確保浴室防滑設施完善")
        
        if not recs:
            recs.append("✅ 今日活動模式正常，長者狀態良好")
        
        return recs
    
    def _generate_weekly_insights(self, daily_stats: list, falls: int, lying: int) -> List[str]:
        """生成每週洞察"""
        insights = []
        
        # 最安全 vs 最需關注的日子
        safest = min(daily_stats, key=lambda d: d["falls"] + d["lying"])
        worst = max(daily_stats, key=lambda d: d["falls"] + d["lying"])
        
        if worst["falls"] + worst["lying"] > 0:
            insights.append(f"本週最需關注：{worst['date']}（{worst['falls']} 次跌倒、{worst['lying']} 次躺臥警報）")
        
        insights.append(f"本週最安全：{safest['date']}")
        
        # 活動量趨勢
        avg_detections = sum(d["detections"] for d in daily_stats) / len(daily_stats)
        insights.append(f"平均每日偵測 {avg_detections:.0f} 次活動")
        
        if falls == 0:
            insights.append("✅ 本週無跌倒事件，表現良好")
        else:
            insights.append(f"⚠️ 本週共 {falls} 次跌倒事件，建議加強防護")
        
        return insights


def generate_sample_data(db: ActivityDatabase, days: int = 7):
    """生成模擬歷史數據用於測試"""
    
    zones = ["living_room", "bedroom", "bathroom", "kitchen"]
    activities_pool = ["standing", "sitting", "walking", "lying"]
    weights = [0.35, 0.30, 0.25, 0.10]  # 活動權重
    
    now = datetime.now()
    
    for day_offset in range(days, 0, -1):
        day_base = now - timedelta(days=day_offset)
        
        # 每天 50-150 條活動記錄
        num_activities = random.randint(50, 150)
        
        for _ in range(num_activities):
            hour = random.choices(
                range(24),
                weights=[1,1,1,1,1,2,5,8,10,10,8,7,8,7,6,5,6,8,10,8,5,3,2,1],
                k=1
            )[0]
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            ts = day_base.replace(hour=hour, minute=minute, second=second)
            
            activity = random.choices(activities_pool, weights=weights, k=1)[0]
            zone = random.choice(zones)
            confidence = random.uniform(0.5, 0.99)
            duration = random.randint(5, 300)
            
            cursor = db.conn.cursor()
            cursor.execute(
                "INSERT INTO activities (timestamp, person_id, zone_id, activity, confidence, duration_seconds) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (ts.isoformat(), "elderly_01", zone, activity, round(confidence, 3), duration)
            )
        
        # 每天 0-3 條警報
        num_alerts = random.choices([0, 0, 0, 1, 1, 2, 3], k=1)[0]
        
        for _ in range(num_alerts):
            hour = random.randint(6, 22)
            ts = day_base.replace(hour=hour, minute=random.randint(0, 59))
            
            alert_type = random.choice(["falling", "lying", "lying"])
            severity = "high" if alert_type == "falling" else "medium"
            zone = random.choice(["bathroom", "kitchen", "living_room"])
            confidence = random.uniform(0.75, 0.98)
            
            cursor = db.conn.cursor()
            cursor.execute(
                "INSERT INTO alerts (timestamp, person_id, zone_id, alert_type, severity, confidence) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (ts.isoformat(), "elderly_01", zone, alert_type, severity, round(confidence, 3))
            )
    
    db.conn.commit()


def format_daily_report_text(report: Dict) -> str:
    """將每日報告格式化為可讀文字"""
    s = report["summary"]
    a = report["alerts"]
    
    text = []
    text.append("=" * 55)
    text.append(f"  每日安全報告 — {report['date']}")
    text.append("=" * 55)
    text.append("")
    text.append(f"  安全評級: {s['safety_icon']} {s['safety_rating']}")
    text.append(f"  {s['safety_description']}")
    text.append("")
    text.append("--- 偵測統計 ---")
    text.append(f"  總偵測次數: {s['total_detections']}")
    text.append(f"  平均信心度: {s['average_confidence']:.1%}")
    text.append("")
    text.append("--- 警報統計 ---")
    text.append(f"  總警報數: {a['total']}")
    text.append(f"  跌倒事件: {a['fall_events']} 次")
    text.append(f"  躺臥警報: {a['lying_alerts']} 次")
    text.append("")
    text.append("--- 活動分佈 ---")
    for act_name, data in report["activity_distribution"].items():
        bar = "█" * int(data["percentage"] / 3)
        text.append(f"  {act_name:4s} {bar} {data['percentage']:.1f}% ({data['count']})")
    text.append("")
    text.append("--- 區域分析 ---")
    for zone, count in report["zone_analysis"].items():
        text.append(f"  {zone}: {count} 次")
    text.append("")
    text.append("--- 時段分析 ---")
    text.append(f"  活動高峰時段: {report['temporal_analysis']['peak_activity_hour']}")
    text.append("")
    text.append("--- 建議 ---")
    for rec in report["recommendations"]:
        text.append(f"  {rec}")
    text.append("")
    
    return "\n".join(text)


def format_weekly_report_text(report: Dict) -> str:
    """將每週報告格式化為可讀文字"""
    ws = report["weekly_summary"]
    
    text = []
    text.append("=" * 55)
    text.append(f"  每週趨勢報告")
    text.append(f"  {report['period']}")
    text.append("=" * 55)
    text.append("")
    text.append(f"  週安全評級: {ws['safety_icon']} {ws['safety_rating']}")
    text.append(f"  活動趨勢: {ws['activity_trend_icon']} {ws['activity_trend']} ({ws['trend_percentage']:+.1f}%)")
    text.append(f"  本週跌倒: {ws['total_falls']} 次")
    text.append(f"  本週躺臥警報: {ws['total_lying_alerts']} 次")
    text.append("")
    text.append("--- 每日明細 ---")
    text.append(f"  {'日期':12s} {'偵測':>6s} {'跌倒':>6s} {'躺臥':>6s} {'評級':>6s}")
    text.append(f"  {'-'*42}")
    for d in report["daily_breakdown"]:
        text.append(f"  {d['date']:12s} {d['detections']:>6d} {d['falls']:>6d} {d['lying']:>6d} {d['safety']:>6s}")
    text.append("")
    text.append("--- 洞察 ---")
    for insight in report["insights"]:
        text.append(f"  {insight}")
    text.append("")
    
    return "\n".join(text)


def format_anomalies_text(anomalies: List[Dict]) -> str:
    """格式化異常偵測結果"""
    if not anomalies:
        return "✅ 未偵測到異常行為模式"
    
    text = []
    text.append("=" * 55)
    text.append("  異常行為偵測報告")
    text.append("=" * 55)
    text.append("")
    
    severity_labels = {"high": "高", "medium": "中", "low": "低"}
    
    for a in anomalies:
        text.append(f"  {a['icon']} [{severity_labels[a['severity']]}] {a['message']}")
    
    text.append("")
    return "\n".join(text)
