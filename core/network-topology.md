# 🌐 Core Network Topology & Subnet Design

This blueprint establishes the physical and logical networking topology, private IP allocations, DNS resolution, and Zero-Trust remote access for the homelab.

---

## 🔗 Official Documentation & References

- **OPNsense Documentation:** [docs.opnsense.org](https://docs.opnsense.org)
- **Tailscale Subnet Routing:** [tailscale.com/kb/1019/subnets](https://tailscale.com/kb/1019/subnets)
- **WireGuard Protocol:** [wireguard.com](https://www.wireguard.com)
- **Proxmox VE Network Model:** [pve.proxmox.com/wiki/Network_Configuration](https://pve.proxmox.com/wiki/Network_Configuration)

---

## 🗺️ Logical Network Architecture

```mermaid
flowchart TD
    WAN["🌐 Internet / ISP Fiber Gateway"] --> Router["🛡️ Firewall & Gateway Router<br/>(192.168.1.1)"]
    
    subgraph LAN ["Physical LAN (192.168.1.0/24)"]
        Switch["Managed 2.5GbE / 10GbE Switch"]
        Router --> Switch

        subgraph PVE_Node ["Proxmox VE Host (192.168.1.250)"]
            vmbr0["Bridge: vmbr0"]
            Switch --> vmbr0
            
            subgraph LXCs ["LXC Containers"]
                TS["LXC 103: Tailscale Router<br/>(192.168.1.253)"]
                Paperless["LXC 106: Paperless-ngx<br/>(192.168.1.246)"]
                N8N["LXC 107: n8n Automation<br/>(192.168.1.247)"]
                Quant["LXC 108: Quant Trading<br/>(192.168.1.248)"]
                Firefly["LXC 109: Firefly III<br/>(192.168.1.245)"]
                Immich["LXC 102: Immich Photos<br/>(192.168.1.252)"]
                Monitor["LXC 104: Monitoring<br/>(192.168.1.249)"]
            end

            subgraph VMs ["Virtual Machines"]
                TrueNAS["VM 101: TrueNAS SCALE<br/>(192.168.1.139)"]
                Servarr["VM 100: Servarr Docker<br/>(192.168.1.251)"]
                HA["VM 105: Home Assistant<br/>(192.168.1.72)"]
            end

            vmbr0 --> LXCs
            vmbr0 --> VMs
        end
    end

    subgraph TailscaleMesh ["Tailscale Zero-Trust Overlay (100.64.0.0/10)"]
        RemoteLaptop["Remote Laptop"]
        Phone["Mobile Client"]
        RemoteLaptop -.->|Encrypted WireGuard| TS
        Phone -.->|Encrypted WireGuard| TS
        TS -.->|Subnet Routing 192.168.1.0/24| LAN
    end
```

---

## 📊 IP Address Allocation Matrix

| IP Address | Hostname / Service | Virtualization | Description |
| :--- | :--- | :---: | :--- |
| `192.168.1.1` | `gateway.homelab.local` | Physical Router | Core Gateway & DHCP/DNS server |
| `192.168.1.250` | `pve.homelab.local` | Bare-Metal | Proxmox VE Hypervisor Node |
| `192.168.1.139` | `truenas.homelab.local` | VM 101 | TrueNAS SCALE ZFS Storage Appliance |
| `192.168.1.251` | `servarr.homelab.local` | VM 100 | Ubuntu 24.04 Media Docker Stack & Homepage |
| `192.168.1.252` | `immich.homelab.local` | LXC 102 | Immich Photo & Video Cloud |
| `192.168.1.253` | `tailscale.homelab.local` | LXC 103 | Tailscale Subnet Router & Mesh Gateway |
| `192.168.1.249` | `monitoring.homelab.local`| LXC 104 | Prometheus & Grafana Telemetry |
| `192.168.1.72` | `homeassistant.homelab.local`| VM 105 | Home Assistant OS (HAOS) Smart Hub |
| `192.168.1.246` | `paperless.homelab.local` | LXC 106 | Paperless-ngx OCR Document Archive |
| `192.168.1.247` | `n8n.homelab.local` | LXC 107 | n8n Workflow Engine & Telegram AI Bot |
| `192.168.1.248` | `quant.homelab.local` | LXC 108 | OpenBB & TradingView Ingress Webhook |
| `192.168.1.245` | `firefly.homelab.local` | LXC 109 | Firefly III Wealth & Budgeting Platform |

---

## 🔒 Security Principles

1. **Zero Open Inbound Ports:** No public ports are forwarded on the residential gateway.
2. **Zero-Trust Remote Access:** All off-site access from laptops and mobile phones routes through Tailscale using modern ChaCha20-Poly1305 WireGuard encryption.
3. **Download Shielding:** BitTorrent and Usenet traffic in VM 100 is strictly bound to an ephemeral WireGuard tunnel (`gluetun`), preventing residential ISP exposure.
