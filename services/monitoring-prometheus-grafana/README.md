# 📊 Observability & Monitoring: Prometheus & Grafana (LXC 105)

[![Prometheus](https://img.shields.io/badge/Prometheus-v2.50+-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)](https://prometheus.io)
[![Grafana](https://img.shields.io/badge/Grafana-v11+-F46800?style=for-the-badge&logo=grafana&logoColor=white)](https://grafana.com)
[![Docker](https://img.shields.io/badge/Docker-cAdvisor-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://github.com/google/cadvisor)
[![Alertmanager](https://img.shields.io/badge/Alerts-Telegram_Webhooks-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://core.telegram.org/bots)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=for-the-badge)](https://www.apache.org/licenses/LICENSE-2.0)

A comprehensive, self-hosted observability, metrics scraping, and automated alerting engine running inside an unprivileged Debian 12 LXC container on Proxmox VE. Collects real-time telemetry from the **Proxmox hypervisor**, **TrueNAS ZFS pools**, **Docker containers**, and **microservices**, routing instant incident alerts to Telegram via n8n.

---

## 🔗 Official Documentation & External Links

- **Prometheus Official Website:** [prometheus.io](https://prometheus.io)
- **Prometheus Documentation:** [prometheus.io/docs](https://prometheus.io/docs)
- **Grafana Official Website:** [grafana.com](https://grafana.com)
- **Grafana Documentation:** [grafana.com/docs/grafana/latest](https://grafana.com/docs/grafana/latest)
- **Grafana Dashboards Library:** [grafana.com/grafana/dashboards](https://grafana.com/grafana/dashboards)
- **Node Exporter:** [github.com/prometheus/node_exporter](https://github.com/prometheus/node_exporter)
- **cAdvisor Container Metrics:** [github.com/google/cadvisor](https://github.com/google/cadvisor)

---

## 🏗️ Telemetry Scraping & Alerting Architecture

```mermaid
flowchart TD
    classDef target fill:#0284c7,stroke:#38bdf8,stroke-width:2px,color:#ffffff;
    classDef prom fill:#b45309,stroke:#fbbf24,stroke-width:2px,color:#ffffff;
    classDef grafana fill:#7c3aed,stroke:#c084fc,stroke-width:2px,color:#ffffff;
    classDef alert fill:#991b1b,stroke:#f87171,stroke-width:2px,color:#ffffff;

    subgraph Targets ["1. Monitored Infrastructure & Exporters"]
        PVE["🖥️ Proxmox VE Hypervisor<br/>Node Exporter (Port 9100)"]:::target
        NAS["🗄️ TrueNAS SCALE Appliance<br/>ZFS Exporter & Metrics (Port 9100)"]:::target
        DockerVM["🐳 VM 100: Media Stack & Docker<br/>cAdvisor & Node Exporter"]:::target
        Trading["📈 LXC 108: Quant Trading Engine<br/>FastAPI /metrics (Port 8000)"]:::target
    end

    subgraph PrometheusCore ["2. Prometheus Monitoring Core (LXC 105 - Port 9090)"]
        ScrapeEngine["⚡ Prometheus Pull Engine<br/>HTTP GET /metrics poller"]:::prom
        TSDB[("💾 Time-Series Database TSDB<br/>30-Day Retention | 15s Interval")]:::prom
        Rules["📏 Alert Rules Engine<br/>Threshold & Duration Evaluators"]:::prom
        
        ScrapeEngine --> TSDB
        TSDB --> Rules
    end

    PVE -->|PromQL Pull| ScrapeEngine
    NAS -->|PromQL Pull| ScrapeEngine
    DockerVM -->|PromQL Pull| ScrapeEngine
    Trading -->|PromQL Pull| ScrapeEngine

    subgraph Visualization ["3. Grafana Visualization (Port 3000)"]
        Dashboards["📊 Live Dashboards<br/>• Proxmox Cluster Overview (ID: 10045)<br/>• ZFS Pool I/O & Health (ID: 15307)<br/>• Docker Container Resource Usage (ID: 14282)"]:::grafana
    end

    TSDB --> Dashboards

    subgraph AlertPipeline ["4. Alert Routing & Notification"]
        AM["🛡️ Alertmanager (Port 9093)<br/>Debouncing & Deduplication"]:::alert
        n8n["⚙️ n8n Automation Engine (LXC 107)<br/>POST /webhook/homelab-agent"]:::alert
        Telegram["📱 Telegram Sysadmin Bot (@homelab_bot)<br/>Instant Priority Cards & Action Buttons"]:::alert
        
        Rules -->|Fire Event| AM
        AM --> n8n
        n8n --> Telegram
    end
```

---

## 🧠 Architectural Deep-Dive & Engineering Decisions

### 1. Pull vs. Push Metrics Model
Prometheus was selected over push-based solutions (like InfluxDB or Graphite) due to its superior reliability in homelab environments:
- **Centralized Polling Control:** Prometheus controls the scraping cadence (15s interval) and connection concurrency, preventing resource-constrained IoT nodes or LXCs from being overwhelmed by uncoordinated push bursts.
- **Instant Outage Detection (`InstanceDown`):** If a container crashes, a VM kernel panics, or a network cable is unplugged, Prometheus notices the missing HTTP response on the very next scrape cycle and fires an immediate alert. Push systems require complex heartbeat timeout logic to detect dead targets.

### 2. Low-Overhead cAdvisor & Node Exporter Deployment
- **Node Exporter:** Installed directly on bare-metal Proxmox and TrueNAS as lightweight Go binaries consuming `< 15MB` RAM. Exposes host CPU states, memory commit limits, network saturation, and disk IO queues.
- **cAdvisor (Container Advisor):** Runs as a lightweight Docker container on VM 100. Inspects the Linux kernel cgroups of running Docker containers to record per-container memory usage, CPU throttling, and network throughput.

### 3. Critical Production Alerting Rules

| Alert Name | Expression / Condition | Duration | Severity | Action Triggered |
| :--- | :--- | :--- | :--- | :--- |
| **`NodeDown`** | `up == 0` | 2 minutes | Critical | Pushes Telegram alert with failing host IP |
| **`HostHighCpuLoad`** | `100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 90` | 15 minutes | Warning | Identifies run-away processes or stuck OCR jobs |
| **`HostOutOfMemory`** | `(node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 < 10` | 5 minutes | Critical | Alerts prior to Linux kernel OOM-killer invocations |
| **`ZfsPoolDegraded`** | `zfs_pool_state{state!="online"} > 0` | 1 minute | Critical | Immediate warning of drive failure or parity corruption |
| **`DiskSpaceLow`** | `(node_filesystem_free_bytes / node_filesystem_size_bytes) * 100 < 15` | 10 minutes | Warning | Prevents ZFS performance degradation (>80% capacity) |

---

## ⚙️ Container Sizing & Storage Recommendations

| Parameter | Specification | Engineering Rationale |
| :--- | :--- | :--- |
| **Virtualization** | Debian 12 LXC Container | Unprivileged container with `nesting=1` |
| **vCPUs** | 2 vCPUs | PromQL query evaluations and dashboard rendering |
| **Memory** | 2048 MB (2 GB) | Prometheus TSDB memory cache + Grafana web application |
| **Disk** | 24 GB SSD (`local-lvm`) | Retains 30 days of metrics at 15-second scrape intervals |
| **Ports** | `9090` (Prometheus), `3000` (Grafana), `9093` (Alertmanager) | Internal LAN and Tailscale access only |

---

## 🚀 Step-by-Step Deployment Guide

### 1. Provision Proxmox LXC Container
Run on the Proxmox VE host CLI:
```bash
pct create 105 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --hostname monitoring-stack \
  --cores 2 \
  --memory 2048 \
  --swap 512 \
  --rootfs local-lvm:24 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.249/24,gw=192.168.1.1 \
  --unprivileged 1 \
  --features nesting=1 \
  --onboot 1 \
  --start 1
```

### 2. Deploy Prometheus & Grafana via Docker Compose
Enter container (`pct enter 105`):
```bash
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh

mkdir -p /docker/monitoring && cd /docker/monitoring

# Copy prometheus.yml from this blueprint
cat << 'EOF' > prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "proxmox-node"
    static_configs:
      - targets: ["192.168.1.250:9100"]

  - job_name: "truenas-scale"
    static_configs:
      - targets: ["192.168.1.139:9100"]

  - job_name: "docker-media-vm"
    static_configs:
      - targets: ["192.168.1.251:9100", "192.168.1.251:8080"]
EOF

# Launch containers
cat << 'EOF' > docker-compose.yml
version: "3.8"
services:
  prometheus:
    image: prom/prometheus:v2.50.1
    container_name: prometheus
    restart: unless-stopped
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./promdata:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:11.0.0
    container_name: grafana
    restart: unless-stopped
    depends_on:
      - prometheus
    volumes:
      - ./grafanadata:/var/lib/grafana
    ports:
      - "3000:3000"
EOF

docker compose up -d
```

### 3. Import Recommended Grafana Dashboards
1. Open `http://192.168.1.249:3000` (default login: `admin` / `admin`).
2. Add Prometheus data source: `http://prometheus:9090`.
3. Go to **Dashboards** ➔ **Import** and enter the following official dashboard IDs:
   - **Node Exporter Full:** `1860` (Comprehensive host hardware telemetry)
   - **Proxmox VE Cluster:** `10045` (CPU, memory, and container status)
   - **Docker Container Metrics (cAdvisor):** `14282`
