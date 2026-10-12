# 📈 10 - Quantitative Research & Trading Ingress (LXC 108)

This blueprint documents deploying an automated quantitative research and trading system inside a Debian 12 LXC container, combining the **OpenBB Financial Platform**, a secure **TradingView Alert Ingress Webhook**, and an **Interactive Brokers (IBKR) Gateway connector** with 2-step Telegram trade confirmations.

---

## ⚙️ 1. Container Sizing & Provisioning

- **VM ID:** `108`
- **Hostname:** `quant-engine`
- **Memory:** `4096 MB`
- **Cores:** `2`
- **Disk:** `24 GB` on `local-lvm`
- **Static IP:** `192.168.1.248/24`
- **Features:** Unprivileged LXC, nesting enabled.

### Provisioning Command:
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

---

## 🛠️ 2. OpenBB & Python Quantitative Environment

Enter container (`pct enter 108`):

```bash
apt-get update && apt-get install -y python3 python3-pip python3-venv git curl build-essential

# Create isolated Python virtual environment
python3 -m venv /opt/quant-env
source /opt/quant-env/bin/activate

# Install OpenBB platform & Quantitative analysis tools
pip install --upgrade pip
pip install openbb ib_insync flask requests pandas numpy exchange_calendars
```

---

## 🛡️ 3. TradingView Alert Ingress & Risk Safeguards

The ingress listener runs a Flask service on port `8080` to receive TradingView alert webhooks with strict safeguards:

1. **Passphrase Verification:** Incoming JSON payloads must include a secret `passphrase` matching the local environment; unauthorized requests are rejected with HTTP 401.
2. **Margin & Settled Cash Verification:** Before queuing orders, the system queries settled cash from IBKR Gateway. No borrowing or margin expansion is permitted.
3. **Strict Limit Orders Only:** Prevents market order slippage.
4. **2-Step Telegram Confirmation:** Alerts trigger an interactive Telegram prompt to the authorized trader (`[ Approve Buy ]` / `[ Reject ]`) with a 5-minute Time-To-Live (TTL). Orders are never submitted automatically without physical human approval.

### Ingress Payload Example:
```json
{
  "passphrase": "<YOUR_WEBHOOK_SECRET_PASSPHRASE>",
  "action": "BUY",
  "ticker": "NASDAQ:NVDA",
  "price": 125.50,
  "strategy": "MeanReversion_1H"
}
```

---

## 🔌 4. Interactive Brokers Gateway (IB Gateway) Integration

- **Paper Trading Port:** `4002` (or `7497` for TWS)
- **Live Trading Port:** `4001` (or `7496` for TWS)
- **API Settings:**
  - Enable ActiveX and Socket Clients.
  - Trusted IP: `127.0.0.1` and container subnet.
  - Read-Only API: Disabled for trading bot, or Enabled for research-only mode.
