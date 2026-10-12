# 🎬 03 - Servarr & Jellyfin Media Stack (VM 100)

This blueprint documents deploying the complete automated home theater media and streaming stack inside an Ubuntu 24.04 Docker VM, featuring **Intel QuickSync 4K hardware transcoding** and a **WireGuard VPN download shield**.

---

## ⚙️ 1. VM Sizing & Provisioning

- **VM ID:** `100`
- **Hostname:** `servarr-docker`
- **Operating System:** Ubuntu Server 24.04 LTS (Minimal)
- **vCPUs:** `4` (Type: `host`)
- **Memory:** `8192 MB` (8 GB)
- **Disk:** `32 GB` on `local-lvm`
- **Network:** `vmbr0` with static IP (e.g. `192.168.1.251/24`)
- **PCI Passthrough:** Intel UHD Graphics (`00:02.0`) passed through to the VM via Proxmox GUI or QEMU CLI.

---

## 🛠️ 2. Host Storage Mounts (NFS Client Setup)

Before starting Docker, mount TrueNAS ZFS datasets on the Ubuntu VM:

```bash
# Install NFS client
sudo apt update && sudo apt install -y nfs-common

# Create mount points
sudo mkdir -p /mnt/storage/data

# Add to /etc/fstab for auto-mount on boot
cat << 'EOF' | sudo tee -a /etc/fstab
<TRUENAS_IP>:/mnt/tank/data /mnt/storage/data nfs defaults,timeo=14,intr 0 0
EOF

sudo mount -a
ls -la /mnt/storage/data
```

---

## 🚀 3. Docker Deployment

1. **Install Docker Engine & Compose plugin:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

2. **Clone / Place Blueprints:**
   ```bash
   mkdir -p /docker/servarr && cd /docker/servarr
   cp <PATH_TO_TEMPLATES>/docker-compose.servarr.yml ./docker-compose.yml
   cp <PATH_TO_TEMPLATES>/.env.example ./.env
   ```

3. **Configure Environment:**
   Edit `.env` to set your VPN WireGuard credentials and subnet:
   ```bash
   nano .env
   ```

4. **Verify Intel QuickSync Permissions:**
   Ensure your user and docker have access to `/dev/dri`:
   ```bash
   sudo usermod -aG render,video $USER
   ls -la /dev/dri
   ```

5. **Start the Stack:**
   ```bash
   docker compose up -d
   ```

---

## 🌐 4. Service Access & Port Reference

| Service | Port | Description |
| :--- | :---: | :--- |
| **Homepage Portal** | `80` | Unified family dashboard with live service widgets |
| **Jellyfin** | `8096` | 4K media server & mobile/TV apps |
| **Jellyseerr** | `5055` | 1-click movie & TV show request portal |
| **qBittorrent** | `8080` | Torrent client (isolated inside Gluetun VPN) |
| **Prowlarr** | `9696` | Universal indexer sync manager |
| **Radarr** | `7878` | Movie monitoring & quality upgrade automation |
| **Sonarr** | `8989` | TV show episode monitoring & release grabber |
| **Lidarr** | `8686` | Music collection manager |
| **Bazarr** | `6767` | Subtitle downloader (OpenSubtitles, etc.) |
| **Autobrr** | `7474` | Real-time IRC announce monitor |
| **NZBGet** | `6789` | Usenet downloader (isolated inside Gluetun VPN) |

---

## 🔍 5. Verification & Health Check

Test that your download traffic is successfully passing through the VPN:

```bash
docker exec -it qbittorrent curl ifconfig.me
```
*The IP output must match your VPN provider's exit node, NOT your home residential ISP IP.*
