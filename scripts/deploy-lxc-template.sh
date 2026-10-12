#!/usr/bin/env bash
# ==============================================================================
# Standardized Proxmox VE LXC Provisioning Blueprint
# Deploys a production-ready Debian 12 LXC container with static IP and SSH.
# ==============================================================================

set -euo pipefail

# Sizing Defaults (Adjust as needed per service)
VMID="${1:-110}"
HOSTNAME="${2:-homelab-service}"
MEMORY="${3:-2048}"
CORES="${4:-2}"
DISK_SIZE="${5:-16G}"
IP_ADDRESS="${6:-192.168.1.110/24}"
GATEWAY="${7:-192.168.1.1}"
BRIDGE="${8:-vmbr0}"
STORAGE_POOL="${9:-local-lvm}"

# Template selection (Debian 12 Bookworm standard)
TEMPLATE_STORAGE="local"
TEMPLATE_NAME="debian-12-standard_12.7-1_amd64.tar.zst"

echo "=========================================================="
echo "🚀 Provisioning LXC Container: $VMID ($HOSTNAME)"
echo "Memory: ${MEMORY}MB | Cores: ${CORES} | Disk: ${DISK_SIZE}"
echo "IP: ${IP_ADDRESS} | GW: ${GATEWAY}"
echo "=========================================================="

# Check if template exists, if not download it
if ! pveam list "$TEMPLATE_STORAGE" | grep -q "$TEMPLATE_NAME"; then
    echo "📥 Downloading Debian 12 template to $TEMPLATE_STORAGE..."
    pveam update
    pveam download "$TEMPLATE_STORAGE" "$TEMPLATE_NAME"
fi

# Create LXC Container
pct create "$VMID" "${TEMPLATE_STORAGE}:vztmpl/${TEMPLATE_NAME}" \
    --hostname "$HOSTNAME" \
    --cores "$CORES" \
    --memory "$MEMORY" \
    --swap 512 \
    --rootfs "${STORAGE_POOL}:${DISK_SIZE}" \
    --net0 "name=eth0,bridge=${BRIDGE},ip=${IP_ADDRESS},gw=${GATEWAY}" \
    --onboot 1 \
    --start 1 \
    --unprivileged 1 \
    --features nesting=1

echo "⏳ Waiting for container to initialize..."
sleep 5

# Upgrade system packages inside container
pct exec "$VMID" -- apt-get update
pct exec "$VMID" -- apt-get install -y curl wget sudo ca-certificates gnupg lsb-release

echo "✅ Container $VMID ($HOSTNAME) provisioned and online!"
echo "To access console: pct enter $VMID"
