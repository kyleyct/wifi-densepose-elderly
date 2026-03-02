#!/usr/bin/env python3
"""
WiFi DensePose 長者防跌倒模擬測試腳本
Fall Detection Simulation Test Script for Elderly Care

此腳本模擬以下場景：
1. 查詢系統狀態
2. 獲取即時姿態數據
3. 模擬跌倒偵測事件
4. 展示警報通知流程
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def print_section(title):
    print(f"\n--- {title} ---")

# ============================================================
# 1. 系統狀態檢查
# ============================================================
print_header("1. 系統狀態檢查 (System Health Check)")

resp = requests.get(f"{BASE_URL}/health/live")
data = resp.json()
print(f"系統狀態: {data['status']}")
print(f"時間戳記: {data['timestamp']}")

resp = requests.get(f"{API_URL}/status")
data = resp.json()
print(f"\nAPI 狀態: {data['api']['status']}")
print(f"版本: {data['api']['version']}")
print(f"姿態服務: {data['services']['pose']['status']}")
print(f"模擬數據模式: {data['services']['pose']['configuration']['mock_data']}")
print(f"信心閾值: {data['services']['pose']['configuration']['confidence_threshold']}")
print(f"最大偵測人數: {data['services']['pose']['configuration']['max_persons']}")

# ============================================================
# 2. 即時姿態偵測
# ============================================================
print_header("2. 即時姿態偵測 (Real-time Pose Detection)")

resp = requests.get(f"{API_URL}/pose/current")
data = resp.json()
print(f"幀 ID: {data['frame_id']}")
print(f"偵測到 {len(data['persons'])} 人")
print(f"處理時間: {data['processing_time_ms']} ms")

for person in data['persons']:
    print(f"\n  人員 {person['person_id']}:")
    print(f"    活動: {person['activity']}")
    print(f"    信心度: {person['confidence']:.2%}")
    print(f"    區域: {person.get('zone_id', 'N/A')}")
    print(f"    關鍵點數量: {len(person['keypoints'])}")

# ============================================================
# 3. 區域佔用情況
# ============================================================
print_header("3. 房間佔用情況 (Room Occupancy)")

resp = requests.get(f"{API_URL}/pose/zones/summary")
data = resp.json()
print(f"總人數: {data['total_persons']}")
print(f"活躍區域: {data['active_zones']} 個")

for zone_id, zone_data in data['zones'].items():
    print(f"  {zone_id}: {zone_data['occupancy']} 人 ({zone_data['status']})")

# 查詢客廳
print_section("客廳詳情 (Living Room)")
resp = requests.get(f"{API_URL}/pose/zones/living_room/occupancy")
data = resp.json()
print(f"客廳人數: {data['current_occupancy']}")
for p in data['persons']:
    print(f"  - {p['person_id']}: {p['activity']} (信心度 {p['confidence']:.2%})")

# ============================================================
# 4. 活動記錄分析
# ============================================================
print_header("4. 最近活動記錄 (Recent Activities)")

resp = requests.get(f"{API_URL}/pose/activities?limit=10")
data = resp.json()

fall_count = 0
lying_count = 0
for act in data['activities']:
    status_icon = "⚠️" if act['activity'] in ['falling', 'lying'] else "✓"
    if act['activity'] == 'falling':
        fall_count += 1
    if act['activity'] == 'lying':
        lying_count += 1
    print(f"  {status_icon} {act['person_id']} | {act['zone_id']} | "
          f"{act['activity']} | 信心度 {act['confidence']:.2%} | "
          f"持續 {act['duration_seconds']}s")

print(f"\n活動摘要:")
print(f"  偵測到跌倒事件: {fall_count} 次")
print(f"  躺臥狀態: {lying_count} 次")

# ============================================================
# 5. 模擬跌倒偵測警報流程
# ============================================================
print_header("5. 模擬跌倒偵測警報流程 (Fall Detection Alert Simulation)")

print("模擬場景: 長者在客廳跌倒")
print("-" * 40)

# 模擬連續監測
for i in range(5):
    resp = requests.get(f"{API_URL}/pose/current")
    data = resp.json()
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for person in data['persons']:
        activity = person['activity']
        confidence = person['confidence']
        
        # 模擬跌倒偵測邏輯
        if activity == 'lying' and confidence > 0.7:
            print(f"\n🚨 [{timestamp}] 警報！偵測到異常狀態！")
            print(f"   人員: {person['person_id']}")
            print(f"   狀態: {activity} (躺臥)")
            print(f"   信心度: {confidence:.2%}")
            print(f"   區域: {person.get('zone_id', '未知')}")
            print(f"   → 觸發跌倒警報通知")
            print(f"   → 通知方式: WebSocket 即時推送 + Webhook")
        elif activity == 'falling':
            print(f"\n🚨🚨🚨 [{timestamp}] 緊急警報！偵測到跌倒！")
            print(f"   人員: {person['person_id']}")
            print(f"   狀態: {activity} (跌倒)")
            print(f"   信心度: {confidence:.2%}")
            print(f"   區域: {person.get('zone_id', '未知')}")
            print(f"   → 立即觸發緊急通知")
        else:
            print(f"  ✓ [{timestamp}] {person['person_id']}: "
                  f"{activity} ({confidence:.2%}) - 正常")
    
    time.sleep(1)

# ============================================================
# 6. 統計報告
# ============================================================
print_header("6. 統計報告 (Statistics Report)")

resp = requests.get(f"{API_URL}/pose/stats")
data = resp.json()
stats = data['statistics']

print(f"統計期間: 過去 {data['period']['hours']} 小時")
print(f"總偵測次數: {stats['total_detections']}")
print(f"成功偵測: {stats['successful_detections']}")
print(f"成功率: {stats['success_rate']:.2%}")
print(f"平均信心度: {stats['average_confidence']:.2%}")
print(f"平均處理時間: {stats['average_processing_time_ms']:.1f} ms")
print(f"偵測到的不同人數: {stats['unique_persons']}")
print(f"最活躍區域: {stats['most_active_zone']}")

print(f"\n活動分佈:")
for activity, ratio in stats['activity_distribution'].items():
    bar = "█" * int(ratio * 40)
    label_map = {
        'standing': '站立',
        'sitting': '坐下', 
        'walking': '行走',
        'lying': '躺臥'
    }
    print(f"  {label_map.get(activity, activity):4s} {bar} {ratio:.1%}")

# ============================================================
# 7. 長者防跌倒配置建議
# ============================================================
print_header("7. 長者防跌倒配置建議")

config = {
    "domain": "healthcare",
    "scenario": "elderly_fall_detection",
    "zones": [
        {"id": "bedroom", "type": "BEDROOM", "alert_activities": ["falling", "lying"]},
        {"id": "bathroom", "type": "BATHROOM", "alert_activities": ["falling", "lying"]},
        {"id": "living_room", "type": "LIVING_ROOM", "alert_activities": ["falling"]},
        {"id": "kitchen", "type": "KITCHEN", "alert_activities": ["falling"]},
    ],
    "analytics": {
        "enable_fall_detection": True,
        "fall_confidence_threshold": 0.8,
        "inactivity_timeout_seconds": 300,
        "lying_alert_delay_seconds": 60,
    },
    "alerts": {
        "enable_activity_alerts": True,
        "notification_methods": ["webhook", "websocket"],
        "max_alerts_per_hour": 10,
        "cooldown_minutes": 5,
    }
}

print(json.dumps(config, indent=2, ensure_ascii=False))

print_header("測試完成 ✓")
print("Phase 1 模擬環境測試完成！")
print("系統已成功在模擬模式下運行，所有 API 端點均可正常使用。")
print("\n下一步建議:")
print("  1. 購買 ESP32-S3 硬體進入 Phase 2")
print("  2. 或繼續在模擬模式下開發自訂警報整合（如 Telegram Bot）")
