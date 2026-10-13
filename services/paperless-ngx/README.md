# 📄 Paperless-ngx Document Archive & OCR Engine (LXC 106)

[![Paperless-ngx](https://img.shields.io/badge/Paperless--ngx-v2.12+-008559?style=for-the-badge&logo=googledocs&logoColor=white)](https://docs.paperless-ngx.com)
[![Docker](https://img.shields.io/badge/Docker-PostgreSQL_16-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7_Alpine-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![TrueNAS](https://img.shields.io/badge/TrueNAS-ZFS_Mirror-0071C5?style=for-the-badge&logo=truenas&logoColor=white)](https://www.truenas.com)
[![License: GPLv3](https://img.shields.io/badge/License-GPL_v3-blue.svg?style=for-the-badge)](https://www.gnu.org/licenses/gpl-3.0)

An intelligent, self-hosted electronic document management and OCR indexing system running inside an unprivileged Debian 12 LXC container on Proxmox VE. Transforms physical receipts, utility statements, tax forms, and medical records into searchable digital archives with automatic machine-learning classification and cross-service automation.

---

## 🔗 Official Documentation & External Links

- **Official Website:** [docs.paperless-ngx.com](https://docs.paperless-ngx.com)
- **Documentation Hub:** [docs.paperless-ngx.com/setup](https://docs.paperless-ngx.com/setup)
- **GitHub Repository:** [paperless-ngx/paperless-ngx](https://github.com/paperless-ngx/paperless-ngx)
- **REST API Guide:** [docs.paperless-ngx.com/api](https://docs.paperless-ngx.com/api)
- **Configuration Reference:** [docs.paperless-ngx.com/configuration](https://docs.paperless-ngx.com/configuration)
- **Subreddit:** [reddit.com/r/PaperlessNGX](https://reddit.com/r/PaperlessNGX)

---

## 🏗️ End-to-End Ingestion & Processing Architecture

The document management pipeline unifies physical scanning, email polling, OCR extraction, full-text indexing, and automated accounting linkage:

```mermaid
flowchart TD
    classDef source fill:#0284c7,stroke:#38bdf8,stroke-width:2px,color:#ffffff;
    classDef n8n fill:#7c3aed,stroke:#c084fc,stroke-width:2px,color:#ffffff;
    classDef storage fill:#059669,stroke:#34d399,stroke-width:2px,color:#ffffff;
    classDef core fill:#b45309,stroke:#fbbf24,stroke-width:2px,color:#ffffff;
    classDef db fill:#312e81,stroke:#818cf8,stroke-width:2px,color:#ffffff;
    classDef link fill:#0f766e,stroke:#2dd4bf,stroke-width:2px,color:#ffffff;

    subgraph CaptureLayer ["1. Ingestion Sources"]
        Scanner["📱 Mobile Scanner - QuickScan / Genius<br/>Network Multi-Function Printer"]:::source
        Email["📧 Automated Email Ingestion<br/>Bank Statements, Utility Bills, Tax Slips"]:::source
    end

    subgraph n8nLayer ["2. Orchestration & Pre-Processing (n8n Engine)"]
        IMAP["📨 n8n IMAP Poller Daemon"]:::n8n
        Decrypt["🔓 Password Decryption Routine<br/>Removes protection from bank PDFs"]:::n8n
        PreTag["🏷️ Metadata Extractor & Regex Matcher<br/>Extracts Vendor, Date, Amount"]:::n8n
        
        Email --> IMAP
        IMAP --> Decrypt
        Decrypt --> PreTag
    end

    subgraph StorageLayer ["3. TrueNAS SCALE Storage (ZFS Pool: tank)"]
        SMB["📁 Samba Share SMB: /paperless/consume<br/>Drop folder for mobile apps"]:::storage
        NFS_Data["🗄️ NFSv4: /paperless/data<br/>Search indices & app state"]:::storage
        NFS_Media["📦 NFSv4: /paperless/media<br/>Immutable PDF/A archive & originals"]:::storage
        ZFS_Snap["🛡️ ZFS Hourly Snapshots (7-day retention)<br/>Ransomware & Bit-Rot Protection"]:::storage
        
        NFS_Media --- ZFS_Snap
    end

    subgraph PaperlessCore ["4. Paperless-ngx Processing Core (LXC 106)"]
        WebAPI["🌐 Paperless Web API & UI (Port 8000)"]:::core
        Inotify["👀 Inotify Directory Watcher<br/>Detects new files instantly in /consume"]:::core
        RedisQ["⚡ Redis 7 Task Broker<br/>Decouples ingestion from OCR workers"]:::core
        WorkerPool["⚙️ Celery Worker Pool (Tesseract 5 OCR)<br/>Languages: ENG, FRA | Mode: Redo/Skip"]:::core
        Whoosh["🔍 Whoosh Full-Text Inverted Index<br/>Sub-second token search"]:::db
        Postgres[("💾 PostgreSQL 16 Database<br/>Document metadata, tags, fields")]:::db
        ML["🧠 Bayes & Neural Text Classifier<br/>Predicts Document Type, Tags, Correspondent"]:::core
        
        Inotify --> RedisQ
        WebAPI --> RedisQ
        RedisQ --> WorkerPool
        WorkerPool --> Whoosh
        WorkerPool --> Postgres
        WorkerPool --> ML
    end

    subgraph CrossLinkage ["5. Cross-Service Ecosystem Integration"]
        Firefly["💰 Firefly III Finance Engine (LXC 109)<br/>Attach Paperless Document URL to ledger entry"]:::link
        TG["🔔 Telegram Notification Bot<br/>Pushes OCR summary card with thumbnail preview"]:::link
    end

    Scanner -->|Direct SMB Save| SMB
    SMB --> Inotify
    PreTag -->|REST API POST| WebAPI
    WorkerPool -->|Store Final PDF/A| NFS_Media
    Postgres -.->|Webhook Sync| Firefly
    WorkerPool -.->|Complete Event| TG
```

---

## 🧠 OCR, Classification & Indexing Mechanics

### 1. OCR Engine & Archival Standards (Tesseract 5 + Ghostscript)
- **PDF/A Archival Conversion:** Every ingested document is rasterized and compiled into **ISO 19005-1 compliant PDF/A-2b** format. This embeds fonts, color profiles, and metadata permanently, ensuring readability 20+ years in the future regardless of operating system software changes.
- **Sidecar OCR Text Layer:** Tesseract performs Optical Character Recognition, generating an invisible UTF-8 text layer superimposed directly over the original document bitmap. Search highlights land exactly on the scanned word coordinates.
- **Multi-Language Dictionaries:** Container bundles both `tessdata-fast` and `tessdata-best` for English (`eng`) and French (`fra`), accommodating bilingual Canadian tax and utility documents.

### 2. Machine Learning Auto-Tagger (Naive Bayes / Neural Classifier)
Paperless-ngx trains an internal classification model each time a document is tagged:
- **Feature Extraction:** Tokenizes document plain text using TF-IDF (Term Frequency-Inverse Document Frequency).
- **Inference:** When a new document arrives, the classifier calculates conditional probabilities:
  $$P(\text{Tag}_k \mid \text{Document Text}) \propto P(\text{Tag}_k) \prod_{i=1}^n P(w_i \mid \text{Tag}_k)$$
- **Automatic Matching:** Matches correspondents (e.g. *BC Hydro*, *Scotiabank*, *CRA*), document types (*Invoice*, *Tax Return*, *Receipt*), and storage paths (*Finance/2026*) once training confidence exceeds 75%.

### 3. Asynchronous Worker Architecture
- Heavy OCR rasterization can spike CPU and memory consumption. By offloading tasks to **Redis 7**, HTTP web requests remain completely responsive.
- The web server container never blocks on a 60-page PDF document; work is pulled by Celery workers bounded by `PAPERLESS_TASK_WORKERS` to protect the Proxmox host.

---

## 🔗 Cross-Service Integrations & Decision Rationale

### Why not use Paperless-ngx's built-in email poller?
While Paperless has a native IMAP poller, it has critical real-world limitations:
1. Cannot handle password-protected statements (many Canadian banks encrypt e-statements with birthdates or account numbers).
2. Cannot perform dynamic multi-condition routing or regex manipulation prior to consumption.
3. Cannot trigger cross-service webhooks (like creating an expense entry in Firefly III simultaneously).

### 1. n8n Automated Ingestion Pipeline
We route all incoming document emails through **n8n (LXC 107)**:
- **Email Ingestion:** n8n polls an inbox dedicated to bills and e-statements over TLS IMAP every 15 minutes.
- **Attachment Filter:** Evaluates MIME types (`application/pdf`, `image/png`, `image/jpeg`).
- **Decryption Worker:** For password-protected statements, an n8n code node passes the file through `qpdf` with a pre-configured passphrase vault to strip the encryption layer.
- **REST API Injection:** Pushes the unencrypted file into Paperless-ngx via REST API:
  ```http
  POST http://192.168.1.246:8000/api/documents/post_document/
  Authorization: Token <YOUR_PAPERLESS_API_TOKEN>
  Content-Type: multipart/form-data

  document=@statement.pdf
  title="Scotiabank Statement - October 2026"
  correspondent=2
  document_type=1
  tags=[4, 7]
  ```

### 2. Linking Documents to Firefly III
- When a utility bill or invoice is ingested, n8n extracts the total dollar amount and transaction date.
- n8n searches Firefly III for matching withdrawal transactions.
- Upon finding the match, it writes a custom link attribute: `Paperless URL: http://192.168.1.246:8000/documents/<ID>/details`, giving you one-click invoice verification directly from your family balance sheet.

### 3. TrueNAS ZFS Storage Layout
- Storage is mounted inside LXC 106 via high-performance NFSv4 from TrueNAS SCALE.
- **ZFS Dataset Optimization:**
  | Dataset | ZFS Recordsize | Compression | Atime | Rationale |
  | :--- | :--- | :--- | :--- | :--- |
  | `/mnt/tank/paperless/data` | `128K` | `zstd` | `off` | Search indices, SQLite metadata, thumbnail cache |
  | `/mnt/tank/paperless/media` | `128K` | `zstd` | `off` | Archived PDF/A documents (typically 50KB - 5MB) |
  | `/mnt/tank/paperless/consume` | `128K` | `lz4` | `off` | Fast ingestion drop folder |
- **Disaster Recovery:** TrueNAS takes hourly local snapshots of `/mnt/tank/paperless` with a 14-day retention window, completely immunizing the document repository against accidental deletions or ransomware.

---

## ⚙️ Container Sizing & Tuning Guidelines

| Parameter | Recommended | Minimum | Production Rationale |
| :--- | :--- | :--- | :--- |
| **Virtualization** | Unprivileged LXC | LXC | Minimal overhead, kernel isolation, instant backups |
| **vCPUs** | 4 Cores | 2 Cores | Tesseract OCR is CPU-bound; 4 cores speeds up multi-page scans 3.5x |
| **Memory** | 4096 MB (4 GB) | 2048 MB | OCR page rasterization requires memory buffers; prevents OOM crashes |
| **Swap** | 1024 MB | 512 MB | Emergency cushion during massive 100+ page batch ingestions |
| **Root Disk** | 20 GB SSD (`local-lvm`) | 12 GB | OS base, Python dependencies, and Whoosh temporary scratch space |
| **Data Storage** | NFSv4 to TrueNAS | Local Disk | Keeps document binaries out of VM backups; leverages ZFS snapshots |

---

## 🚀 Step-by-Step Deployment Guide

### 1. Provision Proxmox LXC Container
Run on the Proxmox VE host CLI:
```bash
pct create 106 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --hostname paperless-ngx \
  --cores 4 \
  --memory 4096 \
  --swap 1024 \
  --rootfs local-lvm:20 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.246/24,gw=192.168.1.1 \
  --unprivileged 1 \
  --features nesting=1 \
  --onboot 1 \
  --start 1
```

### 2. Configure TrueNAS NFS Mounts
Enter the container (`pct enter 106`):
```bash
apt-get update && apt-get install -y nfs-common curl wget git

# Create mount points
mkdir -p /mnt/paperless/data \
         /mnt/paperless/media \
         /mnt/paperless/consume \
         /mnt/paperless/export

# Add persistent NFSv4 mounts to /etc/fstab
cat << 'EOF' >> /etc/fstab
<TRUENAS_IP>:/mnt/tank/paperless/data    /mnt/paperless/data    nfs defaults,nfsvers=4,timeo=14,intr 0 0
<TRUENAS_IP>:/mnt/tank/paperless/media   /mnt/paperless/media   nfs defaults,nfsvers=4,timeo=14,intr 0 0
<TRUENAS_IP>:/mnt/tank/paperless/consume /mnt/paperless/consume nfs defaults,nfsvers=4,timeo=14,intr 0 0
EOF

mount -a
df -h | grep paperless
```

### 3. Deploy Docker & Compose Stack
```bash
# Install Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh

mkdir -p /docker/paperless && cd /docker/paperless

# Deploy compose file and environment templates from this blueprint
cp .env.example .env

# Generate secure random secret key
SECRET_KEY=$(openssl rand -hex 32)
sed -i "s|<GENERATE_RANDOM_SECRET_KEY>|$SECRET_KEY|" .env

# Start stack
docker compose up -d
```

### 4. Create Initial Administrator Account
```bash
docker exec -it paperless-webserver python3 manage.py createsuperuser
```

### 5. Post-Installation Checklist
- [ ] Log in at `http://192.168.1.246:8000`.
- [ ] Go to **Settings** ➔ **Users & Groups** to configure non-admin user accounts if sharing with family members.
- [ ] Create initial **Document Types**: `Invoice`, `Statement`, `Tax Return`, `Receipt`, `Medical`, `Contract`.
- [ ] Generate a REST API token under **My Profile** for n8n workflow integration.
- [ ] Connect mobile scanner (e.g. *QuickScan* on iOS) to SMB share `smb://<TRUENAS_IP>/paperless-consume`.
