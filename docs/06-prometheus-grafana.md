# 📊 06 - Prometheus & Grafana Telemetry (LXC 104)

This blueprint documents deploying **Prometheus** for time-series metrics collection and **Grafana** for real-time visualization and alerting across Proxmox hosts, VMs, and containers.

---

## ⚙️ 1. Container Sizing & Provisioning

- **VM ID:** `104`
- **Hostname:** `monitoring`
- **Operating System:** Debian 12
- **Memory:** `2048 MB`
- **Cores:** `2`
- **Disk:** `20 GB` (for metrics retention)
- **Static IP:** `192.168.1.249/24`

### Provisioning Command:
```bash
pct create 104 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --hostname monitoring \
  --cores 2 \
  --memory 2048 \
  --swap 512 \
  --rootfs local-lvm:20 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.249/24,gw=192.168.1.1 \
  --unprivileged 1 \
  --onboot 1 \
  --start 1
```

---

## 🛠️ 2. Native Package Installation

Enter the container (`pct enter 104`) and install Prometheus and Grafana:

```bash
apt-get update && apt-get install -y prometheus prometheus-node-exporter

# Add Grafana official repository
mkdir -p /etc/apt/keyrings
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | tee /etc/apt/sources.list.d/grafana.list

apt-get update && apt-get install -y grafana
systemctl daemon-reload
systemctl enable --now prometheus grafana-server prometheus-node-exporter
```

---

## ⚙️ 3. Prometheus Scraping Configuration

Edit `/etc/prometheus/prometheus.yml` to scrape your Proxmox host and internal services:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: "node-exporter"
    static_configs:
      - targets: ["localhost:9100"]

  - job_name: "pve-host"
    static_configs:
      - targets: ["<PVE_NODE_IP>:9100"]

  - job_name: "truenas"
    static_configs:
      - targets: ["<TRUENAS_IP>:9100"]
```

Restart Prometheus to apply:
```bash
systemctl restart prometheus
```

---

## 🖥️ 4. Grafana Dashboards Setup

1. Open Grafana in your browser: `http://<CONTAINER_IP>:3000` (Default credentials: `admin` / `admin`).
2. Navigate to **Connections** ➔ **Data Sources** ➔ **Add Data Source** ➔ Select **Prometheus**.
   - URL: `http://localhost:9090` ➔ Click **Save & Test**.
3. Import Community Dashboards:
   - **Node Exporter Full:** Dashboard ID `1860`
   - **Proxmox Cluster:** Dashboard ID `10347`
