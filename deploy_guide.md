# 🚀 JAV 部署到 OCI (Oracle Cloud Infrastructure) 指南

我已經為你準備好了將 `JAV` 項目部署到 OCI 的所有必要文件。部署方案採用 **Docker + Docker Compose**，這能確保環境一致性並方便管理。

## 📁 準備的文件

1.  **`requirements.txt`**: 定義了所有 Python 依賴包。
2.  **`Dockerfile`**: 基於 Python 3.10-slim 的鏡像構建指令。
3.  **`.dockerignore`**: 排除本地開發環境的文件（如 `venv`、`__pycache__` 等）。
4.  **`docker-compose.yml`**: 使用 `docker-compose` 一鍵啟動容器，支持自動重啟和數據持久化。
5.  **`deploy_oci.sh`**: 自动化部署腳本（rsync + ssh + docker）。

---

## 🛠 部署步驟 (本地操作)

在終端中執行以下命令即可一鍵部署：

```bash
cd /Users/innnnnnnnnnnmbp/Downloads/Antigravity/JAV
./deploy_oci.sh
```

---

## ⚠️ 重要提醒：QNAP 連接

目前 `.env` 中的 `QNAP_HOST` 設定為 `http://192.168.0.198:8080`：

-   **內網連接問題**：如果你的 OCI 實例不在你的家庭/辦公室本地網絡中，且沒有通過 VPN (如 Tailscale, WireGuard) 與 QNAP 建立連接，則 OCI 上的 Bot 將**無法**直接訪問該 IP。
-   **解決方案**：
    -   如果使用了 Tailscale，請將 `QNAP_HOST` 修改為 QNAP 的 Tailscale IP。
    -   或者，你需要一個公網 IP 或 DDNS。

---

## 🔍 遠端管理指令 (OCI 上)

如果你需要登入手動查看日誌或重新啟動：

```bash
# 登入 OCI (假設 IP 為 152.67.235.132)
ssh -i /Users/innnnnnnnnnnmbp/Downloads/Antigravity/ssh-key-2026-03-13.key opc@152.67.235.132

# 查看日誌
cd ~/JAV
sudo docker-compose logs -f jav-bot

# 手動重啟
sudo docker-compose restart jav-bot
```

---

## 💬 接下來的建議

如果你需要我協助設置 **Tailscale** 以便 OCI 訪問 QNAP，或者需要修改 OCI 的防火牆規則 (Ingress Rules)，請告訴我！
