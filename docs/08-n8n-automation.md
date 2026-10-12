# 🤖 08 - n8n Workflow Automation Engine (LXC 107)

This blueprint documents deploying **n8n**, a self-hosted node-based workflow automation platform, coupled with a Python Telegram long-polling daemon for 24/7 background AI agents and financial ingestion pipelines.

---

## ⚙️ 1. Container Sizing & Provisioning

- **VM ID:** `107`
- **Hostname:** `n8n-automation`
- **Memory:** `4096 MB`
- **Cores:** `2`
- **Disk:** `20 GB` on `local-lvm`
- **Static IP:** `192.168.1.247/24`
- **Features:** Unprivileged LXC, nesting enabled.

### Provisioning Command:
```bash
pct create 107 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --hostname n8n-automation \
  --cores 2 \
  --memory 4096 \
  --swap 1024 \
  --rootfs local-lvm:20 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.247/24,gw=192.168.1.1 \
  --unprivileged 1 \
  --features nesting=1 \
  --onboot 1 \
  --start 1
```

---

## 🚀 2. Docker Compose Deployment of n8n

Enter container (`pct enter 107`):

1. **Install Docker Engine:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
   ```

2. **Deploy n8n Compose Stack:**
   Create `/opt/n8n/docker-compose.yml`:

```yaml
version: "3.8"

services:
  n8n:
    image: docker.n8n.io/n8nio/n8n:latest
    container_name: n8n-app
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=192.168.1.247
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - NODE_ENV=production
      - WEBHOOK_URL=http://192.168.1.247:5678/
      - GENERIC_TIMEZONE=America/Vancouver
      - N8N_SECURE_COOKIE=false
    volumes:
      - /var/lib/n8n:/home/node/.n8n
```

3. **Start n8n:**
   ```bash
   cd /opt/n8n && docker compose up -d
   ```

---

## 📡 3. 24/7 Telegram Long-Polling Relay Architecture

To allow Telegram bots to work securely behind a residential firewall without opening public ingress ports or setting up public webhooks, run a Python systemd service using long-polling (`getUpdates`) that relays events to internal n8n webhook nodes.

### Systemd Service Blueprint (`/etc/systemd/system/telegram-relay.service`):
```ini
[Unit]
Description=Telegram Long-Polling Relay for n8n Webhooks
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/telegram-relay
ExecStart=/opt/telegram-relay/.venv/bin/python3 /opt/telegram-relay/relay.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
systemctl daemon-reload
systemctl enable --now telegram-relay.service
```

---

## 🔗 4. Common Homelab Ingestion Pipelines

1. **Email to Financial Ledger (`scotia-rbc-firefly-sync`):**
   - Polls mailbox over IMAP for transaction alerts (debit purchases, credit card charges, e-Transfers).
   - Classifies merchant into spending buckets.
   - Dispatches `POST` request to Firefly III REST API.

2. **Telegram AI Agent (`@your_homelab_bot`):**
   - User texts natural language queries to Telegram.
   - Long-polling daemon dispatches message payload to `http://127.0.0.1:5678/webhook/homelab-agent`.
   - n8n calls Google Gemini / LangChain agent with custom homelab diagnostic tool API.
