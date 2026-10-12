# 📄 07 - Paperless-ngx Document Archive (LXC 106)

This blueprint documents deploying **Paperless-ngx**, an open-source document management system that transforms physical documents, bills, and tax notices into searchable PDF archives using Optical Character Recognition (OCR).

---

## ⚙️ 1. Container Sizing & Provisioning

- **VM ID:** `106`
- **Hostname:** `paperless-ngx`
- **Memory:** `4096 MB` (OCR processing requires decent memory)
- **Cores:** `2` (4 recommended for fast multi-page batch OCR)
- **Disk:** `20 GB` on `local-lvm`
- **Static IP:** `192.168.1.246/24`
- **Features:** Unprivileged LXC, nesting enabled.

### Provisioning Command:
```bash
pct create 106 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --hostname paperless-ngx \
  --cores 2 \
  --memory 4096 \
  --swap 1024 \
  --rootfs local-lvm:20 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.246/24,gw=192.168.1.1 \
  --unprivileged 1 \
  --features nesting=1 \
  --onboot 1 \
  --start 1
```

---

## 💾 2. Mounting Storage from TrueNAS (NFS)

Enter the container (`pct enter 106`) and configure NFS mounts:

```bash
apt-get update && apt-get install -y nfs-common curl wget git

# Create local mount targets
mkdir -p /mnt/paperless/data \
         /mnt/paperless/media \
         /mnt/paperless/consume \
         /mnt/paperless/export

# Configure auto-mount in /etc/fstab
cat << 'EOF' >> /etc/fstab
<TRUENAS_IP>:/mnt/tank/paperless/data    /mnt/paperless/data    nfs defaults,timeo=14,intr 0 0
<TRUENAS_IP>:/mnt/tank/paperless/media   /mnt/paperless/media   nfs defaults,timeo=14,intr 0 0
<TRUENAS_IP>:/mnt/tank/paperless/consume /mnt/paperless/consume nfs defaults,timeo=14,intr 0 0
EOF

mount -a
```

---

## 🚀 3. Docker Deployment inside Container

1. **Install Docker Engine:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
   ```

2. **Deploy Paperless-ngx Stack:**
   Create `/docker/paperless/docker-compose.yml`:

```yaml
version: "3.8"

services:
  broker:
    image: docker.io/library/redis:7-alpine
    container_name: paperless-redis
    restart: unless-stopped
    volumes:
      - ./redisdata:/data

  db:
    image: docker.io/library/postgres:16-alpine
    container_name: paperless-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: paperless
      POSTGRES_USER: paperless
      POSTGRES_PASSWORD: <STRONG_RANDOM_DB_PASSWORD>
    volumes:
      - ./pgdata:/var/lib/postgresql/data

  webserver:
    image: ghcr.io/paperless-ngx/paperless-ngx:latest
    container_name: paperless-webserver
    restart: unless-stopped
    depends_on:
      - db
      - broker
    ports:
      - "8000:8000"
    environment:
      PAPERLESS_REDIS: redis://broker:6379
      PAPERLESS_DBENGINE: postgresql
      PAPERLESS_DBHOST: db
      PAPERLESS_DBNAME: paperless
      PAPERLESS_DBUSER: paperless
      PAPERLESS_DBPASS: <STRONG_RANDOM_DB_PASSWORD>
      PAPERLESS_URL: http://192.168.1.246:8000
      PAPERLESS_SECRET_KEY: <RANDOM_HEX_64_CHAR_KEY>
      PAPERLESS_TIME_ZONE: America/Vancouver
      PAPERLESS_OCR_LANGUAGE: eng
      PAPERLESS_OCR_LANGUAGES: eng fra
      USERMAP_UID: 1000
      USERMAP_GID: 1000
    volumes:
      - /mnt/paperless/data:/usr/src/paperless/data
      - /mnt/paperless/media:/usr/src/paperless/media
      - /mnt/paperless/export:/usr/src/paperless/export
      - /mnt/paperless/consume:/usr/src/paperless/consume
```

3. **Start Paperless-ngx:**
   ```bash
   cd /docker/paperless && docker compose up -d
   ```

4. **Create Administrative Superuser:**
   ```bash
   docker exec -it paperless-webserver python3 manage.py createsuperuser
   ```

---

## 📱 4. Ingestion Workflow & Scanner Integration

- **Web Dashboard:** Access `http://<CONTAINER_IP>:8000`.
- **Mobile Scanner Setup:** Share the SMB `/mnt/tank/paperless/consume` directory to your phone. Use apps like **QuickScan** (iOS) or **Genius Scan** to drop PDFs directly into `consume/`.
- **Automatic Ingestion:** Paperless-ngx detects new files immediately, executes OCR, indexes text, and files the document into `media/`.
