# 🌐 00 - Homelab Architecture & Network Design

This document establishes the hardware foundation, subnet design, virtualization strategy, and storage topology for the homelab.

---

## 🖥️ 1. Hardware Specification Baseline

- **Compute:** Intel Core i7 / Xeon (6+ Cores / 12+ Threads recommended) with Intel UHD Graphics for QuickSync 4K hardware transcoding.
- **Memory:** 64 GB DDR4/DDR5 ECC or Non-ECC RAM.
- **Boot Storage:** Dual NVMe SSDs in ZFS Mirror (Raid 1) for Proxmox OS (`rpool`) and fast container rootfs (`local-lvm`).
- **Bulk Storage:** SAS/SATA HDDs (e.g. 2x 8TB or 4x 4TB) passed through directly to TrueNAS SCALE via an IT-mode HBA (Host Bus Adapter) or VirtIO SCSI disks.
- **Networking:** Dual Gigabit or 2.5GbE / 10GbE NICs with LACP bonding or dedicated management interface.

---

## 🖧 2. Subnet Design & IP Allocation Strategy

Using a standard private subnet (`192.168.1.0/24` or user-defined CIDR) with static DHCP leases reserved for homelab hosts:

| IP Address Range | Role / Assignment | Notes |
| :--- | :--- | :--- |
| `192.168.1.1` | Default Gateway / Router | OPNsense, pfSense, or UniFi Dream Machine |
| `192.168.1.2 - .49` | Network Infrastructure | Managed switches, wireless access points, PDUs |
| `192.168.1.50 - .99` | IoT & Smart Devices | Home Assistant targets, smart displays, sensors |
| `192.168.1.100 - .199` | DHCP Client Pool | Laptops, mobile devices, guest devices |
| `192.168.1.200 - .254` | **Static Homelab Services** | PVE Host, TrueNAS, LXC Containers, Docker VMs |

### Recommended Static IP Mapping:
| Service ID | Service Name | Default IP | Type | Virtualization |
| :---: | :--- | :---: | :---: | :---: |
| **PVE** | Proxmox VE Hypervisor | `192.168.1.250` | Host | Bare-Metal |
| **VM 100** | Servarr Media Stack | `192.168.1.251` | VM | Ubuntu Server 24.04 (Docker) |
| **VM 101** | TrueNAS SCALE ZFS | `192.168.1.139` | VM | TrueNAS SCALE Appliance |
| **LXC 102** | Immich Photo Cloud | `192.168.1.252` | LXC | Debian 12 (Nesting enabled) |
| **LXC 103** | Tailscale Subnet Gateway | `192.168.1.253` | LXC | Debian 12 (TUN enabled) |
| **LXC 104** | Prometheus & Grafana | `192.168.1.249` | LXC | Debian 12 |
| **VM 105** | Home Assistant OS | `192.168.1.72` | VM | HAOS Appliance |
| **LXC 106** | Paperless-ngx OCR | `192.168.1.246` | LXC | Debian 12 (NFS mounted) |
| **LXC 107** | n8n Automation Engine | `192.168.1.247` | LXC | Debian 12 |
| **LXC 108** | Quant Trading & Research | `192.168.1.248` | LXC | Debian 12 |
| **LXC 109** | Firefly III Wealth System | `192.168.1.245` | LXC | Debian 12 |

---

## 💾 3. Storage Hierarchy & Dataset Topology

All mass data is consolidated in TrueNAS SCALE on a ZFS pool named `tank`:

```text
tank/
├── data/
│   ├── media/
│   │   ├── movies/       (Managed by Radarr)
│   │   ├── tv/           (Managed by Sonarr)
│   │   ├── music/        (Managed by Lidarr)
│   │   └── books/        (Managed by Audiobookshelf)
│   ├── downloads/
│   │   ├── complete/     (qBittorrent / NZBGet finished files)
│   │   └── incomplete/   (Active downloading chunks)
│   └── photos/           (Immich primary / external library)
└── paperless/
    ├── media/            (Paperless-ngx permanent archived documents)
    ├── data/             (Search index and thumbnails)
    └── consume/          (Drop folder for scanner / email ingestion)
```

### Protocol Access Matrix:
- **NFSv4:** Used for high-performance Linux-to-Linux container mounts (e.g. Paperless-ngx, Immich, Docker).
- **SMB / CIFS:** Used for desktop network drives, mobile scanner uploads, and Windows clients.
