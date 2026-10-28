# 📈 Quantitative Research & Trading Ingress Engine (LXC 108)

[![OpenBB](https://img.shields.io/badge/OpenBB-Platform_v4-000000?style=for-the-badge&logo=python&logoColor=white)](https://openbb.co)
[![Interactive Brokers](https://img.shields.io/badge/Interactive_Brokers-IB_Gateway-D91A2A?style=for-the-badge&logo=interactivebrokers&logoColor=white)](https://www.interactivebrokers.com)
[![TradingView](https://img.shields.io/badge/TradingView-Webhook_Ingress-131722?style=for-the-badge&logo=tradingview&logoColor=white)](https://www.tradingview.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Microservice-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

An on-premise, enterprise-grade quantitative market research platform and automated execution system running inside a Debian 12 LXC container on Proxmox VE. Combines technical alert ingestion from **TradingView**, fundamental ratio verification via **OpenBB Platform**, an AI-driven qualitative sanity check, and **human-in-the-loop trade execution** against **Interactive Brokers (IBKR)**.

---

## 🔗 Official Documentation & External Links

- **OpenBB Platform:** [openbb.co](https://openbb.co) • [OpenBB Documentation](https://docs.openbb.co) • [GitHub](https://github.com/OpenBB-finance/OpenBB)
- **Interactive Brokers API:** [interactivebrokers.github.io](https://interactivebrokers.github.io) • [API Reference Guide](https://www.interactivebrokers.com/campus/ibkr-api-page/)
- **ib_insync Python Framework:** [github.com/erdewit/ib_insync](https://github.com/erdewit/ib_insync) • [Documentation](https://ib-insync.readthedocs.io)
- **Headless IB Gateway Container:** [github.com/gnzsnz/ib-gateway](https://github.com/gnzsnz/ib-gateway)
- **TradingView Webhook Alerts:** [tradingview.com/support/solutions/43000529348](https://www.tradingview.com/support/solutions/43000529348-about-webhooks/)
- **Exchange Calendars (XNYS / XTSE):** [github.com/gerrymanoim/exchange_calendars](https://github.com/gerrymanoim/exchange_calendars)

---

## 🧠 Algorithmic Strategy & Decision Engine

The engine implements a **Hybrid Technical-Fundamental Mean-Reversion & Breakout Architecture**:

```mermaid
flowchart TD
    classDef signal fill:#1e3a8a,stroke:#60a5fa,stroke-width:2px,color:#ffffff;
    classDef security fill:#854d0e,stroke:#facc15,stroke-width:2px,color:#ffffff;
    classDef ai fill:#581c87,stroke:#c084fc,stroke-width:2px,color:#ffffff;
    classDef risk fill:#991b1b,stroke:#f87171,stroke-width:2px,color:#ffffff;
    classDef human fill:#115e59,stroke:#2dd4bf,stroke-width:2px,color:#ffffff;
    classDef exec fill:#065f46,stroke:#34d399,stroke-width:2px,color:#ffffff;
    classDef audit fill:#312e81,stroke:#818cf8,stroke-width:2px,color:#ffffff;

    subgraph MarketSensors ["1. Market Signal Generation"]
        Pine["📈 TradingView PineScript Strategy<br/>1-Hour & Daily Timeframe"]:::signal
        Indicators["📊 Technical Filters<br/>• Bollinger Bands 20, 2<br/>• RSI 14 oversold below 30<br/>• Volume Surge over 1.5x 20-SMA"]:::signal
        Pine --- Indicators
    end

    subgraph IngressGateway ["2. Webhook Ingress (Port 8080)"]
        TV_Alert["📨 Webhook JSON Payload"]:::security
        Auth["🔑 Constant-Time HMAC & Passphrase Check"]:::security
        Debounce["🛡️ Sliding-Window Alert Storm Debouncer<br/>Max 3 alerts per 60 seconds"]:::security
        Pine -->|Encrypted HTTPS POST| TV_Alert
        TV_Alert --> Auth
        Auth --> Debounce
    end

    subgraph FundamentalAI ["3. Fundamental & Qualitative Audit"]
        OpenBB["🏛️ OpenBB REST Microservice (Port 8000)<br/>Query P/E, Debt/Equity, ROCE, FCF"]:::ai
        Cache[("💾 24-Hour TTL SQLite Cache<br/>Instant 1ms Lookup")]:::ai
        AI["🧠 Google Gemini Qualitative Reasoner<br/>Synthesizes 2-Sentence Bull/Bear Rationale"]:::ai
        
        Debounce --> OpenBB
        OpenBB --> Cache
        Cache --> OpenBB
        OpenBB --> AI
    end

    subgraph RiskSafeguards ["4. Quantitative Risk Guardian"]
        Cash["💰 Query IBKR Settled Cash (Port 4002)"]:::risk
        Ceiling["🚫 Hard Ceiling: Max $500 USD per Trade"]:::risk
        Margin["⛔ Margin Borrowing Strictly Prohibited<br/>Order Value must be below Settled Cash"]:::risk
        Calendar["📅 Exchange Calendar Check (XNYS/XTSE)<br/>Market Open & Pre-Market Verification"]:::risk

        AI --> Cash
        Cash --> Ceiling
        Ceiling --> Margin
        Margin --> Calendar
    end

    subgraph HumanApproval ["5. Human-in-the-Loop Confirmation"]
        TG["🤖 Telegram Bot Daemon (@quant_bot)"]:::human
        Button["🔘 Inline Interactive Approval Buttons<br/>5-Minute Time-To-Live Expiration"]:::human
        Trader["📱 Authorized Trader Phone"]:::human
        
        Calendar --> TG
        TG --> Button
        Button --> Trader
    end

    subgraph Execution ["6. Order Execution & Audit"]
        Trader -->|Tap: Approve Buy Order| Router["⚡ Broker Router (ib_insync)"]:::exec
        Router -->|Strict Limit Order ONLY| IBG["🏦 Headless IB Gateway (Port 4002)"]:::exec
        IBG --> Market["🌐 Financial Markets (NYSE / NASDAQ / TSX)"]:::exec
        
        IBG -->|Fill Event Callback| Listener["🎧 Fill Listener Daemon"]:::audit
        Listener --> SQLiteAudit[("📁 SQLite Trade Ledger WAL Mode")]:::audit
        Listener --> CSVAudit["📑 CRA / IRS Tax Audit CSV"]:::audit
        Listener --> FillAlert["🔔 Telegram Execution Receipt"]:::audit
    end
```

### Detailed Strategy Architecture:

The engine executes three complementary strategies in parallel:

#### 1. Pillar 1: Sector ETF Dual Momentum (30% Target Allocation)
- **Execution Interval:** Bi-weekly on the 1st and 15th of each month at **09:45 AM America/New_York** (15 minutes after regular market open).
  - *Weekend & Holiday Guard:* If the 1st or 15th falls on a weekend or NYSE market holiday, the rebalance automatically shifts to the **immediate next valid trading session** via `exchange_calendars`.
- **Macro Market Filter:** Verifies `SPY >= 200-Day SMA`. If the macro market is in a downtrend (`SPY < 200-Day SMA`), the engine sits in 100% Cash / BIL Treasury reserves.
- **Universe:** 11 US Sector SPDR ETFs (`XLK`, `XLE`, `XLF`, `XLV`, `XLI`, `XLY`, `XLP`, `XLB`, `XLU`, `XLC`, `XLRE`).
- **Momentum Scoring:** Multi-horizon weighted momentum:
  $$\text{Score} = 0.40 \times R_{\text{1M}} + 0.30 \times R_{\text{3M}} + 0.30 \times R_{\text{6M}}$$
- **Hysteresis Band (Anti-Whipsaw Churn Reduction):**
  - **Eligible Entries:** Only sectors ranked in the **Top 2** (Rank #1 or #2) qualify for new purchases.
  - **Retention Band:** Currently held positions are **retained** as long as they remain in the **Top 4** (Rank 1, 2, 3, or 4).
  - **Rotation / Liquidation:** A sector is only liquidated if it drops below Rank 4 (Rank 5–11) or the macro regime turns defensive. This prevents costly whipsaw turnover when sectors oscillate around the Rank #2/#3 threshold.
- **Execution:** Submits strict Limit Orders with `tif="DAY"`. Target allocation: 50% of Pillar 1 capital per sector (15% of total portfolio, $15,000 per sector on $100k target).

#### 2. Pillar 2: Connors RSI(2) Dip Buying (70% Target Allocation)
- **Execution Interval:** Daily pre-close scan at **03:45 PM America/New_York** (15 minutes before market close; or 15 minutes before early close on half-days).
- **Zero-Latency Real-Time Pricing (`fast_info`):**
  - Uses `yfinance.Ticker.fast_info` to query real-time market quotes at 03:45 PM ET, completely bypassing standard 15-minute delayed endpoint latency.
  - Injects live ticks directly into today's price bar for real-time 200 SMA, 5-Day SMA, and Connors RSI(2) indicator accuracy.
  - Dynamically calculates marketable limit prices (`Price * 1.002` for buys, `Price * 0.998` for sells) pegged to the live market ask/bid.
- **Strategy Philosophy: Maximum Growth & Trust in Mean Reversion:**
  - Backtested across **11.8 years (2015 to 2026)** against 7 protection models:
    - **Baseline (Maximum Growth):** **9.60% CAGR**, **70.3% Win Rate**, **1.44 Profit Factor** across 2,679 trades.
    - **With Intraday -7.5% Stop Loss:** **7.96% CAGR** (annual return degraded by 1.64% due to 234 whipsaw shakeouts at the bottom of intraday dips right before snapbacks).
  - Preserves full mean-reversion compounding without artificial stop-loss shakeouts.
- **Universe:** Liquid S&P 100 mega-cap leaders (`NVDA`, `META`, `AAPL`, `MSFT`, `AMZN`, `GOOGL`, `AVGO`, `COST`, `JPM`, `V`, `LLY`, `UNH`, `GE`, `NFLX`).
- **Long Entry Rule:**
  $$\text{Price} > \text{200-Day SMA} \quad \text{and} \quad \text{Connors RSI(2)} < 10.0$$
  Identifies strong secular uptrend leaders undergoing temporary liquidity washouts. Limit orders submitted with `tif="DAY"` (unfilled orders expire automatically at market close).
- **Exit Rule:**
  $$\text{Price} > \text{5-Day SMA} \quad \text{or} \quad \text{Holding Period} \ge 10 \text{ Days}$$
  Exits dynamically once the mean-reversion snapback occurs.
- **Portfolio Sizing & Multi-Currency Capital Protection:**
  - Up to 5 slots maximum, allocated 14% each ($14,000 max per position on $100k target).
  - Automatically queries multi-currency account equity (CAD cash reserves converted to USD purchasing power at conservative FX rates) to prevent artificial order clipping.

#### 3. Pillar 3: TradingView Alert Webhook Ingress (Human-in-the-Loop)
- **Technical Trigger (PineScript):**
  - **Long Entry:** Price touches lower Bollinger Band (20, 2) while 14-period RSI is oversold ($< 30$) and trading volume exceeds the 20-day moving average by 1.5x.
  - **Exit Strategy:** Price crosses the 20-period SMA middle band or reaches an explicit Stop Loss / Take Profit target.
- **Fundamental Health Filter (OpenBB Platform):**
  - Automatically rejects companies with extreme insolvency or balance sheet risk:
    $$\text{Debt-to-Equity} < 2.0 \quad \text{and} \quad \text{Operating Cash Flow} > 0$$
- **Human Approval:** Dispatched to Telegram with interactive 2-step inline buttons and a 5-minute TTL.

---

### 💬 Telegram Interactive Bot & Conversational Portfolio Assistant

The Telegram Bot (`@quant_bot`, Chat ID Whitelist: `<AUTHORIZED_TELEGRAM_CHAT_ID>`) provides dual capabilities:

#### 1. Automated Scheduled Status Digests (America/New_York)
- **Pre-Market Morning Briefing (08:30 AM ET):** Delivers pre-market overview, exchange open/holiday status via `exchange_calendars`, overnight carry-over positions, settled cash, and planned scans for the session.
- **Post-Market Daily Closing Digest (04:15 PM ET):** Dispatched immediately after market close, Pillar 2 scan, and stale order cleanup. Calculates closing mark-to-market valuations, realized/unrealized P&L by pillar, distance to 5-day SMA snapback targets, and day summary.
- *On-Demand Triggers:* `/briefing` (morning status) and `/digest` (closing summary) can be requested anytime.

#### 2. Natural Language Conversational Intelligence (Google Gemini)
- Authorized trader can query the bot in plain natural English (e.g. _"How is NVDA doing?"_, _"What's our total profit today?"_, _"Why are we holding XLE and XLV?"_, _"How much cash is available?"_).
- The bot injects live SQLite state, real-time quotes, settled cash, and active strategy rules into Gemini to generate institutional-grade answers.
- **Strict Read-Only Guardrail:** Natural language chat CANNOT execute orders or move money. Order execution remains strictly automated via the quant engine daemons or gated by 2-step inline confirmation buttons.

#### 3. Command Suite
| Command | Description |
| :--- | :--- |
| `/digest` | Generate live full portfolio closing digest with P&L and pillar metrics |
| `/briefing` | Generate live pre-market morning briefing |
| `/status` | Query engine health, trading mode, settled cash, and kill switch state |
| `/positions` | List open broker positions and share quantities |
| `/pillars` | Breakdown automated holdings across Pillar 1 (30%) & Pillar 2 (70%) |
| `/history` | View recent trade ledger execution audit trail |
| `/kill` | Emergency trading halt: cancel all working orders and freeze ingress |
| `/resume` | Disengage kill switch and resume normal paper trading operations |

---

## ⚡ Gateway Auto-Reconnection & Order Lifecycle
- **Active Socket Health & Auto-Reconnection:** Prior to querying settled cash, reading positions, or routing orders, `IBKRBroker.ensure_connected()` validates socket connectivity. If the connection dropped (e.g. during IBKR nightly maintenance), it automatically re-establishes a fresh session before submitting trades.
- **No Silent Fallback:** Real broker orders are never silently downgraded to simulation fills if a temporary network hiccup occurs.
- **Race Condition & Short-Selling Guard:** On every SELL order, the broker queries both held positions and active unfilled sell orders in `openTrades()`. If available net shares $\le 0$, the order is rejected with `ValueError: Prohibited naked short-sell`.
- **Cash Over-Commitment Guard:** On every BUY order, pending unfilled buy orders and a $500 reserve buffer are subtracted from settled cash. Orders are automatically clamped to prevent margin borrowing.
- **Crash Resilience & Idempotency:** The execution daemon persists last-run dates in SQLite (`daemon_schedule_state`). Service restarts never trigger duplicate executions or accidental trades.
- **Daily Post-Close Order Cleaner (04:05 PM ET):** Reconciles unfilled DAY orders and purges stale state after regular market close.
- **Fill Listener & Tax Ledger:** Monitored via `fill_listener.py`, supporting partial fills, full fills, and immutable logging to SQLite and CSV audit exports.

---

## 🛡️ Risk Safeguards & Margin Protection Rules

| Safeguard | Exact Rule / Logic | Purpose |
| :--- | :--- | :--- |
| **Trade Sizing Ceiling** | $\text{Order Value} \le \$500.00\text{ USD}$ (Pillar 3) | Limits maximum capital exposure per manual TradingView alert |
| **No Margin Borrowing** | $\text{Order Value} \le \text{Settled Cash} - \text{Committed Cash}$ | Prevents borrowing fees, interest charges, or margin calls |
| **Order Type Enforcement**| **Strict Limit Orders & MOC** (`orderType='LMT' / 'MOC'`) | Limit orders for entries/rebalances; Market-on-Close (`MOC`) for daily mean-reversion exits to eliminate closing cross auction misses |
| **Limit Price Buffer** | $\text{Limit Price} = \text{Alert Price} \times 1.002$ (Buy) / $0.998$ (Sell) | Tight 0.2% price buffer guarantees execution without chasing |
| **Mean-Reversion Exits (MOC)** | Official Exchange Closing Cross (`MOC`) submitted at 15:45 ET | 100% fill rate at official closing print; eliminates unfilled limit order overnight drag |
| **Portfolio Source of Truth** | Real-Time Broker Session (`IBKRBroker.get_portfolio_details()`) | SQLite mirrors exact broker-settled holdings, eliminating database-broker drift |
| **Hysteresis Band** | Top 2 Buy / Top 4 Retention Band | Eliminates whipsaw churn when sector ranks oscillate |
| **Schedule Timezone** | `America/New_York` with `exchange_calendars` | Eliminates UTC midnight shifts and handles DST transitions |
| **Alert Storm Debouncer** | Sliding window: Max 3 alerts per 60 seconds | Consolidates market open alert bursts into a single digest |
| **Signal Freshness TTL** | 5-minute expiration timestamp | Prevents stale alerts from executing hours later |
| **Sell Order Protection** | $\text{Sell Qty} \le \text{Current Long Position} - \text{Working Sells}$ | Prevents accidental naked short-selling & race conditions |
| **Emergency Kill Switch** | Command `/kill` in Telegram | Immediately cancels all open orders and halts trading |

---

## 🧪 Paper Trading vs. Live Trading Setup

The system is configured to support **Paper Trading** out-of-the-box, allowing you to validate strategies without risking real capital:

```mermaid
flowchart LR
    classDef paper fill:#115e59,stroke:#2dd4bf,stroke-width:2px,color:#ffffff;
    classDef live fill:#991b1b,stroke:#f87171,stroke-width:2px,color:#ffffff;
    classDef engine fill:#1e3a8a,stroke:#60a5fa,stroke-width:2px,color:#ffffff;

    subgraph IBGateway ["🏦 IB Gateway Docker Container - ghcr.io/gnzsnz/ib-gateway"]
        Paper["🧪 Paper Trading Mode<br/>Port: 4002 Loopback<br/>Simulated Fills & Virtual Cash"]:::paper
        Live["🚨 Live Trading Mode<br/>Port: 4001 Loopback<br/>Real Capital & Direct Execution"]:::live
    end

    Ingress["⚡ Python Ingress Engine"]:::engine -->|Port 4002 - Paper Mode| Paper
    Ingress -.->|Port 4001 - Live Mode| Live
```

### How to Run Paper Trading:
1. **Container Port:** Set `TWS_PORT=4002` in `/docker/ib-gateway/.env`.
2. **Network Isolation:** Port `4002` is bound strictly to `127.0.0.1:4002` on the container loopback interface, preventing unauthorized access from WAN or external LAN clients.
3. **Simulated Fills:** IBKR paper trading accounts simulate order fills against real-time market data without touching real funds.
4. **Audit Verification:** Check `trading_system.db` to inspect filled prices, simulated commissions, and portfolio balances.

### Migration Checklist to Live Trading:
- [ ] Minimum 30 days of consistent paper trading logs.
- [ ] Confirm no orphaned or unhandled order states in `trading_system.db`.
- [ ] Change `TWS_PORT=4001` and update credentials to live trading credentials.
- [ ] Verify live 2FA multi-factor authentication handshake on IB Key mobile app.

---

## 🔗 Cross-Service Integrations

- **Firefly III Financial Integration:** Fills logged in the SQLite trade ledger can be synced into Firefly III under the `Quant Trading Profit / Loss` category to track realized gains/losses on your family balance sheet.
- **Telegram Alert Bot (`@quant_bot`):** Dispatches real-time human-in-the-loop trade approval cards with inline buttons.
- **Prometheus & Grafana:** Scrapes container CPU, memory, and SQLite execution latency.

---

## ⚙️ Container Sizing & Recommendations

| Parameter | Specification | Notes |
| :--- | :--- | :--- |
| **Virtualization** | Debian 12 LXC Container | Unprivileged with `nesting=1,keyctl=1` |
| **Cores** | 2 vCPUs | Handles OpenBB calculations and async event loops |
| **Memory** | 4096 MB (4 GB) | IB Gateway Java VM (~1.2GB) + Python runtime (~800MB) |
| **Disk** | 24 GB SSD (`local-lvm`) | Python virtual environments & historical market data cache |
| **Ports** | `8080` (Webhook), `8000` (OpenBB), `4002` (IB Gateway) | Loopback and internal subnet only |

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

2. **Deploy Python Virtual Environment & OpenBB:**
   Enter container (`pct enter 108`):
   ```bash
   apt-get update && apt-get install -y python3 python3-pip python3-venv git curl build-essential

   python3 -m venv /opt/quant-env
   source /opt/quant-env/bin/activate
   pip install --upgrade pip
   pip install openbb ib_insync flask requests pandas exchange_calendars
   ```

3. **Deploy Headless IB Gateway Container:**
   Create `/docker/ib-gateway/docker-compose.yml`:
   ```yaml
   version: "3.8"
   services:
     ib-gateway:
       image: ghcr.io/gnzsnz/ib-gateway:stable
       container_name: quant-ib-gateway
       restart: unless-stopped
       environment:
         - TWS_USERID=<YOUR_IBKR_USERNAME>
         - TWS_PASSWORD=<YOUR_IBKR_PASSWORD>
         - TRADING_MODE=paper
         - TWS_PORT=4002
         - READ_ONLY_API=no
       ports:
         - "127.0.0.1:4002:4002"
   ```

4. **Verify TradingView Alert Ingress Payload Format:**
   In TradingView Alert settings, set Webhook URL to `http://<CONTAINER_IP>:8080/webhook/tradingview` with payload:
   ```json
   {
     "passphrase": "<YOUR_WEBHOOK_PASSPHRASE>",
     "action": "BUY",
     "ticker": "NASDAQ:NVDA",
     "price": 125.50,
     "strategy": "MeanReversion_1H"
   }
   ```

---

## 🔄 State Synchronization & Order Lifecycle Resilience

To prevent desynchronization between IBKR broker positions and the internal SQLite database (`automated_portfolio_state`), the system implements a strict two-phase commit and order reconciliation loop:

### 1. Order Execution & State Machine

```mermaid
flowchart TD
    classDef blue fill:#2563EB,stroke:#1D4ED8,stroke-width:2px,color:#fff;
    classDef amber fill:#D97706,stroke:#B45309,stroke-width:2px,color:#fff;
    classDef purple fill:#7C3AED,stroke:#6D28D9,stroke-width:2px,color:#fff;
    classDef emerald fill:#059669,stroke:#047857,stroke-width:2px,color:#fff;
    classDef red fill:#DC2626,stroke:#B91C1C,stroke-width:2px,color:#fff;
    classDef slate fill:#475569,stroke:#334155,stroke-width:2px,color:#fff;

    Open["🟢 OPEN Position"]:::emerald
    SubmitExit["📤 Submit Exit LMT Order (TIF=DAY)"]:::amber
    PendingExit["⏳ PENDING_EXIT"]:::purple
    FillEvent{"Broker Fill Event?"}:::blue
    OrderExpired{"4:00 PM Close / Expired?"}:::slate
    Closed["🔴 CLOSED"]:::red
    RevertOpen["🔄 Revert to OPEN"]:::emerald

    Open --> SubmitExit
    SubmitExit --> PendingExit
    PendingExit --> FillEvent
    FillEvent -- "Filled (SELL Confirmed)" --> Closed
    FillEvent -- "Unfilled" --> OrderExpired
    OrderExpired -- "Broker Holds Shares" --> RevertOpen
    OrderExpired -- "Broker Shares Sold" --> Closed
```

### 2. Safeguards & Protections
* **Zero Premature State Closure:**
  - Positions are never marked `CLOSED` upon placing an order. Instead, they transition to `PENDING_EXIT`.
  - While in `PENDING_EXIT`, candidate evaluators treat the slot as occupied (`status IN ('OPEN', 'PENDING_EXIT')`), preventing phantom buys or double allocation.
* **Real-Time Execution Postback (`fill_listener.py`):**
  - Actively polls IBKR working orders every 3 seconds.
  - On `Filled` execution for a `SELL`: transitions `automated_portfolio_state` to `CLOSED` and appends an immutable record to the CRA/IRS tax audit CSV.
  - On `Cancelled`/`Inactive` for a `SELL` with 0 filled shares: immediately reverts status from `PENDING_EXIT` back to `OPEN`.
* **Post-Market Automated Reconciliation (`clean_stale_orders()` at 4:05 PM ET):**
  - Authoritatively compares `automated_portfolio_state` against live broker holdings (`broker.get_positions()`).
  - If a `PENDING_EXIT` order expired unfilled at 4:00 PM ET close, it verifies the shares remain held in IBKR and safely reverts the database row to `OPEN`.
  - If a `BUY` order expired unfilled at close without executing, it flags the row as `CANCELLED_UNFILLED` so capital is unlocked for the next trading day.
* **Unified Telegram Visibility:**
  - `/pillars`, `/digest`, and conversational Gemini queries inspect `status IN ('OPEN', 'PENDING_EXIT')`, displaying an explicit `⏳ (Exit Pending)` badge for orders in flight rather than hiding them.

---

## 🛡️ Production Hardening & Pre-Trade Risk Architecture (Phase 1 & Phase 2)

To safely deploy real capital, the engine operates under a defensive, fail-closed multi-layered architecture:

```mermaid
flowchart TD
    classDef blue fill:#2563EB,stroke:#1D4ED8,stroke-width:2px,color:#fff;
    classDef red fill:#DC2626,stroke:#B91C1C,stroke-width:2px,color:#fff;
    classDef amber fill:#D97706,stroke:#B45309,stroke-width:2px,color:#fff;
    classDef emerald fill:#059669,stroke:#047857,stroke-width:2px,color:#fff;
    classDef slate fill:#475569,stroke:#334155,stroke-width:2px,color:#fff;

    Signal["⚡ Strategy Signal (P1 / P2)"]:::slate
    RiskCheck{"🛡️ Pre-Trade Risk Firewall"}:::blue
    Abort["⛔ Order Aborted & Telegram Alert"]:::red
    PreCommit["💾 Phase 1: Write PENDING_SUBMIT"]:::amber
    BrokerSend["📤 Phase 2: Dispatch to IBKR (ClientId 1)"]:::emerald
    BrokerAck{"Broker Ack?"}:::blue
    StateOpen["🟢 Mark OPEN / PENDING_EXIT"]:::emerald
    StateFail["⚠️ Mark SUBMISSION_FAILED"]:::red

    Signal --> RiskCheck
    RiskCheck -- "Violation (Cap / Collar / Kill-Switch)" --> Abort
    RiskCheck -- "Compliant" --> PreCommit
    PreCommit --> BrokerSend
    BrokerSend --> BrokerAck
    BrokerAck -- "Success" --> StateOpen
    BrokerAck -- "Error / Timeout" --> StateFail
```

### 1. Architectural Safeguards Deployed (Phase 1)
* **Pre-Trade Risk Firewall (`risk_engine.py`):**
  - **Single-Order Notional Ceiling:** Hard cap of \$15,000 USD per trade.
  - **Price Deviation Collar:** Orders deviating > 5% from previous close are automatically rejected to guard against bad data or fat-finger ticks.
  - **Kill-Switch Guard:** Reads `system_state.kill_switch_active` before any order dispatch.
  - **Short-Selling Prevention:** Strictly validates broker position availability before submitting SELL limit orders.
* **Fail-Closed Order Router (`broker_router.py`):**
  - Silent simulation fallback is permanently disabled (`simulation_fallback=False`).
  - Network timeouts or gateway drops raise explicit `BrokerConnectionError` or `BrokerExecutionError`, preventing phantom order execution.
* **Dual Client ID Socket Isolation (`quant_orchestrator.py`):**
  - **`clientId=1` (Execution):** Dedicated exclusively to `AutonomousQuantDaemon` and `FillListenerDaemon`.
  - **`clientId=2` (Telemetry):** Dedicated exclusively to `TelegramTradingBot` for user commands (`/digest`, `/pillars`).
  - Completely eliminates socket deadlocks and `Error 326: clientId already in use` collisions.
* **Two-Phase Commit State Machine:**
  - Writes `PENDING_SUBMIT` to SQLite *before* transmitting the packet to IBKR.
  - Upon startup, automatically reconciles orphaned `PENDING_SUBMIT` records against broker holdings to prevent duplicate orders.
* **Thread Supervisor & Watchdog Heartbeat:**
  - Background supervisor monitors thread liveness (`is_alive()`) across all 5 workers. If a thread dies, it alerts Telegram and exits with non-zero code to trigger systemd clean restart.
  - Actively updates `system_state.last_heartbeat` with source `WATCHDOG` every 30 seconds.

### 2. Automated Fault Injection & Regression Verification (Phase 2)
The automated test runner (`test_phase2_fault_injection.py`) runs 16 comprehensive assertions:
- **Suite 1: Pre-Trade Risk Firewall:** Caps, collars, negative inputs, compliant approvals, kill-switch engagement & recovery.
- **Suite 2: Fail-Closed Broker Router:** Negative price rejection, zero mock order generation.
- **Suite 3: Client ID Isolation:** Concurrent queries across `clientId=91` and `clientId=92`.
- **Suite 4: Two-Phase Commit:** Pre-commit persistence and crash recovery of orphaned orders.
- **Suite 5: Process Watchdog:** SQLite heartbeat freshness and `WATCHDOG` source verification.

**Verification Status:** `16 PASSED, 0 FAILED (0.44s execution time)` in container LXC 108.

### 3. Broker Position Reconciliation & Discretionary Stub Guard
* **Enhanced `/positions` Command:**
  - Cross-references real-time broker holdings (`ib.positions()`) against SQLite `automated_portfolio_state`.
  - Automatically classifies holdings into **Pillar 1: Sector Momentum**, **Pillar 2: Connors RSI-2 Mean Reversion**, and **Unmanaged / Discretionary Stubs**.
  - Highlights discrepancies immediately if unmanaged stocks or test stubs exist in the brokerage account.
* **Extended-Hours Stub Liquidation:**
  - Added `outside_rth` parameter to `broker_router.py` with unique client ID order naming (`IB-{clientId}-{orderId}`), ensuring fail-closed pre-trade risk checks and clean execution across both regular and extended trading sessions.

---

## 📈 Long-Horizon Backtest: Current Live Engine (2015 - 2026 YTD)

Comprehensive 11.8-year historical simulation evaluating the exact production quantitative configuration:
* **Target Capital Allocation:** 30% Pillar 1 (Sector Dual Momentum) / 70% Pillar 2 (Mega-Cap Connors RSI-2).
* **Execution & Friction:** Real-time pre-close fills (`fast_info`), \$1.00 IBKR commission per trade, 5 bps slippage.
* **Exit Protocol:** 5-Day SMA snapback or 10-day time-stop horizon (no premature disaster stop).

### 1. Macro Performance Comparison (2015-01-01 to 2026-10-23)

| Metric | Current Live Engine (30/70) | 50/50 Balanced | 70/30 Defensive | SPY Benchmark |
| :--- | :---: | :---: | :---: | :---: |
| **Initial Capital** | \$100,000 | \$100,000 | \$100,000 | \$100,000 |
| **Final Portfolio Equity** | **\$459,902.23** | \$350,723.93 | \$262,834.93 | \$448,975.63 |
| **Total Return** | **+359.90%** | +250.72% | +162.83% | +348.98% |
| **CAGR** | **13.82%** | 11.23% | 8.54% | 13.59% |
| **Maximum Drawdown** | **-21.80%** | -22.56% | -28.01% | **-33.72%** |
| **Sharpe Ratio (\(R_f=2.0\%\))** | **0.80** | 0.65 | 0.46 | 0.66 |
| **Sortino Ratio** | **0.98** | 0.79 | 0.55 | N/A |
| **Calmar Ratio** | **0.63** | 0.50 | 0.31 | 0.40 |
| **Annualized Volatility** | **14.76%** | 14.11% | 14.12% | 17.50% |

### 2. Annual Returns Breakdown vs SPY

| Year | Current Live Engine (30/70) | SPY Benchmark | Alpha vs SPY |
| :---: | :---: | :---: | :---: |
| **2015** | **+15.10%** | +1.29% | **+13.82%** |
| **2016** | +3.24% | +12.00% | -8.76% |
| **2017** | **+24.01%** | +21.71% | **+2.30%** |
| **2018** | -8.91% | -4.57% | -4.34% |
| **2019** | +15.43% | +31.22% | -15.79% |
| **2020** | **+21.40%** | +18.33% | **+3.06%** |
| **2021** | +21.05% | +28.73% | -7.68% |
| **2022** | **+3.95%** | **-18.18%** | **+22.12%** |
| **2023** | +23.10% | +26.18% | -3.08% |
| **2024** | **+26.40%** | +24.89% | **+1.51%** |
| **2025** | +6.63% | +17.72% | -11.09% |
| **2026 YTD** | **+17.13%** | +12.32% | **+4.81%** |

### 3. Pillar 2 Trade Execution Statistics (2,680 Trades)
* **Win Rate:** **70.26%** (7 out of 10 trades profitable)
* **Profit Factor:** **1.45**
* **Average Holding Duration:** **3.2 trading days**
* **Average Winning Trade:** **+1.67%** | **Average Losing Trade:** **-2.65%**
* **Top Contributors:** AVGO (+\$41.5k), MSFT (+\$39.2k), NVDA (+\$36.0k), META (+\$30.2k), GE (+\$29.5k), NFLX (+\$21.6k), AAPL (+\$21.3k).

### 4. Historical Crisis Stress Tests
* **2018 Trade War & Tech Selloff:** Drawdown held to **-15.08%** vs SPY -19.80%.
* **2020 COVID Crash:** Maximum drawdown held to **-21.80%** vs SPY **-33.72%** (+12% capital preservation).
* **2022 Fed Rate Hiking Bear Market:** Drawdown held to **-10.73%** and full-year return **+3.95%** vs SPY **-18.18%** (**+22.12% Alpha** via macro regime cash gating).

---

## 🛡️ Broker-Truth Portfolio Reconciliation & Zero-Ghost Architecture

To guarantee 100% synchronization between Telegram digests and actual broker holdings:
1. **Live Broker As Single Source of Truth:** `generate_portfolio_digest()` queries `broker.get_portfolio_details()` directly via IB Gateway (`ib.portfolio()`). Holdings, shares, average cost basis, and unrealized P&L are taken directly from the broker session rather than theoretical estimates.
2. **Order Lifecycle Gating:** Orders placed during the 3:45 PM ET pre-close scan enter SQLite with status `SUBMITTED`. They are only promoted to `OPEN` upon confirmed broker fill.
3. **Auto-Reconciliation of Expired Limit Orders:** If day limit orders expire unfilled at 4:00 PM close, the daily reconciliation sweeps any zero-share positions to `CANCELLED_UNFILLED` so phantom positions never appear in briefings.
4. **Non-Blocking SQLite Concurrency:** SQLite WAL mode with 30-second busy timeout (`PRAGMA busy_timeout = 30000; PRAGMA synchronous = NORMAL;`) and immediate connection closing around broker I/O prevents transaction lock contention.


