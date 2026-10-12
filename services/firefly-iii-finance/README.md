# 💰 Firefly III Family Wealth & Budgeting Engine (LXC 109)

[![Firefly III](https://img.shields.io/badge/Firefly_III-v6.1+-blue?style=for-the-badge&logo=fireflyiii&logoColor=white)](https://firefly-iii.org)
[![MariaDB](https://img.shields.io/badge/MariaDB-11-brown?style=for-the-badge&logo=mariadb&logoColor=white)](https://mariadb.org)
[![License: AGPLv3](https://img.shields.io/badge/License-AGPL_v3-blue.svg?style=for-the-badge)](https://www.gnu.org/licenses/agpl-3.0)

A secure, self-hosted, double-entry financial management engine running in an unprivileged Debian 12 LXC container. Manages multi-currency banking (CAD, INR, USD), automated spending categorization rules, real estate asset valuations, and loan amortizations.

---

## 🔗 Official Documentation & External Links

- **Official Website:** [firefly-iii.org](https://www.firefly-iii.org)
- **Documentation:** [docs.firefly-iii.org](https://docs.firefly-iii.org)
- **API Documentation:** [api-docs.firefly-iii.org](https://api-docs.firefly-iii.org)
- **GitHub Repository:** [firefly-iii/firefly-iii](https://github.com/firefly-iii/firefly-iii)
- **Data Importer:** [docs.firefly-iii.org/data-importer](https://docs.firefly-iii.org/data-importer)
- **Community Forum:** [reddit.com/r/FireflyIII](https://reddit.com/r/FireflyIII)

---

## 🏗️ Financial Flow & Multi-Currency Architecture

```mermaid
flowchart LR
    subgraph Inputs ["Inbound Transactions"]
        BankAlerts["Banking Alerts (Email)"] --> n8n["n8n Automation Engine"]
        Interac["Interac e-Transfers (Email)"] --> n8n
        Telegram["@salary_bot (Natural Language)"] --> REST
        RentInflow["Tenant Rents (UPI / Interac)"] --> REST
        n8n -->|REST API (Bearer Token)| REST["Firefly III REST API (Port 80)"]
    end

    subgraph FireflyEngine ["Core Accounting Engine"]
        REST --> Rules["Rule Engine & Auto-Categorization"]
        Rules --> Ledger["Double-Entry Transaction Ledger"]
        Ledger --> Budgets["7 Monthly Spending Budgets"]
    end

    subgraph Currencies ["Multi-Currency Balance Sheet"]
        Ledger --> CAD["Canadian Dollar (CAD)<br/>Chequing, Credit Card, Mortgages"]
        Ledger --> INR["Indian Rupee (INR)<br/>Pune Real Estate, HDFC Loan & Savings"]
        Ledger --> USD["US Dollar (USD)<br/>Stock Portfolios & Equities"]
    end
```

---

## ⚙️ Container Sizing & Recommendations

| Parameter | Specification | Notes |
| :--- | :--- | :--- |
| **Virtualization** | Debian 12 LXC Container | Unprivileged with `nesting=1` |
| **Cores** | 2 vCPUs | Standard web application workloads |
| **Memory** | 2048 MB (2 GB) | MariaDB + PHP-FPM core engine |
| **Disk** | 16 GB SSD (`local-lvm`) | Database tables and document uploads |
| **Network** | `vmbr0` (Static IP) | Port 80 exposed internally |

---

## 🚀 Step-by-Step Deployment

1. **Provision Container:**
   ```bash
   pct create 109 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
     --hostname firefly-iii \
     --cores 2 \
     --memory 2048 \
     --swap 512 \
     --rootfs local-lvm:16 \
     --net0 name=eth0,bridge=vmbr0,ip=192.168.1.245/24,gw=192.168.1.1 \
     --unprivileged 1 \
     --features nesting=1 \
     --onboot 1 \
     --start 1
   ```

2. **Deploy Docker Stack:**
   Enter container (`pct enter 109`):
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh

   mkdir -p /docker/firefly && cd /docker/firefly
   # Copy docker-compose.yml and .env.example from this blueprint
   cp .env.example .env
   
   # Generate 32-character base64 encryption key
   APP_KEY=$(head /dev/urandom | head -c 32 | base64)
   sed -i "s|<RANDOM_BASE64_32_CHAR_KEY>|$APP_KEY|" .env

   docker compose up -d
   ```

3. **Complete Onboarding:**
   Navigate to `http://192.168.1.245` in your browser to create the primary administrative login.

4. **Generate Personal Access Token:**
   Go to **Profile** ➔ **OAuth** ➔ **Personal Access Tokens** ➔ **Create Token** for automation.
