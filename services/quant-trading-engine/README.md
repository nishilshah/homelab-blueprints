# 📈 Quantitative Research & Trading Ingress (LXC 108)

[![OpenBB](https://img.shields.io/badge/OpenBB-Platform-000000?style=for-the-badge&logo=python&logoColor=white)](https://openbb.co)
[![Interactive Brokers](https://img.shields.io/badge/Interactive_Brokers-IB_Gateway-D91A2A?style=for-the-badge&logoColor=white)](https://www.interactivebrokers.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)

An on-premise quantitative financial research platform and automated execution system running inside a Debian 12 LXC container. Features **OpenBB SDK**, a **secure TradingView webhook listener**, and an **Interactive Brokers Gateway (IB Gateway)** bridge with 2-step Telegram trade confirmations.

---

## 🔗 Official Documentation & External Links

- **OpenBB Platform:** [openbb.co](https://openbb.co)
- **OpenBB Docs:** [docs.openbb.co](https://docs.openbb.co)
- **Interactive Brokers API:** [interactivebrokers.github.io](https://interactivebrokers.github.io)
- **ib_insync Python Library:** [github.com/erdewit/ib_insync](https://github.com/erdewit/ib_insync)
- **TradingView Webhooks:** [tradingview.com/support/solutions/43000529348](https://www.tradingview.com/support/solutions/43000529348-about-webhooks/)

---

## 🏗️ Execution Architecture & Risk Safeguards

```mermaid
flowchart TD
    TV["TradingView Alert Webhook"] --> Ingress["Flask Ingress Listener (Port 8080)<br/>Passphrase Verification"]
    
    subgraph Safeguards ["Risk & Margin Verification Engine"]
        Ingress --> CashCheck["Query Settled Cash from IBKR<br/>Hard Ceiling: Max $500 USD/Trade"]
        CashCheck --> MarginCheck{"Margin Prohibited?<br/>Cost <= Settled Cash"}
        MarginCheck -->|Passed| Bot["Telegram 2-Step Approval Bot<br/>(@quant_bot)"]
        MarginCheck -->|Failed| Reject["Reject & Log Warning"]
    end

    subgraph ApprovalFlow ["Human-In-The-Loop Execution"]
        Bot -->|5-Min TTL Callback Prompt| Trader["Authorized Trader Mobile"]
        Trader -->|Tap [ Approve Buy ]| Exec["IBKR Execution Engine"]
        Trader -->|Tap [ Reject ]| Cancel["Cancel Order"]
    end

    Exec -->|Strict Limit Order ONLY| IBG["IB Gateway (Port 4002)<br/>Paper/Live Trading Bridge"]
    IBG --> Market["Interactive Brokers Financial Markets"]
```

---

## ⚙️ Container Sizing & Recommendations

| Parameter | Specification | Notes |
| :--- | :--- | :--- |
| **Virtualization** | Debian 12 LXC Container | Unprivileged with `nesting=1` |
| **Cores** | 2 vCPUs | Python pandas calculations and async event loops |
| **Memory** | 4096 MB (4 GB) | IB Gateway JVM + OpenBB cache |
| **Disk** | 24 GB SSD (`local-lvm`) | Python virtual environments and audit database |
| **Ports** | `8080` (Webhook Ingress), `4002` (IB Gateway API) | Internal localhost & LAN only |

---

## 🚀 Step-by-Step Deployment

1. **Provision Container:**
   ```bash
   pct create 108 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
     --hostname quant-engine \
     --cores 2 \
     --memory 4096 \
     --swap 1024 \
     --rootfs local-lvm:24 \
     --net0 name=eth0,bridge=vmbr0,ip=192.168.1.248/24,gw=192.168.1.1 \
     --unprivileged 1 \
     --features nesting=1 \
     --onboot 1 \
     --start 1
   ```

2. **Install Python Quantitative Stack:**
   Enter container (`pct enter 108`):
   ```bash
   apt-get update && apt-get install -y python3 python3-pip python3-venv git curl build-essential

   python3 -m venv /opt/quant-env
   source /opt/quant-env/bin/activate
   pip install --upgrade pip
   pip install openbb ib_insync flask requests pandas exchange_calendars
   ```

3. **Configure Ingress Webhook Passphrase:**
   Create an environment file `/opt/quant/.env`:
   ```bash
   WEBHOOK_PASSPHRASE=<RANDOM_ALPHANUMERIC_SECRET>
   TELEGRAM_BOT_TOKEN=<TELEGRAM_BOT_TOKEN_FROM_BOTFATHER>
   TELEGRAM_CHAT_ID=<YOUR_TELEGRAM_CHAT_ID>
   IB_PORT=4002
   ```

4. **Verify TradingView Alert Ingress Payload Format:**
   ```json
   {
     "passphrase": "<YOUR_WEBHOOK_PASSPHRASE>",
     "action": "BUY",
     "ticker": "NASDAQ:NVDA",
     "price": 125.50,
     "strategy": "MeanReversion_1H"
   }
   ```
