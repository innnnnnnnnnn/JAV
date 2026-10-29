# 🚀 JAV Telegram Bot

這是一個專為 Telegram 開發的 JAV 最新影片自動化抓取與推播機器人。每天定時為您爬取當日最新影片，並使用免費無限制的多通道翻譯引擎將日文片名與標籤翻譯為繁體中文，推播至您的 Telegram 頻道或聊天室。您還能透過 Bot 介面一鍵將種子傳送到 QNAP NAS 進行排程下載，或將種子加到 RSS 供各類下載器訂閱。

---

## ✨ 核心功能

* **📅 定時自動推播（去重保護）**：
  * 每天 22:00（台北時間，GMT+8）自動爬取今日最新影片並推播。
  * 內建 `pushed_codes.json` 去重記錄庫，即使重啟或多次觸發也**絕不重複推播**。
* **🌐 免費無限制中文翻譯**：
  * 採用 Google 官方擴充通道多節點輪替，繞過雲端機房 IP 的 429 限制。
  * **完全免費、無字數上限、無需 API Key**，保證片名與標籤 100% 翻譯為繁體中文。
  * 同步支援 DeepL API 及 MyMemory 作為多重備援。
* **🔄 雙來源爬蟲容錯機制**：
  * 主來源為 `onejav.com`，遭遇 Cloudflare 阻擋（403）時**自動無縫切換**備援來源 `ffjav.com`。
  * 支援番號連字號自動模糊匹配（例如 `SNOS413` 自動嘗試 `SNOS-413`），提升命中率。
* **📡 內建 RSS 訂閱伺服器**：
  * 內建 aiohttp Web Server（預設 Port `8765`），提供 `/` 及 `/rss.xml` 供 QNAP Download Station 或其他下載器訂閱。
* **📥 QNAP NAS 一鍵下載**：
  * 點擊 Telegram 訊息按鈕直接將種子新增至 QNAP NAS 下載排程。
* **🛠 強大的 `/fix` 修復指令**：
  * `/fix`（無參數）：多執行緒並行重新爬取並刷新 RSS 中所有失效的種子連結。
  * `/fix <番號>`：自動爬取該番號的最新種子網址並更新本地快取與 RSS。
  * `/fix <番號> <網址>`：手動為指定番號綁定種子網址。
  * **回覆訊息輸入 `/fix`**：自動從所回覆的影片訊息中提取番號並立即更新。
* **🔍 手動查詢功能**：
  * 輸入 `YYYY/MM/DD`：手動查詢指定日期的影片。
  * 輸入 `YYYY/MM/DD-YYYY/MM/DD`：查詢指定日期區間（最多 14 天）。
  * 輸入 `/push`：立即手動觸發今日影片推播。
  * 輸入 `/clear`：清空 RSS 訂閱清單。

---

## ⚙️ 系統需求

- Python 3.10+ 或 Docker (推薦使用 Docker)
- Telegram Bot Token (請透過 [@BotFather](https://t.me/botfather) 取得)
- QNAP NAS (若需要一鍵下載功能)

---

## 🛠 安裝與設定

1. **環境變數設定**：
   複製 `.env.example` 並命名為 `.env`，填入相關設定：
   ```bash
   cp .env.example .env
   ```
   
   `.env` 內容範例：
   ```env
   TELEGRAM_BOT_TOKEN=你的Telegram_Bot_Token
   TELEGRAM_CHAT_ID=你的頻道或用戶ID
   QNAP_HOST=http://你的NAS_IP:8080
   QNAP_USERNAME=你的NAS帳號
   QNAP_PASSWORD=你的NAS密碼
   QNAP_DOWNLOAD_PATH=/Multimedia/Downloads
   # 可選：若有 DeepL API Key 亦可填入作為額外備援
   DEEPL_API_KEY=你的DeepL_API_Key
   ```

2. **本地啟動 (不使用 Docker)**：
   ```bash
   # 安裝依賴
   pip install -r requirements.txt
   
   # 啟動機器人
   python main.py
   ```

---

## 🐳 Docker 與 OCI 雲端部署

本專案支援 Docker Compose 容器化部署，並附帶 Oracle Cloud Infrastructure (OCI) 一鍵部署腳本。

### 部署到 OCI：
1. 確認 `deploy_oci.sh` 中的 `OCI_IP` 及 `SSH_KEY` 設定正確。
2. 執行一鍵部署腳本：
   ```bash
   ./deploy_oci.sh
   ```
   腳本會自動將程式碼同步至遠端主機，並透過 `docker compose up -d --build` 重新構建並啟動容器。

### 常用維護指令：
* **查看即時日誌**：
  ```bash
  sudo docker logs -f jav-jav-bot-1
  ```
* **重新啟動容器**：
  ```bash
  sudo docker compose restart
  ```
* **停止服務**：
  ```bash
  sudo docker compose down
  ```

---

## 🏷️ 版本管理與發行紀錄 (Changelog)

本專案嚴格遵循 [語意化版本 (Semantic Versioning)](https://semver.org/lang/zh-TW/)：

### 📌 [v2.0.0] - 2026-10-30
* **重大升級 (Major Release)**：
  * **雙爬蟲來源架構**：新增 `ffjav.com` 作為 `onejav.com` 的備援來源，解決 Cloudflare 403 阻擋問題，支援自動連字號轉換。
  * **全新免費翻譯引擎**：採用 Google Chrome 官方擴充通道，徹底解決雲端機房 IP 的 429 限制，實現 100% 免費無限制繁體中文翻譯。
  * **推播去重與分頁修復**：修正 `ffjav` 每日分頁抓取邏輯，加入持久化 `pushed_codes.json` 去重庫，確保每日 22:00 推播絕對不重複。
  * **重構 `/fix` 指令**：支援回覆訊息修復、單一番號即時爬取更新、以及非同步並行全量刷新。
  * **資料持久化強化**：在 `docker-compose.yml` 中完整掛載 `torrents.json`、`rss_items.json`、`pushed_codes.json` 及 `rss.xml`。

### 📌 [v1.0.0] - 2026-05-04
* 初始正式版本發行。
* 支援 OneJAV 每日抓取與 DeepL 翻譯。
* 整合 Telegram Bot 與 QNAP Download Station。
* 提供內建 RSS 訂閱伺服器。

---
*Disclaimer: 此專案僅供程式開發、學術研究與自動化技術學習交流使用。*
