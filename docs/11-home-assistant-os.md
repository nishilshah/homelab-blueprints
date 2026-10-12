# 🏠 11 - Home Assistant Smart Home OS (VM 105)

This blueprint documents deploying **Home Assistant Operating System (HAOS)** as a dedicated virtual machine on Proxmox VE, acting as the local automation hub for smart home devices, sensors, and wall-mounted tablet kiosks.

---

## ⚙️ 1. VM Sizing & Provisioning

- **VM ID:** `105`
- **Hostname:** `homeassistant`
- **Memory:** `4096 MB` (4 GB)
- **vCPUs:** `2` (Type: `host`)
- **Disk:** `32 GB` on `local-lvm`
- **BIOS:** `OVMF (UEFI)`
- **Network:** `vmbr0` with static IP (e.g. `192.168.1.72/24`)

---

## 🚀 2. One-Line Proxmox Installation

On the Proxmox VE Host (as `root` via SSH):

```bash
# Download official HAOS qcow2 image
wget -qO- https://github.com/home-assistant/operating-system/releases/latest/download/haos_ova-13.1.qcow2.xz | xz -d > /var/lib/vz/template/iso/haos.qcow2

# Create VM
qm create 105 \
  --name homeassistant \
  --memory 4096 \
  --cores 2 \
  --cpu host \
  --bios ovmf \
  --efidisk0 local-lvm:0,efitype=4m,pre-enrolled-keys=1 \
  --net0 virtio,bridge=vmbr0 \
  --scsihw virtio-scsi-single \
  --scsi0 local-lvm:0,import-from=/var/lib/vz/template/iso/haos.qcow2,discard=on,ssd=1 \
  --boot order=scsi0 \
  --onboot 1

# Resize disk to 32GB
qm resize 105 scsi0 +26G

# Start VM
qm start 105
```

---

## 📱 3. Tablet Kiosk & Wall Display Integration

Home Assistant natively supports dedicated dashboard views tailored for tablets (e.g. iPad mounted on the refrigerator, nanny tablet, hallway touch displays):

1. **Dedicated User Profiles:**
   - Create separate restricted user accounts (e.g. `nanny` / `kiosk`) with access limited to specific dashboards.
2. **Kiosk Mode Add-on / Lovelace Configuration:**
   - Install **Kiosk Mode** via HACS to hide top navigation bars and side menus for pure full-screen interfaces.
3. **Common Widgets:**
   - Baby care logs (feeding timers, naps, diapers synced with Baby Buddy).
   - Real-time weather, family calendar, and security camera live streams.
   - Quick toggles for kitchen lighting, thermostat, and front door locks.
