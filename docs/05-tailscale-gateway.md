# 🛡️ 05 - Tailscale Mesh Subnet Gateway (LXC 103)

This blueprint documents configuring an unprivileged Debian 12 LXC container as a 24/7 **Tailscale Subnet Router & Exit Node**, granting secure, zero-trust, WireGuard-encrypted remote access to all homelab devices without opening ports on your home firewall.

---

## ⚙️ 1. Container Provisioning on Proxmox VE

- **VM ID:** `103`
- **Hostname:** `tailscale-gateway`
- **Memory:** `1024 MB`
- **Cores:** `1`
- **Disk:** `8 GB` on `local-lvm`
- **Network:** `vmbr0` with static IP (e.g. `192.168.1.253/24`)

### Provisioning Command:
```bash
pct create 103 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --hostname tailscale-gateway \
  --cores 1 \
  --memory 1024 \
  --swap 512 \
  --rootfs local-lvm:8 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.253/24,gw=192.168.1.1 \
  --unprivileged 1 \
  --features nesting=1 \
  --onboot 1
```

---

## 🔧 2. Crucial Proxmox Host Configuration (TUN Device Passthrough)

Unprivileged containers do not have permission to create `/dev/net/tun` by default. You must configure the host to grant permission:

1. **On the Proxmox VE Host (as `root`):**
   Append the following device rules to `/etc/pve/lxc/103.conf`:
   ```bash
   cat << 'EOF' >> /etc/pve/lxc/103.conf
   lxc.cgroup2.devices.allow: c 10:200 rwm
   lxc.mount.entry: /dev/net/tun dev/net/tun none bind,create=file
   EOF
   ```

2. **Start the Container:**
   ```bash
   pct start 103
   ```

---

## 🚀 3. Container Installation & Subnet Routing

Enter the container (`pct enter 103`) and run:

### A. Enable IPv4 & IPv6 Forwarding
```bash
cat << 'EOF' >> /etc/sysctl.d/99-tailscale.conf
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
EOF

sysctl -p /etc/sysctl.d/99-tailscale.conf
```

### B. Install Tailscale
```bash
curl -fsSL https://tailscale.com/install.sh | sh
systemctl enable --now tailscaled
```

### C. Authenticate & Advertise Subnet
Run the authentication command advertising your entire home LAN subnet (e.g. `192.168.1.0/24`) and optionally as an exit node:

```bash
tailscale up \
  --advertise-routes=<YOUR_HOMELAB_SUBNET_CIDR> \
  --advertise-exit-node \
  --accept-dns=false \
  --reset
```

*Follow the interactive URL to authorize the node in your Tailscale admin console.*

### D. Approve Subnet Routes in Admin Console
1. Open the [Tailscale Admin Console](https://login.tailscale.com/admin/machines).
2. Locate `tailscale-gateway` ➔ click **Edit route settings**.
3. Enable `<YOUR_HOMELAB_SUBNET_CIDR>` (e.g. `192.168.1.0/24`).

---

## ✅ 4. Verification

From your phone or laptop connected via mobile data (outside your home):
1. Connect to Tailscale.
2. Ping any internal homelab device (e.g. `ping 192.168.1.250`).
3. Open your Proxmox GUI: `https://192.168.1.250:8006`.
