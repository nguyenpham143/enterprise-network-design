# TVI Network — IP Addressing Plan (Step 2)

Companion to `TVI-Topology.drawio`. Matches `TVI-Plan-v1.2.md` section 2.4.

## 1. Design rules

| Rule | Value |
|---|---|
| Private IPv4 space | `10.0.0.0/8` (RFC 1918) |
| One block per site | HQ `10.10.0.0/16`, Hanoi `10.20.0.0/16`, Da Nang `10.30.0.0/16` |
| VLSM sizing | Planned hosts = required hosts × 1.5 (50% growth). Prefix = smallest block where 2^(32−prefix) − 2 ≥ planned hosts |
| Gateway | First usable address. At HQ it is the HSRP virtual IP; HCMC-DIST-SW01 = network + 2, HCMC-DIST-SW02 = network + 3 |
| DHCP | Centralized at HQ; `.1`–`.9` of each pool excluded; relay with `ip helper-address`. HQ pools on SRV-DHCP-DNS `10.10.47.10`; branch pools on HCMC-EDGE-RTR01 `10.10.255.1` (reached over the tunnels) |
| IPv6 | `2001:db8::/32` (RFC 3849) → one /48 per site → one /64 per VLAN. Lab: GUA on every L3 interface, connected routes only (no IPv6 routing between subnets) |
| Public / WAN | `203.0.113.0/24` (RFC 5737), one /30 per site |
| Routing | Each site: its own OSPF process, multi-area. HQ: area 0 = EDGE–CORE, area 10 = distribution block (CORE is ABR, summary `10.10.0.0/18`). Branches: area 0 = router–switch link, area 20 (Hanoi) / area 30 (Da Nang) = user VLANs (router is ABR). Between sites: eBGP over GRE/IPsec, one /16 summary per site |

Required hosts per site come from the assignment (HQ 2,000+, Hanoi 1,500+, Da Nang 500+ users, 10,000+ IoT endpoints) and are split per VLAN below. At HQ the assignment names only VLAN 10 (Executive/Finance, 300 users); the other ~1,700 HQ users get a reserved /20 for their department VLANs. VOICE is sized for one phone per HQ user (2,000).

## 2. HQ — Ho Chi Minh City — `10.10.0.0/16` · `2001:db8:10::/48` · AS 65001

| VLAN | Name | Hosts | Planned | Prefix | Network | Mask | Usable range | Gateway (VIP) | DIST-SW01 / SW02 | DHCP pool | IPv6 /64 |
|---:|---|---:|---:|---:|---|---|---|---|---|---|---|
| 50 | VOICE | 2,000 | 3,000 | /20 | `10.10.0.0` | `255.255.240.0` | `10.10.0.1`–`10.10.15.254` | `10.10.0.1` | `.2` / `.3` | `10.10.0.10`–`10.10.15.254` | `2001:db8:10:50::/64` |
| 40 | GUEST | 500 | 750 | /22 | `10.10.40.0` | `255.255.252.0` | `10.10.40.1`–`10.10.43.254` | `10.10.40.1` | `.2` / `.3` | `10.10.40.10`–`10.10.43.254` | `2001:db8:10:40::/64` * |
| 10 | EXEC_FINANCE | 300 | 450 | /23 | `10.10.44.0` | `255.255.254.0` | `10.10.44.1`–`10.10.45.254` | `10.10.44.1` | `.2` / `.3` | `10.10.44.10`–`10.10.45.254` | `2001:db8:10:10::/64` |
| 99 | MANAGEMENT | 100 | 150 | /24 | `10.10.46.0` | `255.255.255.0` | `10.10.46.1`–`10.10.46.254` | `10.10.46.1` | `.2` / `.3` | static | `2001:db8:10:99::/64` |
| 100 | SERVERS | 120 | 180 | /24 | `10.10.47.0` | `255.255.255.0` | `10.10.47.1`–`10.10.47.254` | `10.10.47.1` | `.2` / `.3` | static | `2001:db8:10:100::/64` |
| — | Other HQ departments (reserved, not built in lab) | 1,700 | 2,550 | /20 | `10.10.16.0` | `255.255.240.0` | `10.10.16.1`–`10.10.31.254` | — | — | — | — |
| — | Infrastructure | — | — | /24 | `10.10.255.0` | `255.255.255.0` | Loopbacks + point-to-point links | — | — | — | `2001:db8:10:ff00::/56` |

## 3. R&D — Hanoi — `10.20.0.0/16` · `2001:db8:20::/48` · AS 65002

| VLAN | Name | Hosts | Planned | Prefix | Network | Mask | Usable range | Gateway | DHCP pool | IPv6 /64 |
|---:|---|---:|---:|---:|---|---|---|---|---|---|
| 20 | RND_ENGINEERING | 1,200 | 1,800 | /21 | `10.20.16.0` | `255.255.248.0` | `10.20.16.1`–`10.20.23.254` | `10.20.16.1` | `10.20.16.10`–`10.20.23.254` | `2001:db8:20:20::/64` |
| 40 | GUEST | 300 | 450 | /23 | `10.20.30.0` | `255.255.254.0` | `10.20.30.1`–`10.20.31.254` | `10.20.30.1` | `10.20.30.10`–`10.20.31.254` | `2001:db8:20:40::/64` * |
| 99 | MANAGEMENT | 80 | 120 | /25 | `10.20.32.0` | `255.255.255.128` | `10.20.32.1`–`10.20.32.126` | `10.20.32.1` | static | `2001:db8:20:99::/64` |
| — | Infrastructure | — | — | /24 | `10.20.255.0` | `255.255.255.0` | Loopbacks | — | — | `2001:db8:20:ff00::/56` |

## 4. Logistics — Da Nang — `10.30.0.0/16` · `2001:db8:30::/48` · AS 65003

| VLAN | Name | Hosts | Planned | Prefix | Network | Mask | Usable range | Gateway | DHCP pool | IPv6 /64 |
|---:|---|---:|---:|---:|---|---|---|---|---|---|
| 30 | LOGISTICS_OPS | 500 | 750 | /22 | `10.30.80.0` | `255.255.252.0` | `10.30.80.1`–`10.30.83.254` | `10.30.80.1` | `10.30.80.10`–`10.30.83.254` | `2001:db8:30:30::/64` |
| 40 | GUEST | 200 | 300 | /23 | `10.30.88.0` | `255.255.254.0` | `10.30.88.1`–`10.30.89.254` | `10.30.88.1` | `10.30.88.10`–`10.30.89.254` | `2001:db8:30:40::/64` * |
| 99 | MANAGEMENT | 100 | 150 | /24 | `10.30.90.0` | `255.255.255.0` | `10.30.90.1`–`10.30.90.254` | `10.30.90.1` | static | `2001:db8:30:99::/64` |
| 60 | IOT (gateway, ACL and one test host built in lab) | 10,000 | 15,000 | /18 | `10.30.0.0` | `255.255.192.0` | `10.30.0.1`–`10.30.63.254` | `10.30.0.1` | static in lab | `2001:db8:30:60::/64` * |
| — | Infrastructure | — | — | /24 | `10.30.255.0` | `255.255.255.0` | Loopbacks | — | — | `2001:db8:30:ff00::/56` |

\* Allocated in the plan; IPv6 is not enabled on Guest VLANs in the lab, to keep Guest isolated.

## 5. Infrastructure

| Item | IPv4 | IPv6 |
|---|---|---|
| Loopback0 HCMC-EDGE-RTR01 / HCMC-CORE-SW01 / HCMC-DIST-SW01 / HCMC-DIST-SW02 | `10.10.255.1` / `.2` / `.3` / `.4` /32 | `2001:db8:10:ffff::1` / `::2` / `::3` / `::4` /128 |
| Loopback0 HANOI-RND-RTR01 / HANOI-RND-SW01 | `10.20.255.1` / `10.20.255.2` /32 | `2001:db8:20:ffff::1` / `::2` /128 |
| Loopback0 DANANG-LOG-RTR01 / DANANG-LOG-SW01 | `10.30.255.1` / `10.30.255.2` /32 | `2001:db8:30:ffff::1` / `::2` /128 |
| EDGE Gi0/1.900 ⇄ CORE Gi0/0 (trunk, SVI Vlan900) | `10.10.255.64/30` (`.65` / `.66`) | `2001:db8:10:ff01::1` / `::2` /64 |
| CORE Po1 ⇄ DIST-SW01 Po1 (LACP trunk, SVI Vlan901) | `10.10.255.68/30` (`.69` / `.70`) | `2001:db8:10:ff02::1` / `::2` /64 |
| CORE Po2 ⇄ DIST-SW02 Po1 (LACP trunk, SVI Vlan902) | `10.10.255.72/30` (`.73` / `.74`) | `2001:db8:10:ff03::1` / `::2` /64 |
| WAN HCMC ⇄ ISP (demarcation) | `203.0.113.0/30` (ISP `.1`, HCMC `.2`) | `2001:db8:ffff:1::/64` * |
| WAN Hanoi ⇄ ISP (demarcation) | `203.0.113.4/30` (ISP `.5`, Hanoi `.6`) | `2001:db8:ffff:2::/64` * |
| WAN Da Nang ⇄ ISP (demarcation) | `203.0.113.8/30` (ISP `.9`, Da Nang `.10`) | `2001:db8:ffff:3::/64` * |
| Tunnel0 HCMC ⇄ Hanoi (GRE/IPsec) | `172.16.12.0/30` (HQ `.1`, Hanoi `.2`) | `2001:db8:0:12::/64` * |
| Tunnel1 HCMC ⇄ Da Nang (GRE/IPsec) | `172.16.13.0/30` (HQ `.1`, Da Nang `.2`) | `2001:db8:0:13::/64` * |
| Simulated Internet (Loopback on ISP-RTR01) | `8.8.8.8/24` | — |

\* Allocated, not enabled in the lab (no inter-site IPv6 routing).

## 6. Static device addresses

| Device | Address | Gateway |
|---|---|---|
| SRV-DHCP-DNS (VLAN 100) | `10.10.47.10/24` · `2001:db8:10:100::10/64` | `10.10.47.1` · IPv6 default from RA |
| AUTOMATION container eth0 (VLAN 99) | `10.10.46.50/24` | No default gateway; route `10.0.0.0/8 via 10.10.46.1` (eth1 to GNS3 NAT keeps the default route) |
| HCMC-DIST-SW01 / SW02 (SVI Vlan99) | `10.10.46.2` / `10.10.46.3` | — (L3 switch) |
| HCMC-ACC-SW01 (VLAN 99) | `10.10.46.11/24` | `10.10.46.1` |
| HANOI-RND-SW01 / SW02 (VLAN 99) | `10.20.32.11` / `10.20.32.12` /25 | SW01: OSPF · SW02: static default route via `10.20.32.1` |
| DANANG-LOG-SW01 (VLAN 99) | `10.30.90.11/24` | OSPF |
| IOT-DN1 (VLAN 60, test IoT host) | `10.30.0.10/18` | `10.30.0.1` |
| HCMC-CORE-SW01, all site routers | Loopback0 (section 5) | — |

PCs and the IP phone get IPv4 by DHCP (HQ from SRV-DHCP-DNS, branches from HCMC-EDGE-RTR01) and IPv6 by SLAAC.

## 7. IPv6 hierarchy

```text
2001:0db8 : SITE : SUBNET :: host
 /32 (RFC 3849)   /48     /64
SITE:   0 = tunnels, 10 = HQ, 20 = Hanoi, 30 = Da Nang, ffff = WAN links
SUBNET: VLAN ID written as digits (10, 20, 30, 40, 50, 99, 100); 60 = IoT reserve;
        ff01–ff03 = point-to-point links; ffff = loopbacks (/128)
```

Each /48 holds 65,536 /64 subnets, so no site will run out of IPv6 subnets.

## 8. Address use and growth

| Site | Allocated (VLANs + infra /24) | Share of /16 | Free |
|---|---:|---:|---:|
| HQ (with /20 reserve for other departments) | 10,496 | 16.0% | 84.0% |
| Hanoi | 2,944 | 4.5% | 95.5% |
| Da Nang (without IoT reserve) | 2,048 | 3.1% | 96.9% |
| Da Nang (with IoT /18 reserve) | 18,432 | 28.1% | 71.9% |

## 9. Summarization

- Each site edge router advertises exactly one route over the eBGP tunnel overlay: `network 10.X.0.0 mask 255.255.0.0` with `ip route 10.X.0.0 255.255.0.0 Null0`.
- HQ therefore sees only `10.20.0.0/16` and `10.30.0.0/16`; new VLANs inside a branch never change HQ's routing table.
- eBGP to the ISP carries only the public /30s (prefix-list `PUBLIC-ONLY`); 10.x never leaves TVI. Users reach the Internet through NAT overload on each site's Gi0/0.
