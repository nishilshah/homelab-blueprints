# 💰 09 - Firefly III Wealth & Budgeting Engine (LXC 109)

This blueprint documents deploying **Firefly III**, an open-source personal and family financial manager that provides double-entry accounting, multi-currency support, debt amortization tracking, and a comprehensive REST API.

---

## ⚙️ 1. Container Sizing & Provisioning

- **VM ID:** `109`
- **Hostname:** `firefly-iii`
- **Memory:** `2048 MB`
- **Cores:** `2`
- **Disk:** `16 GB` on `local-lvm`
- **Static IP:** `192.168.1.245/24`
- **Features:** Unprivileged LXC, nesting enabled.

### Provisioning Command:
```bash
pct create 109 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --hostname firefly-iii \
  --cores 2 \
  --memory 2048 \
  --swap 512 \
  --rootfs local-lvm:16 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.245/24,gw=192.168.1.1 \
  --unprivileged 1 \
  --features nesting=1 \
  --onboot 1 \
  --start 1
```

---

## 🚀 2. Docker Compose Deployment

Enter the container (`pct enter 109`):

1. **Install Docker:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
   ```

2. **Deploy Compose Stack:**
   Create `/docker/firefly/docker-compose.yml`:

```yaml
version: "3.8"

services:
  firefly_db:
    image: mariadb:11
    container_name: firefly_db
    restart: unless-stopped
    environment:
      MYSQL_RANDOM_ROOT_PASSWORD: "yes"
      MYSQL_USER: firefly
      MYSQL_PASSWORD: <STRONG_RANDOM_DB_PASSWORD>
      MYSQL_DATABASE: firefly
    volumes:
      - ./firefly_db:/var/lib/mysql

  firefly_app:
    image: fireflyiii/core:latest
    container_name: firefly_app
    restart: unless-stopped
    depends_on:
      - firefly_db
    ports:
      - "80:8080"
    environment:
      - APP_KEY=<RANDOM_BASE64_32_CHAR_KEY>
      - APP_ENV=production
      - APP_DEBUG=false
      - APP_URL=http://192.168.1.245
      - DB_CONNECTION=mysql
      - DB_HOST=firefly_db
      - DB_PORT=3306
      - DB_DATABASE=firefly
      - DB_USERNAME=firefly
      - DB_PASSWORD=<STRONG_RANDOM_DB_PASSWORD>
      - TZ=America/Vancouver
      - TRUSTED_PROXIES=**
    volumes:
      - ./firefly_upload:/var/www/html/storage/upload
```

Generate a 32-character base64 key for `APP_KEY`:
```bash
head /dev/urandom | head -c 32 | base64
```

3. **Start Firefly III:**
   ```bash
   cd /docker/firefly && docker compose up -d
   ```

---

## 🏛️ 3. Account Hierarchy & Multi-Currency Setup

Inside the Web UI (`http://<CONTAINER_IP>`):

1. **Currencies:**
   - **Primary:** Canadian Dollar (`CAD`, symbol `C$`).
   - **Foreign Currencies:** Indian Rupee (`INR`, symbol `₹`), US Dollar (`USD`, symbol `$`).
2. **Asset Accounts:**
   - Domestic Chequing & Savings accounts.
   - Real Estate Properties (created as `Asset` accounts with role `Shared Asset`).
3. **Liability Accounts:**
   - Mortgages (`Liability` account with type `Mortgage`).
   - Auto Loans (`Liability` account with type `Loan`).
   - Credit Cards (`Asset` or `Liability` account with type `Credit Card`).
4. **Revenue Accounts:**
   - Corporate payroll & employers.
   - Rental property tenants (UPI / Interac e-Transfers).

---

## 🔑 4. REST API Token Generation

For automation with n8n and Telegram bots:
1. Go to **Profile** ➔ **OAuth** ➔ **Personal Access Tokens**.
2. Click **Create New Token** ➔ Name: `HomelabAutomationToken`.
3. Copy the Bearer Token and store it securely in your secrets manager.
