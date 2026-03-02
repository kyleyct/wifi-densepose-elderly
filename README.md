# WiFi DensePose 長者防跌倒系統

基於 WiFi CSI 信號分析的非侵入式長者跌倒偵測系統，**無需攝影機**，完全保護隱私。

> 本專案基於 [ruvnet/wifi-densepose](https://github.com/ruvnet/wifi-densepose) 開源專案開發，專門針對長者居家安全場景進行定制。

---

## 功能特色

| 功能 | 說明 |
|------|------|
| 🚨 **跌倒即時偵測** | 96.5% 靈敏度，< 2 秒警報回應 |
| 📱 **Telegram 警報** | 跌倒/躺臥時自動通知家人 |
| 📊 **即時監控儀表板** | 網頁版視覺化監控介面 |
| 📈 **歷史數據分析** | 每日/每週報告、異常行為偵測 |
| 🔒 **完全保護隱私** | 僅使用 WiFi 信號，無攝影機 |
| 👥 **多人追蹤** | 最多同時追蹤 10 人 |

---

## 專案結構

```
wifi-densepose-elderly/
├── README.md                  ← 本文件
├── requirements.txt           ← Python 依賴
├── start.sh                   ← 快速啟動腳本
├── src/
│   ├── telegram_bot.py        ← Telegram Bot 警報系統
│   ├── analytics.py           ← 歷史數據分析引擎
│   ├── test_fall_detection.py ← 跌倒偵測模擬測試
│   ├── test_telegram_bot.py   ← Telegram Bot 測試
│   └── test_analytics.py      ← 數據分析測試
├── dashboard/
│   ├── index.html             ← 監控儀表板主頁
│   ├── base.css               ← 基礎樣式
│   ├── style.css              ← 設計樣式
│   ├── dashboard.css          ← 儀表板樣式
│   └── app.js                 ← 儀表板邏輯
└── docs/
    └── wifi-densepose-user-guide.pdf ← 完整使用指南
```

---

## 快速開始

### 環境需求

- Python 3.10+
- pip 套件管理器
- 現代瀏覽器（Chrome / Firefox / Safari）

### 1. Clone 專案

```bash
git clone https://github.com/kyleyct/wifi-densepose-elderly.git
cd wifi-densepose-elderly
```

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 使用監控儀表板

直接用瀏覽器開啟 `dashboard/index.html`，儀表板內建 Demo 模式，無需啟動任何伺服器即可體驗完整功能。

儀表板功能：
- 5 個 KPI 卡片（系統狀態、偵測人數、警報、回應時間、安全評級）
- 4 個房間即時佔用監控
- 活動分佈圖表 + 24 小時時間線
- 警報歷史記錄
- 支援深色模式

### 4. 執行模擬測試

```bash
# 測試 Telegram Bot（模擬模式，無需 Bot Token）
python3 src/test_telegram_bot.py

# 測試歷史數據分析（自動生成 7 天模擬數據）
python3 src/test_analytics.py
```

---

## 功能詳細說明

### Telegram Bot 警報系統

跌倒時自動發送 Telegram 訊息通知家人。

**警報類型：**
- 🚨🚨🚨 **跌倒警報** — 偵測到跌倒，立即通知
- 🚨 **躺臥警報** — 非睡房區域持續躺臥超過 60 秒
- ⚠️ **異常警報** — 其他異常行為模式

**智能功能：**
- 5 分鐘冷卻期（避免重複通知）
- 自動忽略睡房區域的躺臥狀態
- 信心度閾值過濾

**可用指令：**

| 指令 | 功能 |
|------|------|
| `/start` | 啟動機器人 |
| `/status` | 查詢即時狀態 |
| `/daily` | 今日安全摘要 |
| `/alerts` | 最近警報記錄 |
| `/help` | 使用說明 |

**設定步驟：**
1. 在 Telegram 搜尋 `@BotFather` → 發送 `/newbot` → 取得 Bot Token
2. 搜尋 `@userinfobot` → 取得 Chat ID
3. 在 `telegram_bot.py` 中填入 Token 和 Chat ID

---

### 歷史數據分析

自動記錄活動數據，生成安全報告。

**功能：**
- SQLite 資料庫自動記錄
- 每日安全報告（活動分佈、區域分析、時段分析）
- 每週趨勢報告（7 天明細、趨勢分析）
- 異常行為偵測：
  - 📉 活動量突然下降（可能表示身體不適）
  - 🌙 夜間異常活動（可能表示睡眠問題）
  - 🚨 跌倒頻率增加趨勢
  - 🚿 浴室長時間停留

---

## 硬件需求（Phase 2）

進入真實硬件模式需要以下設備：

| 品名 | 規格 | 數量 | 參考價格 |
|------|------|------|---------|
| ESP32-S3 開發板 | ESP32-S3-DevKitC-1 **N16R8**（帶天線版） | 2 塊 | ¥8-25/塊 |
| USB-C 數據線 | 數據線（非純充電線） | 2 條 | ¥3-8/條 |
| 5V USB 電源適配器 | 5V 1A 以上 | 2 個 | ¥5-10/個 |

**基本配置總費用：約 ¥35-80（HK$38-88）**

### 淘寶搜尋關鍵字

```
ESP32-S3-DevKitC-1 N16R8
```

### 選購注意事項

1. **型號必須含 S3** — 不要買成 ESP32（無 S3）或 ESP32-S2
2. **選 N16R8 或 N8R8** — 確保有足夠的 PSRAM
3. **選帶天線版（WROOM）** — 家居環境下板載天線已足夠
4. **USB 線買數據線** — 純充電線無法燒錄韌體

---

## 硬件安裝指南（Phase 2）

### 實體安裝

1. 將 2 塊 ESP32-S3 放置在房間**對面牆壁**
2. 距離 **3-5 米**，安裝高度 **1-1.5 米**（腰部高度）
3. 確保兩塊板之間**無大型遮擋物**
4. 使用 USB 電源適配器供電

### 軟件配置

```bash
# 1. Clone 完整的 WiFi DensePose 專案
git clone https://github.com/ruvnet/wifi-densepose.git
cd wifi-densepose

# 2. 安裝依賴
pip install -r requirements.txt
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 3. 設定環境變數（真實硬件模式）
export MOCK_POSE_DATA=false        # 關閉模擬模式
export SECRET_KEY="your-secret-key"
export ENVIRONMENT="development"
export REDIS_ENABLED="false"
export ENABLE_AUTHENTICATION="false"
export ENABLE_DATABASE_FAILSAFE="true"

# 4. 啟動伺服器
cd v1
PYTHONPATH=. python -m uvicorn src.app:app --host 0.0.0.0 --port 8000

# 5. 驗證
curl http://localhost:8000/health/live
```

### 多房間擴展

每個房間需要一對 ESP32-S3（一發一收），各房間使用不同的 WiFi 通道避免干擾。

建議覆蓋優先順序：**客廳 > 睡房 > 浴室 > 廚房**

---

## 系統架構

```
ESP32-S3 (發射端)
    │
    │  WiFi CSI 信號
    ▼
ESP32-S3 (接收端)
    │
    │  CSI 數據
    ▼
Python 伺服器 (FastAPI)
    │
    ├── DensePose 姿態分析
    ├── 跌倒偵測引擎
    ├── 活動追蹤
    │
    ├──→ Telegram Bot（即時警報）
    ├──→ 監控儀表板（視覺化）
    └──→ 數據分析（報告/趨勢）
```

---

## 常見問題

**Q: 會影響家中現有 WiFi 嗎？**
A: 不會。ESP32-S3 使用獨立通道，不會干擾現有網絡。

**Q: 需要攝影機嗎？**
A: 完全不需要。系統僅使用 WiFi 信號分析，保護隱私。

**Q: 可以同時追蹤多少人？**
A: 最多 10 人，適用於家庭和小型安老院。

**Q: 誤報率高嗎？**
A: 系統設有信心度閾值和冷卻期機制，有效降低誤報。

**Q: 停電怎麼辦？**
A: 建議配備 UPS 不斷電系統。恢復供電後系統自動重連。

**Q: 可以用在安老院嗎？**
A: 可以。支援多房間多人員同時監測，按需擴展 ESP32-S3 對數。

---

## 參考資源

- [WiFi DensePose 原始專案](https://github.com/ruvnet/wifi-densepose)
- [ESP32-S3 官方文檔](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/)
- [DigiKey HK ESP32-S3](https://www.digikey.hk/en/products/detail/espressif-systems/ESP32-S3-DEVKITC-1-N8R8/15295894)

---

## 授權

本專案基於 [MIT License](https://opensource.org/licenses/MIT) 開源。
