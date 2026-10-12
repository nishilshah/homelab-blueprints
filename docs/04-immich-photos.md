# 📸 04 - Immich Photo & Video Cloud (LXC 102)

This blueprint documents deploying **Immich**, a high-performance self-hosted backup solution for photos and videos (Google Photos alternative), inside a dedicated Debian 12 LXC container on Proxmox VE.

---

## ⚙️ 1. Container Sizing & Features

- **VM ID:** `102`
- **Hostname:** `immich-photos`
- **Operating System:** Debian 12 (Bookworm)
- **Cores:** `4`
- **Memory:** `4096 MB` (4 GB, 6 GB recommended during initial library indexing)
- **Root Disk:** `16 GB` on `local-lvm`
- **Network:** `vmbr0` with static IP (e.g. `192.168.1.252/24`)
- **Key Features:** Unprivileged Container, `nesting=1`, keyctl enabled.

### Proxmox Provisioning Command:
```bash
pct create 102 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --hostname immich-photos \
  --cores 4 \
  --memory 4096 \
  --swap 1024 \
  --rootfs local-lvm:16 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.252/24,gw=192.168.1.1 \
  --unprivileged 1 \
  --features nesting=1,keyctl=1 \
  --onboot 1 \
  --start 1
```

---

## 💾 2. Storage & NFS Mounting

Immich stores original photos, thumbnails, and transcoded videos. Mount TrueNAS storage directly into the container:

```bash
# Inside Container (pct enter 102):
apt-get update && apt-get install -y nfs-common

mkdir -p /mnt/photos

cat << 'EOF' >> /etc/fstab
<TRUENAS_IP>:/mnt/tank/data/photos /mnt/photos nfs defaults,timeo=14,intr 0 0
EOF

mount -a
```

---

## 🚀 3. Docker Compose Deployment inside LXC

1. **Install Docker:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
   ```

2. **Download Immich Compose & Env:**
   ```bash
   mkdir -p /opt/immich && cd /opt/immich
   wget -O docker-compose.yml https://github.com/immich-app/immich/releases/latest/download/docker-compose.yml
   wget -O .env https://github.com/immich-app/immich/releases/latest/download/example.env
   ```

3. **Configure Environment:**
   Edit `.env`:
   ```bash
   UPLOAD_LOCATION=/mnt/photos/upload
   DB_DATA_LOCATION=./postgres
   DB_PASSWORD=<STRONG_RANDOM_DB_PASSWORD>
   IMMICH_MACHINE_LEARNING_WORKERS=2
   ```

4. **Start Immich:**
   ```bash
   docker compose up -d
   ```

---

## 📱 4. Access & Mobile App Setup

- **Web UI:** `http://<CONTAINER_IP>:2283`
- **Mobile Apps:** Download Immich on iOS / Android.
  - Server Endpoint: `http://<CONTAINER_IP>:2283` (or your Tailscale domain).
  - Enable Background Sync & Cellular Backup settings according to preference.
