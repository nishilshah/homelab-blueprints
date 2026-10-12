# 🖥️ 01 - Proxmox VE Host Configuration

This blueprint covers setting up the bare-metal **Proxmox Virtual Environment (PVE)** hypervisor, tuning storage pools, enabling non-subscription repositories, and preparing the host for nested virtualization and GPU passthrough.

---

## ⚙️ 1. Host Sizing & Recommendations

- **Operating System:** Proxmox VE 8.x (Debian 12 Bookworm base)
- **Management Web UI:** `https://<PVE_NODE_IP>:8006`
- **Recommended Hostname:** `pve` or `pve-node-01`
- **Default Network Bridge:** `vmbr0` tied to primary physical NIC (`eno1` or `enp3s0`).

---

## 🛠️ 2. Post-Installation Configuration Commands

After installing Proxmox VE from USB, log into the host via SSH as `root` and run the following commands:

### A. Disable Enterprise Repository & Enable Community No-Subscription Repo
```bash
# Disable commercial enterprise apt source
rm -f /etc/apt/sources.list.d/pve-enterprise.list

# Enable Proxmox No-Subscription repository
cat << 'EOF' > /etc/apt/sources.list.d/pve-no-subscription.list
deb http://download.proxmox.com/debian/pve bookworm pve-no-subscription
EOF

# Update package repositories and install system tools
apt-get update && apt-get dist-upgrade -y
apt-get install -y htop iotop iftop curl wget git zfsutils-linux sudo
```

### B. Disable the "No Subscription" Web GUI Nag Dialog
```bash
# Automatically patches the PVE GUI nag banner
sed -Ezi.bak "s/(Ext.Msg.show\(\{\s+title: gettext\('No valid sub)/void\(\{ \/\/\1/g" /usr/share/javascript/proxmox-widget-toolkit/proxmoxlib.js
systemctl restart pveproxy.service
```

### C. Enable IOMMU & Intel QuickSync GPU Passthrough Modules
If your CPU has an integrated Intel GPU (e.g. Intel UHD / Iris Xe), enable IOMMU and graphics drivers in the Linux kernel:

```bash
# 1. Edit Grub configuration
sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="quiet"/GRUB_CMDLINE_LINUX_DEFAULT="quiet intel_iommu=on iommu=pt i915.enable_guc=3"/' /etc/default/grub
update-grub

# 2. Add VFIO and Render kernel modules
cat << 'EOF' >> /etc/modules
vfio
vfio_iommu_type1
vfio_pci
vfio_virqfd
kvmgt
EOF

# 3. Verify render nodes exist
ls -la /dev/dri
# Output should show: card0 and renderD128
```

---

## 📦 3. Storage Pools Setup

1. **`local` (Directory):** Used for ISOs, backup archives, and container templates (`/var/lib/vz`).
2. **`local-lvm` (LVM-Thin):** High-speed block storage for VM virtual disks (`raw`) and container root filesystems (`subvol`).
3. **ZFS Storage (Optional `zpool`):** If using bare-metal ZFS pools directly on PVE:
   ```bash
   zpool status
   ```

---

## 🔒 4. Hardening & SSH Access

```bash
# Allow key-based SSH authentication
mkdir -p ~/.ssh && chmod 700 ~/.ssh
cat /path/to/your/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Optional: Disable password authentication once key is verified
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd
```
