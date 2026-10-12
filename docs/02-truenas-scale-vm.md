# 🗄️ 02 - TrueNAS SCALE Storage Foundation

This blueprint documents deploying **TrueNAS SCALE** as a dedicated Virtual Machine (VM 101) on Proxmox VE, acting as the primary ZFS storage foundation for all media, photos, backups, and paperless documents.

---

## ⚙️ 1. VM Sizing & Provisioning

- **VM ID:** `101`
- **Hostname:** `truenas-scale`
- **Memory:** `16384 MB` (16 GB minimum recommended for ZFS ARC cache)
- **vCPUs:** `4` (Host type recommended)
- **OS Disk:** `32 GB` (VirtIO SCSI on `local-lvm`)
- **Data Disks:** SAS/SATA drives passed through directly via PCIe HBA or VirtIO SCSI disks (`/dev/disk/by-id/...`).

### CLI Creation on Proxmox VE:
```bash
qm create 101 \
  --name truenas-scale \
  --memory 16384 \
  --cores 4 \
  --cpu host \
  --net0 virtio,bridge=vmbr0,firewall=0 \
  --scsihw virtio-scsi-single \
  --scsi0 local-lvm:32,discard=on,ssd=1 \
  --ostype l26 \
  --bios ovmf \
  --onboot 1
```

*Note: Attach TrueNAS SCALE ISO to CD-ROM and complete the standard installation.*

---

## 🏊 2. ZFS Pool & Dataset Layout

Inside TrueNAS Web UI (`http://<TRUENAS_IP>`):

1. **Storage Pool:** `tank`
   - Topology: Mirror (2 drives) or RAID-Z2 (4+ drives).
   - Compression: `lz4` (or `zstd`).
   - Atime: `off` (improves read IOPS).

2. **Create Datasets:**
   - `tank/data` (General data & media)
   - `tank/data/media` (Movies, TV shows, Music)
   - `tank/data/downloads` (Torrent & Usenet downloads)
   - `tank/paperless` (Archived searchable documents)
   - `tank/paperless/consume` (Ingestion folder)
   - `tank/backups` (Cluster snapshots & database dumps)

---

## 📡 3. Network Share Configuration

### A. NFS Exports (For Linux Containers & Docker)
Go to **Shares** ➔ **Unix (NFS) Shares** ➔ **Add**:
- **Paths:** `/mnt/tank/data`, `/mnt/tank/paperless`
- **Maproot User:** `root`
- **Maproot Group:** `root`
- **Allowed Networks:** `<YOUR_HOMELAB_SUBNET_CIDR>` (e.g. `192.168.1.0/24`)

### B. SMB / CIFS Shares (For Windows & Mobile Scanners)
Go to **Shares** ➔ **Windows (SMB) Shares** ➔ **Add**:
- **Path:** `/mnt/tank/paperless/consume`
- **Share Name:** `consume`
- **Purpose:** Multi-protocol file sharing for mobile document scanners (e.g. Genius Scan, ScanSnap).

---

## 🔒 4. Maintenance & Automated Snapshots

1. **Periodic Snapshot Tasks:**
   - Dataset: `tank/paperless` ➔ Frequency: Daily at midnight ➔ Keep: 30 days.
   - Dataset: `tank/data/media` ➔ Frequency: Weekly ➔ Keep: 8 weeks.
2. **SMART Tests & Scrubbing:**
   - ZFS Scrub schedule: Twice monthly.
   - S.M.A.R.T. Long Test: Once monthly.
