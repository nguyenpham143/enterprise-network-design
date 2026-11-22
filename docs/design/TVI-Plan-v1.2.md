# Kế hoạch BTL2 TVI — Triển khai lại từ đầu trên GNS3 (Bản chốt v1.2)

> **Thay đổi so với v1.1** (do giới hạn image đã kiểm tra thực tế ngày 12/11/2026):
> 1. Image switch duy nhất có được là vIOS-L2 **15.0(TTC_20140605)** (bản thử nghiệm 2014). Image này chỉ boot khi ổ đĩa là **IDE** (template GNS3 `vIOS-L2`: IDE, 1024 MB, 8 cổng Gi0/0–Gi1/3). Image **không có OSPFv3 và DAI**.
> 2. Bỏ OSPFv3 khỏi lab. IPv6 vẫn dual-stack (GUA trên mọi interface L3 trong lab), nhưng chỉ định tuyến bằng connected route. OSPFv3 chuyển thành nội dung giải thích trong report. Checklist mục VI ghi "OSPFv3 **or** multi-area OSPF", nên lab chạy **OSPFv2 multi-area** (xem ghi chú 11).
> 3. Bỏ DAI khỏi lab. Rubric Step 7 ghi "DHCP Snooping**/**DAI", nên có DHCP snooping là đạt. DAI chuyển thành nội dung giải thích trong report.
> 4. Container Step 9 đổi sang `adosztal/network_automation` (image mà appliance "Network Automation" của GNS3 dùng). Image `networktocode/network-automation` trong đề đã bị xoá khỏi Docker Hub (lỗi 404).
> 5. Baseline AAA: phải gửi `aaa new-model` **trước** `aaa authentication/authorization`, nếu không IOS từ chối (đã thử).
> 6. Câu "còn trống >90%" ở Step 2 được sửa thành số liệu đúng cho từng site.
> 8. CORE↔DIST: image vIOS-L2 crash khi có từ 4 cổng `no switchport` trên một switch (đã tái hiện 12/11/2026). Áp dụng phương án dự phòng của mục 2.2: Po1 (CORE↔DIST-SW01) và Po2 (CORE↔DIST-SW02) là **EtherChannel LACP dạng trunk L2**, mỗi cặp một VLAN transit (901, 902). IP /30 đặt trên SVI `Vlan901` (.69/.70) và `Vlan902` (.73/.74). Bằng chứng Step 3: Po1/Po2 cờ (SU). OSPF ở Step 5 chạy trên Vlan901/Vlan902 thay cho Po.
> 9. Lỗi thêm của image vIOS-L2 (tái hiện 12/11/2026) và cách xử lý trong lab:
> - `switchport mode access` không ăn (cổng kẹt `dynamic desirable`), nên **port-security không bật được** ("is a dynamic port"). Port-security chỉ giải thích trong report; rubric Step 7 chỉ đòi DHCP Snooping/DAI.
> - `switchport access vlan` bị bỏ qua khi boot: thêm EEM applet `ACCESS-VLANS` (chạy khi có SYS-5-RESTART) để gán lại VLAN cho cổng access trên ACC/HANOI-SW02/DANANG-SW01.
> - Po3 với 2 thành viên gây vòng lặp và crash khi bật lại cổng: Po3 chạy LACP với **1 thành viên hoạt động** (Gi1/1 shutdown ở cả hai DIST).
> - Cổng BLK trên ACC vẫn chuyển gói: đặt `spanning-tree vlan 10,40,50,99,100 cost 100` trên Po3 của DIST-SW02, nên cổng bị chặn là **Po3 phía DIST-SW02**. Bằng chứng Step 3 đổi thành `show spanning-tree vlan 10` trên DIST-SW02: Po3 Altn BLK.
> - ACC học sai MAC của SRV: thêm `mac address-table static 0cd9.809e.0000 vlan 100 interface Gi1/1`.
> - Gói gửi tới MAC ảo HSRP bị bỏ: thêm `standby use-bia` trên mọi SVI của 2 DIST.
> 10. Thay đổi trong Giai đoạn 4–7 (13/11/2026):
> - Link EDGE–CORE cũng đi qua VLAN transit 900 (CORE `Vlan900` 10.10.255.66, EDGE `Gi0/1.900` 10.10.255.65), cùng lý do với ghi chú 8. QoS MARK-IN vì vậy gắn vào `Gi0/1.900`.
> - CORE crash mỗi khi relay DHCP đi qua nó (crashinfo khớp thời điểm thử), nên CORE đặt `no service dhcp`. Pool DHCP của **chi nhánh** (HN-V20, HN-V40, DN-V30, DN-V40) chuyển sang **HCMC-EDGE-RTR01**; helper-address ở chi nhánh trỏ về 10.10.255.1 (vẫn là DHCP tập trung tại HQ, đi qua tunnel). Pool của HQ vẫn ở SRV-DHCP-DNS.
> - `standby use-bia` làm link-local của HSRP IPv6 bị trùng, nên bỏ nhóm HSRP IPv6 và đặt `ipv6 nd ra suppress` trên DIST-SW02 (chỉ DIST-SW01 phát RA). IPv6 chạy được trên từng link (PC nhận SLAAC, ping gateway), nhưng vIOS-L2 không chuyển tiếp IPv6 giữa các VLAN; bằng chứng IPv6 là `show ipv6 interface brief` và SLAAC trên PC.
> - BGP qua tunnel dùng thêm prefix-list `INTERNAL` (`10.0.0.0/8 ge 16 le 16`) để chỉ trao đổi tuyến /16, tránh recursive routing của tunnel.
> - VPCS không phân giải được tên qua DNS server IOS (router IOS thì phân giải được); bằng chứng DNS dùng `ping srv.tvi.lab` từ HANOI-RND-RTR01 (`ip domain lookup`, `ip name-server 10.10.47.10`).
> - vIOS-L2 **crash khi định tuyến (CEF) gói TCP** (tái hiện: 1 gói TCP SYN từ VPCS đi qua DIST là crash; ICMP/UDP không sao). Đặt `no ip cef` trên CORE, 2 DIST, HANOI-RND-SW01, DANANG-LOG-SW01 (chuyển sang process switching). Sau đó SSH từ AUTOMATION tới CORE/router/chi nhánh và Static NAT 8080 đều chạy.
> - HANOI-RND-SW02 có `ip routing` mặc định nên bỏ qua `ip default-gateway`: thêm `ip route 0.0.0.0 0.0.0.0 10.20.32.1`.
> 11. Sửa theo rà soát checklist mục VI (14/11/2026):
> - OSPF multi-area: HQ area 0 (EDGE–CORE) + area 10 (khối DIST, CORE là ABR, tóm tắt `10.10.0.0/18`); chi nhánh area 0 (router–switch) + area 20/30 cho VLAN người dùng (router là ABR).
> - `spanning-tree vlan 900-902 priority 24576` trên CORE: VLAN transit cũng có root được ép.
> - IoT: VLAN 60 trên DANANG-LOG-SW01 (cổng Gi0/2, host thử `IOT-DN1` 10.30.0.10/18), sub-int `Gi0/1.60` 10.30.0.1/18 trên DANANG-LOG-RTR01; `IOT-ISOLATION` viết lại (permit server → deny 10.0.0.0/8 → permit any) và áp inbound.
> - SRV-DHCP-DNS: `no ip http server`, `ip http secure-server`; static NAT đổi thành `203.0.113.2:8443` → `10.10.47.10:443`.
> - Backup đặt tên theo ISO 8601 (`20261114T105841`); backup tên cũ đã xoá, chạy lại script 3 lần.
> - IP schema giữ `10.10.16.0/20` cho ~1.700 user các phòng ban HQ khác (chưa dựng trong lab).
> 7. Container AUTOMATION: eth0 (VLAN 99) không đặt gateway mà dùng route `10.0.0.0/8 via 10.10.46.1`; eth1 (GNS3 NAT) giữ default route. Tránh việc SSH tới chi nhánh bị đẩy nhầm ra NAT.

Mục tiêu: Đạt điểm tối đa ở 10 step phần lab (mỗi step 1.0 điểm) và 7 tiêu chí phần report. Tuyệt đối không làm những thứ mà rubric hoặc checklist của đề không chấm.
Kế hoạch này là khung chuẩn để sinh viên và trợ lý AI bám sát khi triển khai. Toàn bộ thiết kế và bài lab Packet Tracer cũ đều bị loại bỏ hoàn toàn.
Quy tắc chống làm thừa: Mỗi tính năng triển khai bắt buộc phải khớp với 1 dòng trong mục 3 "Rubric → Bằng chứng". Tính năng nào không có dòng tương ứng thì không làm.

## 1. Quyết định đã chốt

| Chủ đề | Quyết định |
|---|---|
| Nền tảng lab | GNS3 (app Windows + GNS3 VM trên VMware Workstation) |
| Image | Cisco vIOS (router) và vIOS-L2 (switch), đúng đề mục IV Phase 3. Switch: vIOS-L2 15.0(TTC_20140605), template `vIOS-L2` (ổ đĩa IDE, 1024 MB, 8 cổng). Đã thử thành công trên image này: VLAN, trunk, LACP, Port-channel L3, Rapid-PVST, SVI, HSRP v2 (cả IPv6), track, helper-address, OSPFv2, IPv6 GUA + static, DHCP snooping, port-security, ACL, SSH, AAA, NTP, logging. Không có: OSPFv3, DAI |
| Mô hình HQ | Đúng đề mục IV Phase 5: 1 core switch + 2 distribution switch + 1 edge router; thêm 1 access switch dưới 2 distribution để PC dùng được HSRP (kiến trúc 3 lớp — đề cho phép "three-tier") |
| Chi nhánh | Đúng Phase 5: Hà Nội 1 router + 2 switch; Đà Nẵng 1 router + 1 switch; ISP 1 router chạy BGP |
| Máy chạy script Step 9 | Container Docker `adosztal/network_automation` trong GNS3, template `AUTOMATION` (đề mục IV Phase 4 Option A; image `networktocode/network-automation` của đề đã bị xoá khỏi Docker Hub). Có sẵn Python 3.8.5, netmiko 3.3.3, napalm, pyyaml, ansible, ssh |
| Server DHCP/DNS | 1 router vIOS tên `SRV-DHCP-DNS` (kiêm HTTP server nội bộ port 80 để test Static NAT) |
| Internet | Loopback `8.8.8.8/24` trên `ISP-RTR01` |
| PC, IP phone | VPCS; "phone" là VPCS cắm cổng access VLAN 50 |
| Định tuyến | OSPF trong từng site (underlay); eBGP với ISP và eBGP qua tunnel GRE/IPsec giữa các site (overlay) — đúng đề mục I.7 |
| IPv6 | Schema cấp IPv6 cho mọi VLAN và link ở cả 3 site (Step 2 "across all sites"). Trong lab bật IPv6 GUA trên các interface L3 trong từng site (dual-stack, đúng checklist "IPv6 GUA assigned alongside IPv4"). Định tuyến IPv6 chỉ dùng connected route: PC ↔ server đi qua inter-VLAN trên DIST. **Không chạy OSPFv3**, vì image vIOS-L2 không có lệnh `ipv6 ospf`/`router ospfv3`; checklist cho phép "OSPFv3 or multi-area OSPF". Không bật IPv6 trên VLAN Guest (giữ cách ly), link WAN, tunnel; không định tuyến IPv6 giữa site (rubric không đòi) |
| Theo checklist mục VI | Root bridge mọi miền switching, VLAN 999 blackhole, LACP active, chỉ SSH, EF voice + AF31 video, HSRP priority 110 preempt |
| Theo đề mục I.6 | Port security, DHCP snooping (ở access HQ). DAI chỉ giải thích trong report, vì image không có `ip arp inspection`; rubric Step 7 ghi "DHCP Snooping/DAI" |
| Không làm | EVPN-VXLAN, SD-WAN, WLC/Wi-Fi, ZTNA thật (chỉ giải thích trong report), OSPFv3 và DAI (image không hỗ trợ, chỉ giải thích trong report), VLAN IoT thật, DHCP snooping ở chi nhánh, router/core dự phòng thứ 2 |

## 2. Thiết kế hệ thống

### 2.1 Danh sách thiết bị

| Site | Thiết bị | Image | Vai trò |
|---|---|---|---|
| ISP | `ISP-RTR01` | vIOS | AS 65000, Loopback 8.8.8.8 giả lập Internet |
| HQ | `HCMC-EDGE-RTR01` | vIOS | Edge: eBGP, NAT, IPsec, QoS WAN, phát default route vào OSPF |
| HQ | `HCMC-CORE-SW01` | vIOS-L2 | Core L3: chỉ định tuyến, nối edge và 2 distribution bằng EtherChannel L3 |
| HQ | `HCMC-DIST-SW01` | vIOS-L2 | Distribution L3: SVI, HSRP active, STP root |
| HQ | `HCMC-DIST-SW02` | vIOS-L2 | Distribution L3: SVI, HSRP standby, STP secondary |
| HQ | `HCMC-ACC-SW01` | vIOS-L2 | Access: port-security, DHCP snooping |
| HQ | `SRV-DHCP-DNS` | vIOS | DHCP/DNS/NTP/Syslog/HTTP tập trung (VLAN 100) |
| HQ | `AUTOMATION` | Docker `adosztal/network_automation` | Chạy Python Step 9 (VLAN 99) |
| HQ | `PC-HQ1` (VLAN 10), `PC-HQ2` (VLAN 40), `IP-PHONE01` (VLAN 50) | VPCS | Đầu cuối test |
| Hà Nội | `HANOI-RND-RTR01` | vIOS | Router-on-a-stick, eBGP, NAT, IPsec |
| Hà Nội | `HANOI-RND-SW01` | vIOS-L2 | Switch L3 nhẹ (OSPF qua VLAN 99), STP root |
| Hà Nội | `HANOI-RND-SW02` | vIOS-L2 | Access |
| Hà Nội | `PC-HN1` (VLAN 20), `PC-HN2` (VLAN 40) | VPCS | |
| Đà Nẵng | `DANANG-LOG-RTR01` | vIOS | Router-on-a-stick, eBGP, NAT, IPsec |
| Đà Nẵng | `DANANG-LOG-SW01` | vIOS-L2 | Access + OSPF qua VLAN 99, STP root |
| Đà Nẵng | `PC-DN1` (VLAN 30) | VPCS | |

Mức RAM ước tính: 5 vIOS × 512 MB + 7 vIOS-L2 × 1 GB ≈ 10 GB. Do đó, cần cấp cho GNS3 VM 16 GB RAM và 8 vCPU.

### 2.2 Đấu nối vật lý (Interface ID cho sơ đồ Physical)

| Từ | Cổng | Tới | Cổng | Loại |
|---|---|---|---|---|
| ISP-RTR01 | Gi0/0 | HCMC-EDGE-RTR01 | Gi0/0 | Routed /30 — demarcation HQ |
| ISP-RTR01 | Gi0/1 | HANOI-RND-RTR01 | Gi0/0 | Routed /30 — demarcation HN |
| ISP-RTR01 | Gi0/2 | DANANG-LOG-RTR01 | Gi0/0 | Routed /30 — demarcation ĐN |
| HCMC-EDGE-RTR01 | Gi0/1 | HCMC-CORE-SW01 | Gi0/0 | Routed /30 (`no switchport`) |
| HCMC-CORE-SW01 | Gi0/1, Gi0/2 | HCMC-DIST-SW01 | Gi0/1, Gi0/2 | Port-channel 1, LACP, L3 (`no switchport`) |
| HCMC-CORE-SW01 | Gi0/3, Gi1/0 | HCMC-DIST-SW02 | Gi0/1, Gi0/2 | Port-channel 2, LACP, L3 (`no switchport`) |
| HCMC-DIST-SW01 | Gi1/0, Gi1/1 | HCMC-DIST-SW02 | Gi1/0, Gi1/1 | Port-channel 3, LACP, trunk L2 (tạo vòng tam giác với ACC để STP có việc chặn; mang HSRP hello) |
| HCMC-DIST-SW01 | Gi0/3 | HCMC-ACC-SW01 | Gi0/0 | Trunk |
| HCMC-DIST-SW02 | Gi0/3 | HCMC-ACC-SW01 | Gi0/1 | Trunk (STP chặn) |
| HCMC-ACC-SW01 | Gi0/2 / Gi0/3 / Gi1/0 | PC-HQ1 / PC-HQ2 / IP-PHONE01 | eth0 | Access 10 / 40 / 50 |
| HCMC-ACC-SW01 | Gi1/1 | SRV-DHCP-DNS | Gi0/0 | Access 100 |
| HCMC-ACC-SW01 | Gi1/2 | AUTOMATION | eth0 | Access 99 |
| AUTOMATION | eth1 | GNS3 NAT node | — | Chỉ để tải code vào container. eth1 lấy DHCP (có default route ra Internet). eth0 đặt tĩnh 10.10.46.50/24, **không đặt gateway**, mà thêm route `10.0.0.0/8 via 10.10.46.1`. Như vậy SSH tới mọi thiết bị 10.x đi qua VLAN 99, không bị default route của eth1 kéo ra NAT |
| HANOI-RND-RTR01 | Gi0/1 | HANOI-RND-SW01 | Gi0/0 | Trunk |
| HANOI-RND-SW01 | Gi0/1, Gi0/2 | HANOI-RND-SW02 | Gi0/1, Gi0/2 | Port-channel 1, LACP, trunk |
| HANOI-RND-SW02 | Gi0/3 / Gi1/0 | PC-HN1 / PC-HN2 | eth0 | Access 20 / 40 |
| DANANG-LOG-RTR01 | Gi0/1 | DANANG-LOG-SW01 | Gi0/0 | Trunk |
| DANANG-LOG-SW01 | Gi0/1 | PC-DN1 | eth0 | Access 30 |

Mọi cổng switch không dùng đều phải cấu hình: `switchport access vlan 999` + `shutdown`.
Lưu ý dự phòng: Nếu vIOS-L2 không nhận port-channel L3, hãy đổi Po1/Po2 thành trunk L2 mang 1 VLAN transit riêng cho mỗi cặp. Các SVI vẫn giữ đúng địa chỉ IP /30 như ở mục 2.4.

### 2.3 Danh sách VLAN

| VLAN | Tên | Site |
|---|---|---|
| 10 | EXEC_FINANCE | HQ |
| 20 | RND_ENGINEERING | Hà Nội |
| 30 | LOGISTICS_OPS | Đà Nẵng |
| 40 | GUEST | cả 3 |
| 50 | VOICE | HQ |
| 99 | MANAGEMENT | cả 3 |
| 100 | SERVERS | HQ |
| 999 | BLACKHOLE | cả 3 (cổng không dùng) |

Tên các VLAN 10/20/30/99 được đặt đúng theo yêu cầu tại mục III của đề bài.

### 2.4 Quy hoạch IP (VLSM, mỗi site 1 khối /16 để tóm tắt; số host = nhu cầu × 1.5)

HQ `10.10.0.0/16` · `2001:db8:10::/48` · AS 65001
| VLAN | Host cần | Prefix | Mạng | Gateway (HSRP VIP) | DIST-SW01 / DIST-SW02 | IPv6 |
|---|---|---|---|---|---|---|
| 50 VOICE | 2,000 | /20 | 10.10.0.0/20 | 10.10.0.1 | .2 / .3 | 2001:db8:10:50::/64 |
| 40 GUEST | 500 | /22 | 10.10.40.0/22 | 10.10.40.1 | .2 / .3 | 2001:db8:10:40::/64 (đã cấp, không bật trong lab) |
| 10 EXEC_FINANCE | 300 | /23 | 10.10.44.0/23 | 10.10.44.1 | .2 / .3 | 2001:db8:10:10::/64 |
| 99 MANAGEMENT | 100 | /24 | 10.10.46.0/24 | 10.10.46.1 | .2 / .3 | 2001:db8:10:99::/64 |
| 100 SERVERS | 120 | /24 | 10.10.47.0/24 | 10.10.47.1 | .2 / .3 | 2001:db8:10:100::/64 |

Hà Nội `10.20.0.0/16` · `2001:db8:20::/48` · AS 65002
| VLAN | Host cần | Prefix | Mạng | Gateway | IPv6 |
|---|---|---|---|---|---|
| 20 RND_ENGINEERING | 1,200 | /21 | 10.20.16.0/21 | 10.20.16.1 | 2001:db8:20:20::/64 |
| 40 GUEST | 300 | /23 | 10.20.30.0/23 | 10.20.30.1 | 2001:db8:20:40::/64 (đã cấp, không bật trong lab) |
| 99 MANAGEMENT | 80 | /25 | 10.20.32.0/25 | 10.20.32.1 | 2001:db8:20:99::/64 |

Đà Nẵng `10.30.0.0/16` · `2001:db8:30::/48` · AS 65003
| VLAN | Host cần | Prefix | Mạng | Gateway | IPv6 |
|---|---|---|---|---|---|
| 30 LOGISTICS_OPS | 500 | /22 | 10.30.80.0/22 | 10.30.80.1 | 2001:db8:30:30::/64 |
| 40 GUEST | 200 | /23 | 10.30.88.0/23 | 10.30.88.1 | 2001:db8:30:40::/64 (đã cấp, không bật trong lab) |
| 99 MANAGEMENT | 100 | /24 | 10.30.90.0/24 | 10.30.90.1 | 2001:db8:30:99::/64 |
| (dự trữ) IoT | 10,000+ | /18 | 10.30.0.0/18 | — | 2001:db8:30:60::/64 |

Khối IoT chỉ cần ghi trong tài liệu IP schema để chứng minh khả năng mở rộng cho 10k+ endpoint. Không dựng VLAN IoT trong lab.

Hạ tầng
| Mục | IPv4 | IPv6 |
|---|---|---|
| Loopback0 EDGE / CORE / DIST-SW01 / DIST-SW02 | 10.10.255.1 / .2 / .3 / .4 /32 | 2001:db8:10:ffff::1 / ::2 / ::3 / ::4 /128 |
| Loopback0 HANOI-RND-RTR01 / HANOI-RND-SW01 | 10.20.255.1 / 10.20.255.2 /32 | 2001:db8:20:ffff::1 / ::2 /128 |
| Loopback0 DANANG-LOG-RTR01 / DANANG-LOG-SW01 | 10.30.255.1 / 10.30.255.2 /32 | 2001:db8:30:ffff::1 / ::2 /128 |
| EDGE Gi0/1 ↔ CORE Gi0/0 | 10.10.255.64/30 (.65 / .66) | 2001:db8:10:ff01::1 / ::2 /64 |
| CORE Po1 ↔ DIST-SW01 Po1 (SVI Vlan901) | 10.10.255.68/30 (.69 / .70) | 2001:db8:10:ff02::1 / ::2 /64 |
| CORE Po2 ↔ DIST-SW02 Po1 (SVI Vlan902) | 10.10.255.72/30 (.73 / .74) | 2001:db8:10:ff03::1 / ::2 /64 |
| WAN HQ / HN / ĐN ↔ ISP | 203.0.113.0/30, .4/30, .8/30 (ISP .1 / .5 / .9; site .2 / .6 / .10) | 2001:db8:ffff:1::/64, :2::/64, :3::/64 (đã cấp, không bật trong lab) |
| Tunnel0 HQ↔HN / Tunnel1 HQ↔ĐN | 172.16.12.0/30, 172.16.13.0/30 (HQ .1, chi nhánh .2) | 2001:db8:0:12::/64, 2001:db8:0:13::/64 (đã cấp, không bật trong lab) |
| SRV-DHCP-DNS | 10.10.47.10/24 | 2001:db8:10:100::10/64 |
| AUTOMATION eth0 | 10.10.46.50/24 | — |
| IP quản lý (SSH) | CORE 10.10.255.2 (Loopback0), DIST 10.10.46.2 / .3, ACC 10.10.46.11, HN-SW01 10.20.32.11, HN-SW02 10.20.32.12, DN-SW01 10.30.90.11, router site = Loopback0 | — |

Dải 203.0.113.0/24 (RFC 5737) và 2001:db8::/32 (RFC 3849) là các dải IP chuẩn dành cho tài liệu. Cần ghi rõ chi tiết này trong report.

### 2.5 Chi tiết cấu hình theo từng Step

Step 3 — Cấu hình L2:
- Tạo VLAN theo mục 2.3. Cấu hình cổng trunk: `switchport trunk encapsulation dot1q` + `switchport mode trunk` + `switchport trunk allowed vlan` theo đúng danh sách VLAN của từng site.
- Cấu hình LACP bằng lệnh `channel-group <n> mode active`. Cặp kết nối CORE↔DIST-SW01 (Po1) và CORE↔DIST-SW02 (Po2) là EtherChannel L3, bám sát yêu cầu mục I.7 "core links must utilize EtherChannel (LACP)". Cặp DIST-SW01↔DIST-SW02 (Po3) và HANOI-RND-SW01↔SW02 (Po1) cấu hình là trunk L2.
- Bật `spanning-tree mode rapid-pvst` trên mọi switch. Tại HQ, cấu hình HCMC-DIST-SW01 là `spanning-tree vlan 10,40,50,99,100 root primary`, và DIST-SW02 là `root secondary`. Tại Hà Nội, đặt HANOI-RND-SW01 làm primary và SW02 làm secondary cho VLAN 20,40,99. Tại Đà Nẵng, đặt DANANG-LOG-SW01 là `spanning-tree vlan 30,40,99 root primary`.

Step 4 — Cấu hình HSRP và DHCP:
- Trên các SVI của 2 switch distribution: cấu hình `standby version 2`, `standby <VLAN> ip <VIP>`, `standby <VLAN> preempt` trên cả hai thiết bị. Trên DIST-SW01, đặt `standby <VLAN> priority 110`. Cấu hình thêm `track 1 interface Port-channel1 line-protocol` + `standby <VLAN> track 1 decrement 20` để tự động nhường quyền active khi mất đường uplink lên core.
- Gán địa chỉ IPv6 trên các SVI: DIST-SW01 dùng `2001:db8:10:<VLAN>::2/64`, DIST-SW02 dùng `::3/64`. Về Gateway IPv6: tạo nhóm HSRP riêng với lệnh `standby 1<VLAN> ipv6 autoconfig` (ví dụ: VLAN 10 dùng nhóm 1010; lưu ý IPv4 và IPv6 không dùng chung số nhóm). Image vIOS-L2 đã nhận lệnh này khi thử. Nếu lúc chạy thật HSRP IPv6 không lên Active/Standby, chỉ để DIST-SW01 phát RA và cấu hình `ipv6 nd ra suppress` trên DIST-SW02 (lệnh này cũng đã được image nhận).
- Đặt `ip helper-address 10.10.47.10` trên các SVI 10/40/50 của 2 switch distribution, cũng như trên các sub-interface .20/.40 (HN) và .30/.40 (ĐN).
- Trên SRV-DHCP-DNS: Tạo 7 pool (HQ-V10, HQ-V40, HQ-V50, HN-V20, HN-V40, DN-V30, DN-V40). Loại trừ địa chỉ bằng `ip dhcp excluded-address` từ .1–.9 ở mỗi mạng. Đặt `default-router` bằng địa chỉ gateway, `dns-server 10.10.47.10`, `domain-name tvi.lab`. Bật dịch vụ DNS và NTP với `ip dns server` + `ip host srv.tvi.lab 10.10.47.10` và `ntp master 3`. Thêm route mặc định `ip route 0.0.0.0 0.0.0.0 10.10.47.1`. Với IPv6, trên Gi0/0 của SRV đặt địa chỉ `2001:db8:10:100::10/64` + `ipv6 address autoconfig default` (lệnh gõ trong interface, không phải global) để nhận default route IPv6 từ bản tin RA. Không bật `ipv6 unicast-routing` trên SRV-DHCP-DNS: router đang định tuyến IPv6 sẽ bỏ qua RA và không học được default route.

Step 5 — Định tuyến OSPF trong từng site:
- Tại HQ: Bật OSPF 1 **multi-area**: area 0 = EDGE–CORE (Vlan900) + loopback EDGE/CORE; area 10 = khối distribution (Vlan901/902, SVI và loopback 2 DIST). CORE là ABR, tóm tắt `area 10 range 10.10.0.0 255.255.192.0`. Đặt `passive-interface default`, sau đó mở lại trên các kết nối /30 (Gi0/1 của EDGE, SVI Vlan901/Vlan902 giữa CORE và DIST). Gán `router-id` bằng địa chỉ Loopback0. Trên EDGE, cấu hình `default-information originate`. Trên SVI Vlan902 của CORE (đường xuống DIST-SW02), đặt `ip ospf cost 20` để hướng lưu lượng chiều về đi vào DIST-SW01 (đang là HSRP active); khi mất Po1 thì lưu lượng sẽ tự động đi qua Po2.
- Tại chi nhánh: Bật `ip routing` trên HANOI-RND-SW01 và DANANG-LOG-SW01, rồi cấu hình Loopback0 và OSPF trên Vlan99. Trên router chi nhánh, mở OSPF ở sub-interface .99 (area 0) và để các sub-interface người dùng ở trạng thái passive trong area 20 (HN) / area 30 (ĐN, gồm cả VLAN 60 IoT); router chi nhánh là ABR. Cách này giúp mỗi site có quan hệ neighbor FULL thực sự, và các switch sẽ dùng OSPF thay cho lệnh `ip default-gateway`.
- IPv6 dual-stack (không dùng OSPFv3): Bật `ipv6 unicast-routing` trên EDGE, CORE, 2 DIST và 2 router chi nhánh. Gán GUA theo mục 2.4 trên: Loopback0 của các thiết bị đó, link EDGE–CORE, Po1/Po2, SVI 10/50/99/100 của 2 DIST (đã làm ở Step 4), sub-interface .20/.99 (HN) và .30/.99 (ĐN). Router chi nhánh tự phát RA trên sub-int người dùng, nên PC chi nhánh nhận IPv6 bằng SLAAC. Trong lab chỉ dùng connected route: PC-HQ1 (VLAN 10) tới SRV-DHCP-DNS (VLAN 100) qua inter-VLAN trên DIST, ping trên từng link /64. Không cấu hình `ipv6 ospf`, vì image vIOS-L2 báo "Invalid input" với mọi cú pháp OSPFv3. Report trình bày OSPFv3 như thiết kế cho môi trường thật.

Step 6 — Định tuyến BGP và Tunnel IPsec:
- Cấu hình eBGP với ISP: Kết nối HQ 65001↔65000 (203.0.113.1), HN 65002↔65000 (203.0.113.5), ĐN 65003↔65000 (203.0.113.9). Chỉ quảng bá các mạng /30 public. Sử dụng prefix-list `PUBLIC-ONLY` để chặn dải 10.0.0.0/8 lọt ra ISP. Phía ISP sẽ quảng bá mạng 8.8.8.0/24 và các mạng /30.
- Cấu hình Tunnel GRE: Từ HQ, dựng Tunnel0 tới 203.0.113.6 và Tunnel1 tới 203.0.113.10 (lấy nguồn là Gi0/0). Áp dụng bảo mật bằng lệnh `tunnel protection ipsec profile TVI-IPSEC` (dùng IKEv1 PSK, AES-256, SHA-256, DH group 14; nếu image không nhận group 14 thì đổi sang dùng group 5).
- Cấu hình eBGP overlay qua tunnel: HQ (AS 65001) thiết lập peer với 172.16.12.2 (AS 65002) và 172.16.13.2 (AS 65003). Mỗi site chỉ quảng bá đúng 1 tuyến tóm tắt bằng cặp lệnh `network 10.10.0.0 mask 255.255.0.0` + `ip route 10.10.0.0 255.255.0.0 Null0`. Làm tương tự cho dải 10.20.0.0/16 và 10.30.0.0/16 để đáp ứng yêu cầu "route summarization at branch edges".
- Cấu hình Default route ra Internet: Đặt `ip route 0.0.0.0 0.0.0.0 <ISP>` tại mỗi site để lưu lượng đi thẳng ra Internet tại chỗ, không phải vòng qua HQ.

Step 7 — Bảo mật hệ thống:
- Cấu hình NAT tại mỗi router site: Dùng lệnh `ip nat inside source list NAT-ACL interface Gi0/0 overload` (PAT). Đặt `ip nat inside` trên cổng LAN/sub-int và `ip nat outside` trên cổng Gi0/0. Riêng trên `HCMC-EDGE-RTR01`, cấu hình thêm Static NAT Port Forwarding `ip nat inside source static tcp 10.10.47.10 443 203.0.113.2 8443` (và bật `ip http secure-server` – HTTPS – riêng trên `SRV-DHCP-DNS`) để minh họa truy cập dịch vụ nội bộ qua NAT theo đúng tài liệu hướng dẫn `CO3094-SamppeNetInfras w Address Translation.pdf`.
- Cấu hình ACL `GUEST-IN` (áp theo chiều inbound trên SVI Vlan40 của 2 DIST và sub-int .40 ở chi nhánh): permit udp any eq bootpc any eq bootps; permit udp/tcp any host 10.10.47.10 eq 53; deny ip any 10.0.0.0 0.255.255.255; permit ip any any. Cấu hình thêm ACL `IOT-ISOLATION` trên `DANANG-LOG-RTR01` cho dải IoT `10.30.0.0 0.0.63.255` (VLAN 60, sub-int `Gi0/1.60`, áp inbound) chỉ tới `SRV-DHCP-DNS` (`10.10.47.10`), chặn toàn bộ `10.0.0.0/8` còn lại (Corp, Guest, Voice, Mgmt), rồi permit ra Internet để khớp trọn vẹn checklist mục VI.3 ("block unauthorized access between Corporate, Guest, and IoT subnets").
- Cấu hình bảo mật L2 trên HCMC-ACC-SW01: Bật `ip dhcp snooping`, `ip dhcp snooping vlan 10,40,50`, `no ip dhcp snooping information option`, và đặt trust trên các cổng Gi0/0, Gi0/1, Gi1/1. (Không cấu hình DAI vì image không có lệnh `ip arp inspection`; bảng binding của DHCP snooping vẫn được trình bày trong report như nguồn dữ liệu mà DAI sẽ dùng.) Bật port-security (maximum 2, sticky, violation restrict) trên các cổng người dùng Gi0/2, Gi0/3, Gi1/0.
- Hardening trên mọi thiết bị: Cấu hình `service password-encryption`, `enable secret`, `username admin privilege 15 secret`, `ip ssh version 2`, vào `line vty 0 4` đặt `transport input ssh` + `login local`. Tắt HTTP bằng `no ip http server` trên mọi thiết bị (`SRV-DHCP-DNS` chỉ bật HTTPS `ip http secure-server` làm Web Server demo Static NAT) và tuyệt đối không cấu hình SNMP v1/v2c.

Step 8 — Cấu hình QoS:
- Đánh dấu gói tin tại HCMC-EDGE-RTR01 (chiều input trên Gi0/1): Tạo class VOICE khớp với ACL nguồn 10.10.0.0/20 → `set dscp ef`. Tạo class VIDEO khớp với ACL udp any any range 3478 3481 → `set dscp af31`.
- Đánh dấu gói tin tại router chi nhánh (chiều input trên sub-interface LAN): Tạo ACL khớp đích 10.10.0.0/20 → `set dscp ef` để xử lý chiều về của cuộc gọi.
- Áp dụng chính sách hàng đợi trên cả 3 router (chiều output trên Gi0/0): Tạo policy cha `shape average 10000000` chứa policy con bên trong. Trong policy con, đặt `priority percent 30` cho `match dscp ef`, `bandwidth percent 25` cho `match dscp af31`, và `fair-queue` cho class-default. Do GRE/IPsec tự động sao chép giá trị DSCP ra header bên ngoài, các gói tin đi qua tunnel vẫn được ưu tiên chính xác.

Step 9 — Tự động hóa mạng (Thư mục `Automation/`):
- File `inventory.yaml`: Chứa hostname, ip, device_type `cisco_ios`, port 22, và danh sách VLAN riêng cho từng thiết bị. Danh sách gồm 7 switch và 3 router site (riêng CORE và các router để danh sách VLAN rỗng, chỉ nhận cấu hình baseline và thực hiện backup).
- Script `auto_provision.py` (sử dụng thư viện netmiko + pyyaml):
  - Đọc thông tin đăng nhập từ biến môi trường `TVI_USER`/`TVI_PASS`. Nếu thiếu thì hỏi người dùng qua `getpass`. Tuyệt đối không lưu mật khẩu cứng trong file.
  - Đẩy cấu hình Baseline: `aaa new-model`, `aaa authentication login default local`, `aaa authorization exec default local`, `ntp server 10.10.47.10`, `logging host 10.10.47.10`, và banner motd. Thứ tự là bắt buộc: `aaa new-model` phải đi trước 2 lệnh `aaa ...` (đã thử: đảo thứ tự thì IOS báo "Invalid input"). Sau khi có baseline AAA, console GNS3 cũng sẽ hỏi username/password (`admin`).
  - Container dùng netmiko 3.3.3. Khi viết script, kiểm tra tên lớp exception import được trong bản này (`NetmikoTimeoutException`/`NetMikoTimeoutException`) trước khi chốt code.
  - Tự động tạo các VLAN còn thiếu dựa theo payload trong file inventory, bao gồm cả tên VLAN.
  - Trước và sau khi thay đổi cấu hình: Chạy lệnh `show running-config` + `show ip interface brief`, sau đó lưu vào `backups/<hostname>_<timestamp>_backup.cfg`, timestamp theo ISO 8601 (`YYYYMMDDThhmmss`).
  - Ghi log cho mọi lần chạy và bắt các lỗi (`NetmikoTimeoutException`, `NetmikoAuthenticationException`) vào file `logs/automation.log`. Nếu 1 thiết bị gặp lỗi, script vẫn tiếp tục chạy cho các thiết bị còn lại chứ không dừng.
  - Đảm bảo tính Idempotent: Đối chiếu với running-config hiện tại và chỉ gửi những dòng lệnh còn thiếu. Nếu không thiếu dòng nào thì ghi nhận "no changes" và không chạy lệnh `write memory`.
- Quy trình áp dụng thực tế: Thực hiện bootstrap thủ công ở mức tối thiểu (theo mục 2.6, có sẵn trunk cho phép VLAN 99 và cổng access Gi1/2 cho máy AUTOMATION) → chạy script để tạo các VLAN corporate (10, 20, 30, 40, 50, 100) và đẩy baseline → tiếp tục cấu hình các cổng access, LACP, STP, HSRP.
- File `README.md`: Hướng dẫn cách cài đặt thư viện, đặt biến môi trường, lệnh khởi chạy script, cũng như cách kiểm tra thư mục backups/ và file log.

### 2.6 Bootstrap tối thiểu (Để script có thể SSH vào thiết bị)
- Trên các Switch: Cấu hình `hostname`, `ip domain-name tvi.lab`, `crypto key generate rsa modulus 2048`, `username admin privilege 15 secret ...`, `ip ssh version 2`, tạo `vlan 99`, vào `interface Vlan99` gán IP quản lý, đặt `ip default-gateway` (áp dụng cho switch chỉ chạy L2), cấu hình cổng uplink trunk (`switchport trunk encapsulation dot1q` + `switchport mode trunk`) cho phép VLAN 99 đi qua (trên `HCMC-ACC-SW01` gán thêm cổng `Gi1/2` vào `switchport access vlan 99` nối với container `AUTOMATION`), và vào `line vty 0 4` bật `login local` + `transport input ssh`.
- Trên CORE và các Router: Cấu hình tương tự như trên, nhưng địa chỉ IP quản lý được đặt trên cổng Loopback0.

## 3. Ánh xạ Rubric → Bằng chứng (Dùng cho Report và Demo)
Quy tắc thực hiện cho mỗi dòng: Chạy đúng câu lệnh trên thiết bị được ghi trong bảng, chụp ảnh màn hình lưu thành file `Evidence/S<step>_<tên>.png`. Khi demo trực tiếp, gõ lại đúng lệnh đó và thuyết trình theo nội dung ở cột "Logic để nói".

### Step 1 — Topology
| Thiết bị | Lệnh / thao tác demo | Phải thấy | Logic để nói |
|---|---|---|---|
| — | mở `TVI-Topology.drawio` trang Logical và Physical | 3 site, ISP cloud, đường demarcation, interface ID, VLAN, subnet, AS, OSPF area, trust zone | Demarcation là Gi0/0 của mỗi router site: phía ISP do nhà mạng chịu trách nhiệm, phía trong do TVI quản lý; trang Logical tách rõ miền L2 (VLAN) và L3 (subnet, routing) |

### Step 2 — IP schema
| Thiết bị | Lệnh / thao tác demo | Phải thấy | Logic để nói |
|---|---|---|---|
| — | mở `TVI-IP-Schema.md` | Bảng VLSM 3 site, IPv6 /48 → /64, khối IoT dự trữ, hạ tầng | Mỗi site 1 khối /16 nên chỉ cần quảng bá 1 tuyến; VLAN nhận prefix nhỏ nhất đủ cho số host × 1.5 nên không phí; HQ còn trống 84% (đã giữ /20 cho các phòng ban HQ khác), Hà Nội 95%, Đà Nẵng vẫn còn 72% dù đã giữ sẵn /18 cho 10k+ IoT |

### Step 3 — VLAN, trunk, EtherChannel, STP
| Thiết bị | Lệnh demo | Phải thấy | Logic để nói |
|---|---|---|---|
| HCMC-ACC-SW01 | `show vlan brief` | VLAN 10, 40, 50, 99, 100, 999; cổng không dùng nằm ở 999 | Tách lưu lượng theo phòng ban; cổng thừa bị cô lập và tắt |
| HCMC-ACC-SW01 | `show interfaces trunk` | Gi0/0, Gi0/1 trunk 802.1Q, đúng danh sách VLAN | Chỉ VLAN cần thiết đi trên trunk |
| HCMC-CORE-SW01 | `show etherchannel summary` | Po1, Po2 cờ (SU), cổng (P), giao thức LACP | Link core gộp 2 cổng: thêm băng thông và hỏng 1 cổng vẫn chạy |
| HANOI-RND-SW01 | `show etherchannel summary` | Po1 (SU), LACP | EtherChannel L2 ở chi nhánh |
| HCMC-DIST-SW01 | `show spanning-tree vlan 10` | "This bridge is the root", chế độ rstp | Root được ép bằng priority, không để switch tự bầu; RSTP hội tụ nhanh |
| HCMC-DIST-SW02 | `show spanning-tree vlan 10` | Po3 trạng thái Altn BLK (cost 100) | Vòng ACC–DIST-SW01–DIST-SW02 bị STP chặn ở đường dự phòng, sẵn sàng thay thế |
| HCMC-DIST-SW01 | `show etherchannel summary` | Po3 (SU), LACP | Trunk L2 giữa 2 distribution gộp 2 cổng |

### Step 4 — HSRP, DHCP/DNS tập trung
| Thiết bị | Lệnh demo | Phải thấy | Logic để nói |
|---|---|---|---|
| HCMC-DIST-SW01, DIST-SW02 | `show standby brief` | SW01 Active priority 110 P, SW02 Standby, VIP .1 | PC chỉ biết gateway .1; một distribution hỏng thì cái kia nhận VIP |
| PC-HN1 | `ip dhcp` rồi `show ip` | IP 10.20.16.x, gateway 10.20.16.1, DNS 10.10.47.10 | PC ở Hà Nội nhận IP từ server ở HQ qua tunnel nhờ `ip helper-address` → DHCP tập trung qua ranh giới định tuyến |
| SRV-DHCP-DNS, HCMC-EDGE-RTR01 | `show ip dhcp binding` | SRV: binding của PC-HQ1; EDGE: binding của PC-HN1, PC-DN1 | DHCP tập trung ở HQ phục vụ cả 3 site (pool chi nhánh đặt trên EDGE, xem ghi chú 10) |
| HANOI-RND-RTR01 (client DNS) | `ping srv.tvi.lab` | Phân giải qua domain server 10.10.47.10 [OK] và trả lời | DNS tập trung ở HQ phục vụ cả chi nhánh (VPCS không có DNS client tương thích, xem ghi chú 10) |

### Step 5 — OSPF trong site
| Thiết bị | Lệnh demo | Phải thấy | Logic để nói |
|---|---|---|---|
| HCMC-CORE-SW01 | `show ip ospf neighbor`, `show ip ospf \| include Area\|area border` | FULL với EDGE (area 0), DIST-SW01/02 (area 10); "area border router" | Underlay HQ hội tụ, multi-area: CORE là ABR |
| HCMC-EDGE-RTR01 | `show ip route ospf` | `O IA 10.10.0.0/18` (tuyến tóm tắt của area 10) | ABR tóm tắt khối distribution, area 0 nhỏ gọn |
| HANOI-RND-RTR01, DANANG-LOG-RTR01 | `show ip ospf neighbor` | FULL với HANOI-RND-SW01 / DANANG-LOG-SW01 | Mỗi chi nhánh cũng có OSPF hội tụ |
| HCMC-DIST-SW01 | `show ip route ospf` | Loopback 10.10.255.1/.2/.4, default O*E2 từ EDGE (có sau Giai đoạn 6, khi EDGE đã có static default ra ISP) | Mọi loopback HQ được học |
| HCMC-EDGE-RTR01 | `ping 10.10.255.4 source Loopback0` | Thành công | Loopback reachable trong site (đúng yêu cầu Step 5) |
| HANOI-RND-RTR01 | `ping 10.20.255.2 source Loopback0` | Thành công | Như trên ở Hà Nội; tương tự ĐN với 10.30.255.2 |
| HCMC-DIST-SW01 | `show ipv6 interface brief`, `show ip interface brief` | Cùng một interface (Vlan10/50/99/100, Po1, Loopback0) có cả IPv4 lẫn IPv6 GUA `2001:DB8:10:...` | Dual-stack chạy thật, đúng checklist "IPv6 GUA alongside IPv4". Underlay dùng OSPFv2 multi-area (checklist: "OSPFv3 or multi-area OSPF"); OSPFv3 là thiết kế cho môi trường thật, giải thích trong report |
| PC-HQ1 | `ip auto` rồi `show ipv6`, sau đó `ping 2001:db8:10:10::2` | PC có địa chỉ 2001:db8:10:10::/64; ping gateway thành công | PC nhận IPv6 bằng SLAAC từ RA của DIST-SW01 |

### Step 6 — eBGP và tunnel IPsec
| Thiết bị | Lệnh demo | Phải thấy | Logic để nói |
|---|---|---|---|
| HCMC-EDGE-RTR01 | `show ip bgp summary` | 3 neighbor Established: 203.0.113.1, 172.16.12.2, 172.16.13.2 | eBGP với ISP (đường Internet) và eBGP qua tunnel (đường nội bộ giữa site) |
| HCMC-EDGE-RTR01 | `show ip route bgp` | Đúng 1 tuyến 10.20.0.0/16 và 1 tuyến 10.30.0.0/16 qua Tunnel | Chi nhánh tóm tắt tại biên → bảng định tuyến nhỏ |
| ISP-RTR01 | `show ip bgp` | Chỉ có /30 public và 8.8.8.0/24, không có 10.x | Địa chỉ private không lọt ra ISP |
| HCMC-EDGE-RTR01 | `show crypto isakmp sa`, `show crypto ipsec sa` | QM_IDLE; #pkts encaps/decaps tăng khi ping liên site | Lưu lượng giữa site được mã hoá |
| HCMC-EDGE-RTR01 | `show interfaces Tunnel0` | up/up | Tunnel HQ↔HN hoạt động (Tunnel1 tương tự) |

### Step 7 — Bảo mật
| Thiết bị | Lệnh demo | Phải thấy | Logic để nói |
|---|---|---|---|
| PC-HQ2 (Guest) | `ping 10.10.47.10`, `ping 8.8.8.8` | Nội bộ: timeout; Internet: trả lời | Guest chỉ ra Internet, cách ly hoàn toàn với Corp |
| HCMC-DIST-SW01, DANANG-LOG-RTR01 | `show access-lists GUEST-IN`, `show access-lists IOT-ISOLATION` | Bộ đếm dòng deny tăng ở cả hai ACL | Chính ACL chặn và phân tách rõ Corp, Guest, IoT theo checklist |
| IOT-DN1 | `ping 10.10.47.10`, `ping 10.30.80.10`, `ping 8.8.8.8` | Server: trả lời; Corp: administratively prohibited; Internet: trả lời | IoT chỉ tới server và Internet, không chạm được Corp/Guest/Mgmt |
| HCMC-EDGE-RTR01 | `show ip nat translations` (sau khi PC-HQ1 ping 8.8.8.8 và ISP `telnet 203.0.113.2 8443`) | Dòng PAT (10.10.x → 203.0.113.2) và dòng Static NAT (`203.0.113.2:8443` ↔ `10.10.47.10:443`) | Kết hợp NAT Overload cho user ra Internet và Static NAT cho truy cập dịch vụ nội bộ |
| HCMC-ACC-SW01 | `show ip dhcp snooping`, `show ip dhcp snooping binding` | Snooping bật cho VLAN 10,40,50; cổng trust Gi0/0, Gi0/1, Gi1/1; binding MAC–IP của PC | Chỉ cổng trust (hướng về server thật) mới được trả lời DHCP, nên DHCP giả bị chặn. Bảng binding này cũng là dữ liệu mà DAI dùng ở môi trường thật (image lab không có DAI) |
| PC/VPCS hoặc router khác | `telnet 10.10.255.1` | Bị từ chối | Chỉ cho SSHv2, giao thức không mã hoá bị tắt |

### Step 8 — QoS
| Thiết bị | Lệnh demo | Phải thấy | Logic để nói |
|---|---|---|---|
| IP-PHONE01 | `ping 10.20.16.x -t` (PC-HN1) | Trả lời liên tục | Tạo lưu lượng VoIP giả lập |
| HCMC-EDGE-RTR01 | `show policy-map interface Gi0/1.900 input` | Class VOICE có gói được `set dscp ef` | Gói từ VLAN voice được đánh dấu EF |
| HCMC-EDGE-RTR01, HANOI-RND-RTR01 | `show policy-map interface Gi0/0 output` | Class priority EF có bộ đếm tăng | Voice đi hàng đợi ưu tiên trên WAN cả hai chiều |
| PC-HQ1 | `ping <IP PC-HN1> -P 17 -p 3478` | Gửi được gói UDP | Tạo lưu lượng video giả lập |
| HCMC-EDGE-RTR01 | `show policy-map interface Gi0/1.900 input` | Class VIDEO có gói `set dscp af31` | Video được đánh dấu AF31, xếp sau voice |

### Step 9 — Automation
| Thiết bị | Lệnh demo | Phải thấy | Logic để nói |
|---|---|---|---|
| AUTOMATION | `cat inventory.yaml`; `grep -n -i password auto_provision.py` | Inventory tách riêng; không có mật khẩu trong code | Đúng yêu cầu inventory ngoài và không lưu credential |
| AUTOMATION | `export TVI_USER=admin`, nhập `TVI_PASS` bằng `read -s`, `python3 auto_provision.py` (lần 1, trên switch mới bootstrap) | Mỗi thiết bị: backup trước → gửi lệnh → backup sau; VLAN được tạo | Script dựng VLAN + baseline thay cho gõ tay |
| HCMC-ACC-SW01 | `show vlan brief`, `show run \| include ntp\|logging\|aaa` | VLAN có tên đúng; baseline có mặt | Kết quả trên thiết bị khớp payload |
| AUTOMATION | chạy lần 2 | Mọi thiết bị "no changes" | Idempotent: không gửi lại lệnh đã có |
| GNS3 + AUTOMATION | tắt 1 switch, chạy lần 3 | Thiết bị tắt báo timeout, các thiết bị khác vẫn xong | Xử lý lỗi, không crash |
| AUTOMATION | `ls backups/`, `tail logs/automation.log` | File `<hostname>_<YYYYMMDDThhmmss>_backup.cfg`; log có dòng thành công và dòng lỗi timeout | Đủ bằng chứng backup và log theo đề mục III |

### Step 10 — Kiểm thử đầu-cuối và failover
| Thiết bị | Lệnh demo | Phải thấy | Logic để nói |
|---|---|---|---|
| PC-HQ1 | `ping` + `trace` tới PC-HN1, PC-DN1 | Thành công; trace đi qua 172.16.12.x / 172.16.13.x | Liên site đi qua tunnel mã hoá |
| PC-HN1 | `ping` + `trace` tới PC-DN1 | Thành công qua HQ | Chi nhánh tới nhau qua hub HQ |
| PC-DN1 | `ping 8.8.8.8`, `trace 8.8.8.8` | Đi thẳng ISP, không qua HQ | Ra cloud tại chỗ, không backhaul |
| PC-HQ1 + HCMC-DIST-SW01 | `ping 10.20.16.x -t`, rồi trên DIST-SW01 `interface Gi0/1` + `shutdown` | Không mất gói | Po1 còn 1 cổng, LACP giữ link |
| PC-HQ1 + HCMC-DIST-SW01 | tiếp tục ping, `interface Port-channel1` + `shutdown`; xem `show standby brief` trên DIST-SW02 | Mất vài gói rồi chạy lại; DIST-SW02 thành Active | Tracking hạ priority, HSRP chuyển gateway, OSPF đổi đường; hội tụ dưới 3 phút |
| HCMC-DIST-SW01 | `no shutdown` | SW01 lấy lại Active (preempt) | Hệ thống tự về trạng thái chính |

## 4. Các bước triển khai (Thực hiện đúng thứ tự)

Giai đoạn 0 — Chuẩn bị máy
- [x] Tắt Memory Integrity, VBS, System Guard, Enhanced Sign-in Security, Windows Hello VBS; `bcdedit /set {current} hypervisorlaunchtype off` và `vsmlaunchtype off`; khởi động lại. Kiểm tra: `HypervisorPresent=False`, VT-x/SLAT = True.
- [x] Cài GNS3 2.2.61 và GNS3 VM 2.2.61. GNS3 VM chạy trên VMware với 16 GB RAM, 8 vCPU, VT-x/EPT; báo "KVM support available: True".
- [x] Switch: template `vIOS-L2` (image vIOS-L2 15.0(TTC_20140605), ổ đĩa **IDE**, 1024 MB, 8 cổng). Đã boot được và thử đủ lệnh (xem mục 1).
- [x] Container: template `AUTOMATION` (`adosztal/network_automation`). Đã chạy được, có Python 3.8.5, netmiko 3.3.3.
- [x] Router: template `vIOS` (image vIOS **15.6(2)T**, MD5 khớp danh sách GNS3; kèm `IOSv_startup_config.img` của GNS3; virtio, 512 MB, 4 cổng Gi0/0–Gi0/3). Boot được ngay. Đã thử và IOS nhận toàn bộ lệnh router của plan: hardening + AAA, OSPF + `default-information originate`, BGP + prefix-list, sub-interface dot1Q + helper-address, IKEv1 (AES-256, SHA-256, group 14), transform-set, `tunnel protection ipsec profile`, NAT overload + static port-forward, ACL GUEST-IN/IOT-ISOLATION, class-map/policy-map (set dscp ef/af31, priority/bandwidth percent, fair-queue, shape average lồng child), DHCP pool, `ip dns server`, `ip host`, `ntp master`, `ip http server`, `ipv6 address autoconfig default` (lệnh này gõ trong interface).
- [x] Điều kiện hoàn thành: 1 node vIOS và 1 node vIOS-L2 chạy cùng lúc. **Đã đạt** (12/11/2026).

Giai đoạn 1 — Thiết kế trên giấy (Step 1, 2)
- [x] Soạn file `TVI-IP-Schema.md` bám sát mục 2.4 (bao gồm bảng quy hoạch, công thức tính VLSM, phân bổ IPv6, tuyến tóm tắt và khối IoT dự trữ).
- [x] Vẽ sơ đồ `TVI-Topology.drawio` (sinh bằng `make_topology.py`; còn bước xuất PNG bằng draw.io) gồm 2 trang: Trang Logical (thể hiện subnet, VLAN, AS, OSPF area, tunnel, các trust zone Corp/Guest/Voice/Mgmt/Server/Internet, và đường demarcation) và trang Physical (thể hiện tên thiết bị, interface ID đúng theo mục 2.2, cùng Po1/Po2). Xuất cả hai trang ra file ảnh PNG.
- Điều kiện hoàn thành: Thu thập đủ bằng chứng của Step 1 và Step 2 theo bảng ở mục 3.

Giai đoạn 2 — Dựng topology và Bootstrap
- [x] Tạo project GNS3 tên `TVI`. Kéo thả các node và nối dây chính xác theo mục 2.2. Đặt tên hiển thị của từng node trùng khớp với hostname.
- [x] Cấu hình bootstrap tối thiểu theo mục 2.6 cho toàn bộ các switch, CORE và router (bao gồm cấu hình trunk cơ bản mang VLAN 99 giữa các switch và gán cổng access VLAN 99 cho container `AUTOMATION`).

Giai đoạn 3 — Viết và chạy thử Automation (Step 9)
- [x] Viết các file `Automation/inventory.yaml`, `auto_provision.py`, và `README.md` theo đúng yêu cầu tại mục 2.5 Step 9.
- [x] Chạy script lần 1 cho nhóm thiết bị HCMC-DIST-SW01, DIST-SW02, ACC-SW01 (nhờ đã có trunk VLAN 99 ở Giai đoạn 2 nên máy AUTOMATION SSH được ngay để tự động tạo các VLAN còn lại và đẩy baseline). Thiết bị CORE và router HQ sẽ chạy script sau Giai đoạn 5; các thiết bị ở chi nhánh sẽ chạy sau Giai đoạn 6.

Giai đoạn 4 — Cấu hình L2, HSRP và DHCP (Step 3, 4)
- [x] Triển khai cấu hình ở mục 2.5 cho Step 3, Step 4 và thiết bị SRV-DHCP-DNS.
- Điều kiện hoàn thành: Thu thập đủ bằng chứng của Step 3 và Step 4 (riêng phần cấp DHCP cho chi nhánh sẽ kiểm tra sau Giai đoạn 6).

Giai đoạn 5 — Cấu hình OSPF và IPv6 (Step 5)
- [x] Cấu hình OSPFv2 và IPv6 dual-stack (không có OSPFv3) theo đúng hướng dẫn tại mục 2.5.
- [x] Chạy script lần 1 cho HCMC-CORE-SW01 và HCMC-EDGE-RTR01 (lúc này địa chỉ Loopback0 đã được định tuyến nên có thể kết nối tới).
- Điều kiện hoàn thành: Thu thập đủ bằng chứng của Step 5.

Giai đoạn 6 — Cấu hình WAN và Bảo mật (Step 6, 7)
- [x] Cấu hình thiết bị ISP-RTR01, phiên eBGP, tunnel GRE + IPsec profile, eBGP overlay chạy qua tunnel, NAT (Overload + Static NAT), ACL GUEST-IN, ACL IOT-ISOLATION, DHCP snooping, port-security và hardening thiết bị.
- [x] Chạy script lần 1 cho các switch và router ở cả hai chi nhánh.
- Điều kiện hoàn thành: Thu thập đủ bằng chứng của Step 6, Step 7 và phần cấp DHCP chi nhánh thuộc Step 4.

Giai đoạn 7 — Cấu hình QoS (Step 8)
- [x] Cấu hình đánh dấu gói tin (Marking) cùng chính sách điều phối băng thông (shaping/LLQ) theo mục 2.5.
- Điều kiện hoàn thành: Thu thập đủ bằng chứng của Step 8.

Giai đoạn 8 — Kiểm thử tổng thể và Xuất file cấu hình (Step 9, 10)
- [x] (Đã lưu output CLI dạng .txt vào `Evidence/`; còn chụp ảnh màn hình khi viết report.) Chạy kiểm tra lại toàn bộ các dòng trong mục 3 và lưu ảnh chụp màn hình vào thư mục `Evidence/`. Chạy tiếp script lần 2 (kiểm tra tính idempotent) và lần 3 (kiểm tra xử lý lỗi khi có 1 node bị tắt).
- [x] Thực hiện bài test failover, ghi chép lại số lượng gói tin bị mất và tổng thời gian mạng hội tụ. (13/11/2026: shut Po1 trên DIST-SW01 → DIST-SW02 Active, PC-HQ1 mất 0/150 gói; no shut → SW01 Active lại nhờ preempt. `Evidence/S10_failover.txt`)
- [x] Chạy lệnh `write memory` trên tất cả thiết bị. Lấy các file backup "after" mới nhất do script sinh ra, đồng thời xuất thủ công cấu hình của ISP-RTR01 và SRV-DHCP-DNS để đưa vào các thư mục `Configurations/HQ_Startup_Configs/`, `Hanoi_Startup_Configs/`, `DaNang_Startup_Configs/` (riêng cấu hình của ISP để ở một thư mục riêng).

Giai đoạn 9 — Viết Report PDF bằng tiếng Anh
Báo cáo cần có trang bìa, mục lục và đánh số trang đầy đủ. Mỗi chương dưới đây tương ứng với 1 tiêu chí chấm điểm:
1. Executive Summary (10%): Trình bày gói gọn trong 1 trang bằng ngôn ngữ quản lý. Đi từ nhu cầu thực tế của TVI (mô hình hybrid work, xử lý AI ở Hà Nội, triển khai IoT ở Đà Nẵng, giảm độ trễ ứng dụng SaaS, mở rộng lên 10k user vào năm 2030) → chuyển thành các mục tiêu kỹ thuật → tóm tắt kết quả đạt được.
2. Architecture & Topology (15%): Đưa vào sơ đồ logical và physical, bảng danh sách thiết bị, bảng đấu nối vật lý, phân tích sự tách biệt giữa miền L2 và L3, cùng vị trí điểm demarcation.
3. IP Addressing (15%): Trình bày bảng IP schema, giải thích cách tính VLSM, cấu trúc phân cấp IPv6, kỹ thuật tóm tắt tuyến /16 qua BGP tại biên chi nhánh, tỷ lệ không gian địa chỉ còn trống và khối mạng IoT dự trữ cho 10k+ thiết bị.
4. Core Infrastructure & Technology Rationale (20%): Giải thích lý do chọn kiến trúc 3 lớp core/distribution/access, cơ chế RSTP + chọn root bridge, LACP, HSRP + interface tracking, OSPF làm underlay, BGP làm overlay (giúp cô lập miền lỗi giữa các site, kiểm soát chính sách và tóm tắt tuyến), cùng giao thức GRE/IPsec. Làm rõ cách thức mạng underlay và overlay tương tác với nhau. Trình bày lộ trình mở rộng bằng EVPN-VXLAN cho data center và SD-WAN dual-ISP: giải thích rõ cơ chế hoạt động (kiến trúc spine-leaf, VXLAN đóng vai trò overlay L2 chạy trên nền underlay L3 OSPF, EVPN sử dụng MP-BGP làm control plane để học MAC/IP thay thế cho cơ chế flooding truyền thống), cách áp dụng vào data center tại HQ, và lý do chưa dựng trực tiếp trong bài lab. Viết riêng 1 đoạn về OSPFv3 (RFC 5340): thiết kế cho môi trường thật là chạy OSPFv3 song song OSPFv2 trên mọi link dual-stack để IPv6 hội tụ như IPv4. Nói rõ trong lab chỉ dùng OSPFv2 + IPv6 connected, vì image vIOS-L2 15.0 (2014) không có OSPFv3; checklist chấp nhận "OSPFv3 or multi-area OSPF". Cuối cùng, nêu lý do lựa chọn chạy image vIOS trên nền tảng GNS3, kèm các giới hạn của image (cần ổ đĩa IDE, không có OSPFv3/DAI) và việc thay container automation.
5. Security, QoS & Automation (15%): Đưa vào bảng phân vùng trust zone, giải thích ý nghĩa từng dòng lệnh trong ACL GUEST-IN và IOT-ISOLATION, cơ chế NAT (Overload kết hợp Static NAT Port Forwarding), DHCP snooping + port-security (có bằng chứng lab), DAI (giải thích cơ chế: so gói ARP với bảng binding của DHCP snooping, kèm cấu hình mẫu `ip arp inspection vlan 10,40,50`; nói rõ image lab không hỗ trợ nên chưa có bằng chứng chạy thật), và các bước hardening. Trình bày giải pháp ZTNA/SASE cho nhân viên làm việc từ xa (xác thực định danh, cấp quyền tối thiểu, kiểm tra tình trạng thiết bị tuân theo chuẩn NIST SP 800-207). Về QoS: lập bảng giá trị DSCP (EF 46, AF31 26), giải thích cơ chế LLQ và traffic shaping. Về Automation: mô tả luồng chạy của script, cấu trúc file inventory, cơ chế bắt lỗi, tính chất idempotency, và đính kèm đoạn log mẫu.
6. Testing, Verification & Failover (15%): Chèn toàn bộ ảnh chụp bằng chứng theo mục 3, dưới mỗi ảnh viết phần giải thích dựa theo cột "Logic để nói". Lập bảng tổng hợp kết quả kiểm thử failover.
7. Formatting (10%): Đảm bảo hệ thống tiêu đề nhất quán, có đầy đủ chú thích cho mọi hình ảnh và bảng biểu. Trích dẫn đầy đủ các tài liệu chuẩn (RFC 2328, 5340, 4271, 1918, 5737, 3849, 2474, 3246, 2597, 7348, 7432; IEEE 802.1Q, 802.1w, 802.1AX; Cisco docs; NIST SP 800-207). Lưu ý quan trọng: Toàn bộ câu chữ trong báo cáo phải được người viết tự đọc lại và biên tập bằng văn phong cá nhân — đề bài nghiêm cấm nộp văn bản do AI sinh ra mà chưa qua chỉnh sửa.
Phụ lục: Cung cấp hướng dẫn vận hành chi tiết (cách khởi động bài lab, cách chạy script tự động hóa, và quy trình thực hiện bài test failover).

Giai đoạn 10 — Đóng gói bài nộp và Chuẩn bị kịch bản Demo
- [ ] Nén toàn bộ thành file zip theo cấu trúc `TVI_Project_GroupXX/`: bên trong gồm `Report/TVI_Technical_Explanation_Report.pdf`, thư mục `Configurations/` (chứa 3 thư mục con của 3 site), và thư mục `Automation/` (chứa `inventory.yaml`, `auto_provision.py`, `README.md`, `backups/`, `logs/`).
- [ ] Chuẩn bị kịch bản demo (tổng thời lượng ≤ 15 phút theo quy định của đề) đi theo đúng trình tự ở mục 3: Trình bày Step 1–2 → Demo Step 3–6 (mỗi step chỉ gõ 1–2 lệnh cốt lõi) → Demo Step 7–8 → Thực hiện failover của Step 10 → Chạy trực tiếp script Step 9 (chạy lần 2 và chạy khi có 1 node bị tắt) → Phần hỏi đáp.

Giai đoạn 11 — Kiểm tra đối chiếu Rubric trước khi nộp (Bắt buộc)
- [ ] Rà soát xuôi: Kiểm tra từng step từ 1–10 và từng tiêu chí report từ 1–7 xem đã có đủ bằng chứng đạt mức điểm cao nhất hay chưa. Nếu thiếu mục nào thì phải bổ sung ngay.
- [ ] Rà soát ngược: Kiểm tra mọi khối lệnh trong thư mục `Configurations/` và mọi phần viết trong report xem có trỏ được về ít nhất 1 dòng ở mục 3 hoặc 1 tiêu chí trong report/checklist hay không. Thành phần nào dư thừa không trỏ được thì phải xoá bỏ.
- [ ] (13/11/2026: phần lab + automation đã đối chiếu đạt — hostname, RPVST priority, VLAN 999 + shutdown, LACP active, IPv6 GUA, passive-interface, /16 summary, tunnel up/up, HSRP 110 preempt, helper, NAT, ACL, Telnet/HTTP tắt (trừ HTTP của SRV dùng cho demo static NAT), EF/AF31, không mật khẩu trong code, inventory, try/except, backups + log, failover 0 gói mất. Còn phần report/zip sau GĐ 9–10.) Đối chiếu lần cuối với checklist tại mục VI của đề bài (kiểm tra hostname, STP root, VLAN 999, LACP active, IPv6 GUA, passive-interface, summarization, trạng thái tunnel up/up, HSRP 110 preempt, helper-address, NAT, ACL + tắt Telnet/HTTP, đánh dấu EF/AF31, không lưu mật khẩu trong code, tách file inventory ngoài, dùng khối lệnh try/except, có đủ thư mục backups + file log, báo cáo có mục lục + số trang, đúng cấu trúc file zip, và thời gian failover < 3 phút).
- [ ] Nhờ công cụ Antigravity (agy) chấm thử một cách độc lập dưới góc độ giảng viên trên gói bài nộp hoàn chỉnh. Tiến hành sửa lại các lỗi bị trừ điểm nếu nhận xét đó là chính xác.
- [ ] Tự diễn tập toàn bộ buổi demo 1 lần và bấm giờ để kiểm soát thời gian.

Quy tắc chung: Một giai đoạn chỉ được phép đánh dấu hoàn thành khi đã thu thập đủ tất cả ảnh chụp bằng chứng cho các dòng tương ứng ở mục 3, đồng thời cam kết không tự ý thêm bất kỳ tính năng nào nằm ngoài bảng.
