#!/usr/bin/env python3
"""
Top 500 DNS & Network Reachability Benchmark
Tests DNS resolution and TCP reachability against the Homelab AdGuard Home DNS server (192.168.1.242).
Uses the Tranco Top Sites dataset (curated from Chrome UX Report, Cloudflare Radar, and Cisco Umbrella).
"""

import sys
import os
import time
import socket
import struct
import urllib.request
import zipfile
import io
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

DNS_SERVER_DEFAULT = "192.168.1.242"
DNS_PORT_DEFAULT = 53
CACHE_FILE_DEFAULT = os.path.expanduser("~/.gemini/antigravity/scratch/top500_domains.txt")
TRANCO_URL = "https://tranco-list.eu/top-1m.csv.zip"


def fetch_top_domains(count=500, cache_file=CACHE_FILE_DEFAULT):
    """Fetch top domains from cache or download from Tranco."""
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            domains = [line.strip() for line in f if line.strip()]
        if len(domains) >= count:
            return domains[:count]

    print(f"📥 Fetching official Tranco Top Sites list (top {count})...")
    req = urllib.request.Request(TRANCO_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        z = zipfile.ZipFile(io.BytesIO(resp.read()))
        csv_filename = z.namelist()[0]
        with z.open(csv_filename) as f:
            domains = []
            for _ in range(count):
                line = f.readline().decode("utf-8").strip()
                if not line:
                    break
                parts = line.split(",")
                if len(parts) >= 2:
                    domains.append(parts[1])

    # Cache for fast re-runs
    os.makedirs(os.path.dirname(os.path.abspath(cache_file)), exist_ok=True)
    with open(cache_file, "w") as f:
        for d in domains:
            f.write(f"{d}\n")

    return domains


def build_dns_query(domain, qtype=1, tx_id=0x1234):
    """Construct a RFC 1035 compliant DNS query packet."""
    header = struct.pack("!HHHHHH", tx_id, 0x0100, 1, 0, 0, 0)
    parts = domain.strip(".").split(".")
    qname = b"".join(bytes([len(p)]) + p.encode("ascii") for p in parts) + b"\x00"
    return header + qname + struct.pack("!HH", qtype, 1)


def parse_dns_response(data):
    """Parse raw DNS response bytes extracting RCODE and IPv4 addresses."""
    if len(data) < 12:
        return {"status": "MALFORMED", "rcode": -1, "ips": []}

    tid, flags, qdcount, ancount, _, _ = struct.unpack("!HHHHHH", data[:12])
    rcode = flags & 0x000F

    idx = 12
    # Skip question section
    for _ in range(qdcount):
        while idx < len(data) and data[idx] != 0:
            if data[idx] >= 0xC0:
                idx += 2
                break
            idx += data[idx] + 1
        if idx < len(data) and data[idx] == 0:
            idx += 1
        idx += 4  # qtype + qclass

    ips = []
    # Parse answers
    for _ in range(ancount):
        if idx >= len(data):
            break
        # Skip domain name / pointer
        if data[idx] >= 0xC0:
            idx += 2
        else:
            while idx < len(data) and data[idx] != 0:
                idx += data[idx] + 1
            if idx < len(data) and data[idx] == 0:
                idx += 1

        if idx + 10 > len(data):
            break
        atype, aclass, attl, rdlength = struct.unpack("!HHIH", data[idx:idx + 10])
        idx += 10

        if atype == 1 and rdlength == 4:  # A Record
            ips.append(socket.inet_ntoa(data[idx:idx + 4]))
        idx += rdlength

    if rcode == 0:
        if "0.0.0.0" in ips or "127.0.0.1" in ips:
            status = "BLOCKED"
        elif ips:
            status = "RESOLVED"
        else:
            status = "NO_A_RECORD"
    elif rcode == 3:
        status = "NXDOMAIN"
    elif rcode == 2:
        status = "SERVFAIL"
    elif rcode == 5:
        status = "REFUSED"
    else:
        status = f"RCODE_{rcode}"

    return {"status": status, "rcode": rcode, "ips": ips}


def test_domain(domain, server, port, timeout_dns=2.5, check_tcp=True, timeout_tcp=1.5):
    """Test DNS resolution and TCP reachability for a single domain."""
    tx_id = (hash(domain) & 0xFFFF)
    packet = build_dns_query(domain, qtype=1, tx_id=tx_id)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout_dns)

    t0 = time.perf_counter()
    try:
        sock.sendto(packet, (server, port))
        data, _ = sock.recvfrom(4096)
        dt_ms = (time.perf_counter() - t0) * 1000
        parsed = parse_dns_response(data)
        status = parsed["status"]
        ips = parsed["ips"]
    except socket.timeout:
        return {
            "domain": domain,
            "dns_status": "TIMEOUT",
            "latency_ms": None,
            "ips": [],
            "tcp_status": "SKIPPED",
        }
    except Exception as e:
        return {
            "domain": domain,
            "dns_status": f"ERR_{type(e).__name__}",
            "latency_ms": None,
            "ips": [],
            "tcp_status": "SKIPPED",
        }
    finally:
        sock.close()

    # TCP reachability check on port 443 / 80
    tcp_status = "SKIPPED"
    if check_tcp and status == "RESOLVED" and ips:
        target_ip = ips[0]
        # Attempt HTTPS (443)
        tsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tsock.settimeout(timeout_tcp)
        try:
            tsock.connect((target_ip, 443))
            tcp_status = "OK (443)"
        except Exception:
            # Fallback to HTTP (80)
            try:
                tsock.close()
                tsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tsock.settimeout(timeout_tcp)
                tsock.connect((target_ip, 80))
                tcp_status = "OK (80)"
            except Exception as e2:
                tcp_status = f"FAIL_{type(e2).__name__}"
        finally:
            tsock.close()

    return {
        "domain": domain,
        "dns_status": status,
        "latency_ms": dt_ms,
        "ips": ips,
        "tcp_status": tcp_status,
    }


def main():
    parser = argparse.ArgumentParser(description="Homelab AdGuard Top 500 Reachability Benchmark")
    parser.add_argument("--server", default=DNS_SERVER_DEFAULT, help="DNS Server IP (default: 192.168.1.242)")
    parser.add_argument("--port", type=int, default=DNS_PORT_DEFAULT, help="DNS Port (default: 53)")
    parser.add_argument("--count", type=int, default=500, help="Number of domains to test (default: 500)")
    parser.add_argument("--workers", type=int, default=25, help="Concurrent worker threads (default: 25)")
    parser.add_argument("--no-tcp", action="store_true", help="Skip TCP port 443/80 reachability check")
    parser.add_argument("--timeout-dns", type=float, default=2.5, help="DNS query timeout in seconds (default: 2.5)")
    parser.add_argument("--timeout-tcp", type=float, default=1.5, help="TCP connect timeout in seconds (default: 1.5)")
    args = parser.parse_args()

    check_tcp = not args.no_tcp
    print("=" * 70)
    print("🚀 HOMELAB ADGUARD HOME TOP SITES BENCHMARK")
    print(f"🎯 Target DNS Server : {args.server}:{args.port}")
    print(f"📊 Sample Size       : Top {args.count} Most Visited Domains (Tranco List)")
    print(f"⚡ Concurrency       : {args.workers} Parallel Worker Threads")
    print(f"🌐 TCP Reachability  : {'Enabled (Ports 443 / 80)' if check_tcp else 'Disabled'}")
    print("=" * 70)

    domains = fetch_top_domains(count=args.count)
    print(f"Loaded {len(domains)} domains. Initiating parallel benchmark...")

    results = []
    start_time = time.perf_counter()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                test_domain,
                domain,
                args.server,
                args.port,
                args.timeout_dns,
                check_tcp,
                args.timeout_tcp,
            ): domain
            for domain in domains
        }

        completed = 0
        total = len(domains)
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            completed += 1
            if completed % 50 == 0 or completed == total:
                pct = (completed / total) * 100
                print(f"  [{completed:>3}/{total}] ({pct:>5.1f}%) Completed... Latest: {res['domain']:<25} DNS: {res['dns_status']}")

    total_duration = time.perf_counter() - start_time

    # Calculate statistics
    resolved = [r for r in results if r["dns_status"] == "RESOLVED"]
    blocked = [r for r in results if r["dns_status"] == "BLOCKED"]
    no_a = [r for r in results if r["dns_status"] == "NO_A_RECORD"]
    nxdomain = [r for r in results if r["dns_status"] == "NXDOMAIN"]
    timeouts = [r for r in results if r["dns_status"] == "TIMEOUT"]
    errors = [r for r in results if r["dns_status"] not in ("RESOLVED", "BLOCKED", "NO_A_RECORD", "NXDOMAIN", "TIMEOUT")]

    latencies = [r["latency_ms"] for r in results if r["latency_ms"] is not None]
    latencies.sort()

    tcp_ok = [r for r in results if r["tcp_status"].startswith("OK")]
    tcp_tested = [r for r in results if r["tcp_status"] != "SKIPPED"]

    print("\n" + "=" * 70)
    print("📊 BENCHMARK SUMMARY RESULTS")
    print("=" * 70)
    print(f"⏱️  Total Test Execution Time : {total_duration:.2f} seconds ({len(domains)/total_duration:.1f} queries/sec)")
    print(f"✅ Cleanly Resolved          : {len(resolved):>4} / {len(domains)} ({len(resolved)/len(domains)*100:>5.1f}%)")
    print(f"🛡️  Blocked by AdGuard        : {len(blocked):>4} / {len(domains)} ({len(blocked)/len(domains)*100:>5.1f}%) [Ads/Trackers Sinkholed]")
    print(f"ℹ️  No A Record (Root/Infra)  : {len(no_a):>4} / {len(domains)} ({len(no_a)/len(domains)*100:>5.1f}%) [e.g. akamai.net, akadns.net]")
    print(f"❓ NXDOMAIN                  : {len(nxdomain):>4} / {len(domains)} ({len(nxdomain)/len(domains)*100:>5.1f}%)")
    print(f"⌛ DNS Timeouts              : {len(timeouts):>4} / {len(domains)} ({len(timeouts)/len(domains)*100:>5.1f}%)")
    print(f"❌ Other Errors              : {len(errors):>4} / {len(domains)} ({len(errors)/len(domains)*100:>5.1f}%)")

    if check_tcp and tcp_tested:
        print(f"🌐 TCP Reachability (443/80) : {len(tcp_ok):>4} / {len(tcp_tested)} ({len(tcp_ok)/len(tcp_tested)*100:>5.1f}%)")

    if latencies:
        p50 = latencies[int(len(latencies) * 0.50)]
        p90 = latencies[int(len(latencies) * 0.90)]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
        avg = sum(latencies) / len(latencies)
        print("\n⚡ DNS LATENCY DISTRIBUTION (ms):")
        print(f"   Min      : {latencies[0]:>6.2f} ms")
        print(f"   Average  : {avg:>6.2f} ms")
        print(f"   Median   : {p50:>6.2f} ms")
        print(f"   90th %ile: {p90:>6.2f} ms")
        print(f"   95th %ile: {p95:>6.2f} ms")
        print(f"   99th %ile: {p99:>6.2f} ms")
        print(f"   Max      : {latencies[-1]:>6.2f} ms")

    if blocked:
        print("\n🛡️  SAMPLE OF TOP VISITED TRACKER/AD DOMAINS SINKHOLED BY ADGUARD:")
        for b in blocked[:10]:
            print(f"   • {b['domain']:<30} -> {b['ips']} (Latency: {b['latency_ms']:.1f}ms)")

    if timeouts:
        print("\n⚠️  DOMAINS THAT TIMED OUT:")
        for t in timeouts:
            print(f"   • {t['domain']}")

    print("=" * 70)


if __name__ == "__main__":
    main()
