# 🎬 Servarr & Jellyfin Automated Media Stack (VM 100)

[![Jellyfin](https://img.shields.io/badge/Jellyfin-10.9+-00A4DC?style=for-the-badge&logo=jellyfin&logoColor=white)](https://jellyfin.org)
[![Docker](https://img.shields.io/badge/Docker_Compose-v2-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![WireGuard](https://img.shields.io/badge/WireGuard-Gluetun_VPN-88171A?style=for-the-badge&logo=wireguard&logoColor=white)](https://github.com/qdm12/gluetun)
[![Intel](https://img.shields.io/badge/Intel_QuickSync-4K_Transcoding-0071C5?style=for-the-badge&logo=intel&logoColor=white)](https://ark.intel.com)
[![Homepage](https://img.shields.io/badge/Homepage-v0.9+-black?style=for-the-badge&logo=homepage&logoColor=white)](https://gethomepage.dev)

A unified, fully automated home theater media and streaming stack hosted in an Ubuntu 24.04 Docker VM on Proxmox VE. Combines **Intel QuickSync 4K hardware transcoding**, zero-copy **atomic hardlinks**, automated request discovery (*Arr suite), and **VPN-isolated BitTorrent/Usenet downloads**.

---

## 🔗 Official Documentation & External Links

| Service | Official Website | Documentation | GitHub Repository |
| :--- | :--- | :--- | :--- |
| **Jellyfin** | [jellyfin.org](https://jellyfin.org) | [jellyfin.org/docs](https://jellyfin.org/docs) | [jellyfin/jellyfin](https://github.com/jellyfin/jellyfin) |
| **Jellyseerr** | [jellyseerr.dev](https://jellyseerr.dev) | [docs.jellyseerr.dev](https://docs.jellyseerr.dev) | [fallenbagel/jellyseerr](https://github.com/fallenbagel/jellyseerr) |
| **Radarr** | [radarr.video](https://radarr.video) | [wiki.servarr.com/radarr](https://wiki.servarr.com/radarr) | [Radarr/Radarr](https://github.com/Radarr/Radarr) |
| **Sonarr** | [sonarr.tv](https://sonarr.tv) | [wiki.servarr.com/sonarr](https://wiki.servarr.com/sonarr) | [Sonarr/Sonarr](https://github.com/Sonarr/Sonarr) |
| **Prowlarr** | [prowlarr.com](https://prowlarr.com) | [wiki.servarr.com/prowlarr](https://wiki.servarr.com/prowlarr) | [Prowlarr/Prowlarr](https://github.com/Prowlarr/Prowlarr) |
| **Gluetun VPN**| — | [github.com/qdm12/gluetun-wiki](https://github.com/qdm12/gluetun-wiki) | [qdm12/gluetun](https://github.com/qdm12/gluetun) |
| **qBittorrent**| [qbittorrent.org](https://www.qbittorrent.org)| [qbittorrent.org/doc](https://www.qbittorrent.org) | [qbittorrent/qBittorrent](https://github.com/qbittorrent/qBittorrent) |
| **Autobrr** | [autobrr.com](https://autobrr.com) | [autobrr.com/introduction](https://autobrr.com/introduction) | [autobrr/autobrr](https://github.com/autobrr/autobrr) |
| **Bazarr** | [bazarr.media](https://www.bazarr.media) | [wiki.bazarr.media](https://wiki.bazarr.media) | [morpheus65535/bazarr](https://github.com/morpheus65535/bazarr) |
| **TRaSH Guides** | [trash-guides.info](https://trash-guides.info) | Hardlinks & Atomic Moves Reference | [TRaSH-Guides](https://github.com/TRaSH-/Guides) |

---

## 🏗️ End-to-End Media Lifecycle & VPN Isolation Architecture

```mermaid
flowchart TD
    classDef client fill:#0284c7,stroke:#38bdf8,stroke-width:2px,color:#ffffff;
    classDef manager fill:#7c3aed,stroke:#c084fc,stroke-width:2px,color:#ffffff;
    classDef vpn fill:#b45309,stroke:#fbbf24,stroke-width:2px,color:#ffffff;
    classDef storage fill:#059669,stroke:#34d399,stroke-width:2px,color:#ffffff;
    classDef playback fill:#dc2626,stroke:#f87171,stroke-width:2px,color:#ffffff;

    subgraph RequestDiscovery ["1. Discovery & User Requests"]
        User["📱 Family Member / Mobile Client"]:::client -->|1-Click Request| JS["🎬 Jellyseerr (Port 5055)<br/>User Discovery Portal"]:::client
        JS -->|New Movie Request| Radarr["🎥 Radarr (Port 7878)<br/>Movie Manager"]:::manager
        JS -->|New TV Series Request| Sonarr["📺 Sonarr (Port 8989)<br/>TV Episode Manager"]:::manager
    end

    subgraph IndexerSync ["2. Indexer Management"]
        Prowlarr["🔍 Prowlarr (Port 9696)<br/>Syncs 50+ Usenet/Torrent Trackers"]:::manager --> Radarr
        Prowlarr --> Sonarr
    end

    subgraph VPNTunnel ["3. Gluetun VPN Shield Container (Isolated Network)"]
        VPN["🛡️ Gluetun WireGuard Client<br/>Mullvad or Proton | Killswitch Active"]:::vpn
        Qbit["📥 qBittorrent (Port 8080)<br/>Routed strictly through VPN tunnel"]:::vpn
        NZB["⚡ NZBGet (Port 6789)<br/>Routed strictly through VPN tunnel"]:::vpn
        
        VPN --- Qbit
        VPN --- NZB
    end

    Radarr -->|Send Torrent Magnet| Qbit
    Sonarr -->|Send Torrent Magnet| Qbit
    Radarr -->|Send NZB File| NZB
    Sonarr -->|Send NZB File| NZB

    subgraph TrueNASStorage ["4. TrueNAS SCALE Storage (/mnt/tank/data)"]
        Incomplete["📂 /data/torrents/incomplete<br/>Active downloading chunks"]:::storage
        Complete["📦 /data/torrents/complete<br/>Seeding source data"]:::storage
        MediaMovies["🎬 /data/media/movies<br/>Atomic Hardlink - 0 copied bytes"]:::storage
        MediaTV["📺 /data/media/tv<br/>Atomic Hardlink - 0 copied bytes"]:::storage
        
        Incomplete --> Complete
        Complete -.->|Instant Hardlink - Same Filesystem| MediaMovies
        Complete -.->|Instant Hardlink - Same Filesystem| MediaTV
    end

    Qbit --> Incomplete

    subgraph PlaybackLayer ["5. Playback & Hardware Transcoding Engine"]
        MediaMovies --> Jellyfin["🍿 Jellyfin 4K Server (Port 8096)<br/>Intel QuickSync Passthrough /dev/dri"]:::playback
        MediaTV --> Jellyfin
        Jellyfin -->|Direct Play / 4K Tone Mapping| Clients["📺 Apple TV 4K / Google TV / iPad"]:::client
    end
```

---

## 🧠 Architectural Deep-Dive & Engineering Decisions

### 1. Atomic Moves & Hardlinks Architecture (TRaSH Guides Standard)
In naive Docker tutorials, users commonly mount separate host paths:
- `/downloads` mapped to `/mnt/downloads`
- `/movies` mapped to `/mnt/movies`

**Why this naive setup is flawed:**
- Docker treats each bind mount as a distinct physical filesystem boundary.
- When a download finishes, Radarr must perform a **full IO copy** across filesystems. A 50GB 4K remux takes minutes to copy, burns double the storage space, and saturates disk bandwidth.

**The Homelab Unified Path Solution:**
- We mount a single root path `/mnt/storage/data` into `/data` across **every single container**.
- Both `/data/torrents/complete` and `/data/media/movies` exist within the same filesystem mount.
- Radarr and Sonarr create an **Instant Hardlink**:
  ```bash
  ln /data/torrents/complete/Movie.mkv /data/media/movies/Movie\ (2026)/Movie.mkv
  ```
- **Performance:** Execution takes **0.001 seconds**, consumes **0 additional disk bytes**, and allows qBittorrent to seed indefinitely while Jellyfin streams the exact same physical blocks on disk.

### 2. The Gluetun VPN Container Shield
- Downloaders (`qBittorrent`, `NZBGet`) are attached directly to Gluetun via `network_mode: "service:gluetun"`.
- The downloader containers have **no virtual network interface of their own**. They share Gluetun's network stack.
- **Fail-Safe Killswitch:** If the WireGuard VPN handshake drops, the kernel interface goes down. Traffic is physically incapable of escaping via the residential ISP gateway, guaranteeing complete privacy and zero IP/DNS leaks.

### 3. Intel QuickSync Hardware Transcoding (QSV)
- Software transcoding of 4K HEVC/H.265 HDR video spikes an 8-core CPU to 100% utilization, causing stuttering and system lockups.
- By passing the Intel iGPU render node (`/dev/dri/renderD128`) from the Proxmox host into VM 100, Jellyfin offloads video decoding and tone mapping to dedicated silicon.
- **Result:** Effortlessly transcodes simultaneous 4K 10-bit HDR streams down to 1080p SDR with **under 8% CPU utilization**.

---

## 🌐 Network Ports Reference

| Port | Service | Access Policy | Description |
| :---: | :--- | :---: | :--- |
| `80` | **Homepage** | Local / Tailscale | Unified homelab dashboard portal |
| `8096` | **Jellyfin** | Local / Tailscale | Media server streaming port |
| `5055` | **Jellyseerr** | Local / Tailscale | 1-Click user request discovery portal |
| `8080` | **qBittorrent** | Isolated (VPN) | WebUI routed strictly through Gluetun WireGuard |
| `6789` | **NZBGet** | Isolated (VPN) | Usenet WebUI routed through Gluetun WireGuard |
| `9696` | **Prowlarr** | Local / Internal | Universal indexer sync manager |
| `7878` | **Radarr** | Local / Internal | Movie management & auto-grabber |
| `8989` | **Sonarr** | Local / Internal | TV episode manager & auto-grabber |
| `8686` | **Lidarr** | Local / Internal | Music collection manager |
| `6767` | **Bazarr** | Local / Internal | Subtitle synchronization daemon |
| `7474` | **Autobrr** | Local / Internal | Real-time IRC announce monitor |

---

## ⚙️ VM Sizing & Storage Recommendations

| Parameter | Specification | Rationale |
| :--- | :--- | :--- |
| **Virtualization** | KVM Virtual Machine (Ubuntu 24.04 LTS) | Enables clean iGPU passthrough and Docker overlay2 stability |
| **vCPUs** | 4 Cores (`host` type) | Background library scans, file indexing, and extraction |
| **Memory** | 8192 MB (8 GB) | qBittorrent RAM cache (1GB) + Jellyfin streaming buffers |
| **Disk** | 40 GB SSD (`local-lvm`) | OS, Docker containers, and Jellyfin metadata/artwork |
| **Storage Mount** | NFSv4 (`/mnt/tank/data`) | Permanent media repository stored on TrueNAS SCALE ZFS pool |

---

## 🚀 Step-by-Step Deployment Guide

### 1. Verify Storage & Hardware Passthrough
On the Ubuntu VM, verify the TrueNAS NFS share is mounted:
```bash
df -h | grep /mnt/storage/data
```
Verify Intel GPU render node visibility:
```bash
ls -la /dev/dri
# Expected output: card0 and renderD128
```

### 2. Configure Environment Secrets
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
nano .env
```
Fill in your VPN parameters:
- `VPN_SERVICE_PROVIDER=mullvad` (or `protonvpn`, `custom`)
- `WIREGUARD_PRIVATE_KEY=<YOUR_PRIVATE_KEY>`
- `WIREGUARD_ADDRESSES=<YOUR_VPN_IP/32>`
- `LAN_NETWORK=192.168.1.0/24`

### 3. Launch Docker Compose Stack
```bash
docker compose up -d
```

### 4. Verify VPN Tunnel Isolation
Confirm your public BitTorrent IP matches the VPN gateway, never your home ISP:
```bash
docker exec -it qbittorrent curl ifconfig.me
```

---

## 🛠️ Operational Maintenance & Health Best Practices

### 1. Download Client Hygiene & Path Mapping
* **Inactive Download Clients:** If Usenet (`nzbget`) is not in use or has no active servers configured, keep it disabled (`enable: false`) in **Sonarr** and **Radarr** Settings > Download Clients. This eliminates false-positive `RemotePathMappingCheck` warnings regarding unmapped completed directories.
* **VPN Service Dependency:** All torrent/download traffic strictly routes through the `gluetun` network container. If Gluetun restarts, child containers automatically pause traffic via Docker network namespace binding.

### 2. Ghost Queue Reconciliation & Unpackerr Loop Prevention
* **Stuck Downloads:** If a movie or episode is grabbed but blocked on manual import (e.g. `importBlocked`), **Unpackerr** checks the queue every 60 seconds and logs continuous extraction errors if the file is missing from `/data/downloads/qbittorrent/completed`.
* **Remediation:** Remove stuck queue entries via the *Arr WebUI or REST API with `removeFromClient=true` to instantly release the torrent client and clear Unpackerr/qbit-manage error loops.

### 3. NFS Atomic Hardlinks
* Always map `/data` as a single shared mount volume across all Servarr containers to enable zero-copy atomic hardlinks on TrueNAS SCALE datasets, preserving download seeding while instantly indexing files in Jellyfin without doubling disk consumption.
