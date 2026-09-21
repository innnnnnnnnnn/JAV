# 🚀 JAV Telegram Bot

這是一個專為 Telegram 開發的自動化機器人，每天定時為您爬取 OneJAV 的最新影片，將標題翻譯成中文，並推送到您的 Telegram 頻道或聊天室。您還能透過 Bot 介面一鍵將種子傳送到 QNAP NAS 進行下載，或者將檔案加到 RSS 供其他下載器訂閱。

## ✨ 核心功能

*   **📅 定時自動推播**：每天 22:00（台北時間）自動爬取今日最新影片並推播。
*   **🌍 自動翻譯**：整合 DeepL API，將日文影片標題與標籤自動翻譯成中文。
*   **📡 RSS 產生器**：內建 Web Server (預設 Port 8765)，可以自動生成訂閱用的 `rss.xml` 供下載軟體使用。
*   **📥 QNAP 整合**：一鍵將想看的影片直接加入 QNAP Download Station 排程下載。
*   **🤖 豐富的 Bot 指令**：
    *   `YYYY/MM/DD`：手動查詢指定日期的影片。
    *   `YYYY/MM/DD-YYYY/MM/DD`：查詢指定日期區間（最多14天）。
    *   `/push`：手動觸發今日影片的推播（不會影響日常背景輪詢）。
    *   `/fix [code] [url]`：手動修正損壞的種子連結，或者輸入 `/fix` 重新更新全部。
    *   `/clear`：清空 RSS 訂閱清單。

## ⚙️ 系統需求

- Python 3.10+ 或 Docker (推薦使用 Docker)
- Telegram Bot Token (請透過 [BotFather](https://t.me/botfather) 取得)
- QNAP NAS (若需要一鍵下載功能)

## 🛠 安裝與設定

1.  **環境變數設定**：
    請複製一份 `.env.example` 並命名為 `.env`，然後填入您的相關憑證。
    ```bash
    cp .env.example .env
    ```
    
    `.env` 檔案應包含以下設定：
    ```env
    TELEGRAM_BOT_TOKEN=你的Bot_Token
    TELEGRAM_CHAT_ID=你的頻道或用戶ID
    QNAP_HOST=http://你的NAS_IP:8080
    QNAP_USERNAME=你的NAS帳號
    QNAP_PASSWORD=你的NAS密碼
    QNAP_DOWNLOAD_PATH=/Multimedia/Downloads
    DEEPL_AUTH_KEY=你的DeepL_API_Key
    ```

2.  **本地啟動 (不使用 Docker)**：
    ```bash
    # 安裝套件
    pip install -r requirements.txt
    
    # 啟動主程式
    python main.py
    ```

## 🐳 Docker 與 OCI 部署

強烈建議使用 Docker 運行以確保環境一致。我們也提供了專門給 Oracle Cloud Infrastructure (OCI) 的一鍵部署腳本。

### 部署到 OCI：
1. 確保 `deploy_oci.sh` 中的 `OCI_IP` 及 `SSH_KEY` 是正確的。
2. 執行以下指令進行部署：
   ```bash
   ./deploy_oci.sh
   ```
部署腳本會自動將程式碼同步到伺服器並使用 `docker compose up -d --build` 重新構建及啟動。

### OCI 伺服器常用維護指令：
- **查看日誌**：`sudo docker compose logs -f jav-bot`
- **重新啟動**：`sudo docker compose restart jav-bot`

## 🔄 版本管理說明

本專案使用 Git 及 GitHub 進行版本控制。
如果您在本地有修改功能，請使用以下指令進行提交並更新遠端伺服器：

```bash
git add .
git commit -m "你的更新說明"
git push origin main
```

您可以善用 Git 標籤 (Tags) 來管理里程碑，例如：`v1.0.0`。

---
*Disclaimer: 此專案僅供學術研究與自動化學習交流使用。*
