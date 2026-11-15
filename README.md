# TVI Enterprise Network — BTL2 Mạng máy tính
## Cấu trúc thư mục

| Đường dẫn | Nội dung |
|---|---|
| `TVI-Plan-v1.2.md` | Kế hoạch chính: thiết kế, bảng Rubric → Bằng chứng (mục 3), các giai đoạn, ghi chú giới hạn image |
| `TVI-IP-Schema.md` | Quy hoạch IP (VLSM IPv4, IPv6 /48 → /64, VLAN 60 IoT, khối dự trữ) |
| `TVI-Topology.drawio`, `make_topology.py` | Sơ đồ Physical + Logical (sinh bằng script) |
| `TVI.gns3`, `project-files/` | Project GNS3 (mở trực tiếp trên máy đang dùng) |
| `GNS3/TVI.gns3project` | Bản export portable để import sang máy khác (không kèm image Cisco) |
| `Configurations/` | Cấu hình đã lưu của từng thiết bị: `HQ_Startup_Configs/`, `Hanoi_Startup_Configs/`, `DaNang_Startup_Configs/`, `ISP_Config/` |
| `Automation/` | `inventory.yaml`, `auto_provision.py`, `README.md`, `backups/`, `logs/automation.log` |
| `Evidence/` | Output CLI cho từng dòng bằng chứng ở mục 3 của plan |
| `Assignment 2 - ...pdf` | Đề bài |

## 1. Cài đặt GNS3 (Windows)

**Yêu cầu máy:** Windows 10/11, CPU có VT-x/AMD-V, RAM ≥ 24 GB (GNS3 VM dùng 16 GB), VMware Workstation.

1. **Tắt Hyper-V/VBS** để VMware dùng được VT-x lồng nhau (chạy PowerShell quyền Administrator, xong thì khởi động lại):
   - Windows Security → Device security → Core isolation → tắt **Memory integrity**.
   - `bcdedit /set {current} hypervisorlaunchtype off`
   - `bcdedit /set {current} vsmlaunchtype off`
   - Nếu vẫn còn: tắt các mục `HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\{SystemGuard,SecureBiometrics,WindowsHello}` → `Enabled=0`.
   - Kiểm tra: `systeminfo` không còn dòng "A hypervisor has been detected"; mục Hyper-V Requirements báo VT-x = Yes.
2. Cài **GNS3 2.2.61 all-in-one** (giữ mặc định, bỏ chọn các tool không cần).
3. Tải **GNS3 VM 2.2.61 cho VMware** (`.ova`), import vào VMware; trong VM Settings → Processors tick **Virtualize Intel VT-x/EPT**.
4. Mở GNS3 → Setup Wizard → chọn **Run appliances in a virtual machine** → GNS3 VM, VMware, **8 vCPU, 16384 MB**. Khi VM chạy, GNS3 báo `KVM support available: True`.

## 2. Image và template (không có trong repo vì bản quyền)

Tự chuẩn bị image, rồi tạo template trong GNS3 (Edit → Preferences), tất cả **chạy trên GNS3 VM**. Tên file image phải giữ đúng như dưới để project nhận ra:

| Template | Image | Thiết lập |
|---|---|---|
| `vIOS` (router) | `vios-adventerprisek9-m.vmdk.SPA.156-2.T` (vIOS 15.6(2)T) + `IOSv_startup_config.img` của GNS3 | Qemu, virtio, 512 MB, 4 adapter |
| `vIOS-L2` (switch) | `vios_l2-adventerprisek9-m.vmdk.SSA.152-4.0.55.E` | Qemu, **ổ đĩa IDE** (virtio sẽ crash khi boot), 1024 MB, 8 adapter |
| `AUTOMATION` | Docker `adosztal/network_automation` | 2 adapter (eth0 = VLAN 99, eth1 = NAT) |
| PC, IP phone | VPCS có sẵn | — |

## 3. Mở project

- **Trên máy đang có lab:** mở GNS3, đợi GNS3 VM chạy (thanh Servers Summary báo GNS3 VM màu xanh), rồi File → Open project → chọn `TVI.gns3` trong thư mục này.
- **Trên máy khác:** GNS3 → File → Import portable project → chọn `GNS3/TVI.gns3project` → chọn chạy trên GNS3 VM. Cần có sẵn đủ template ở mục 2.
- Project có **21 node**: 5 router vIOS (ISP-RTR01, HCMC-EDGE-RTR01, SRV-DHCP-DNS, 2 router chi nhánh), 7 switch vIOS-L2, 7 VPCS (PC-HQ1, PC-HQ2, IP-PHONE01, PC-HN1, PC-HN2, PC-DN1, IOT-DN1), container AUTOMATION và NAT1.
- **Không tắt GNS3 hay VMware giữa chừng** khi vừa thêm/sửa node: GNS3 chưa kịp lưu thì thay đổi đó mất.

## 4. Khởi động lab (làm trước buổi demo khoảng 10 phút)

1. Bấm **Start all nodes** (▶). Đợi khoảng **5 phút** cho vIOS/vIOS-L2 boot xong.
   - Thông báo `% Invalid input` về `Gi2/0` lúc switch boot là vô hại.
   - Một switch vIOS-L2 thỉnh thoảng tự reload; đợi 2 phút cho nó lên lại.
2. Mở console bằng double-click node. Đăng nhập user `admin`, mật khẩu lab của nhóm (không lưu trong repo), gõ `enable`.
3. Đợi mạng hội tụ: trên `HCMC-EDGE-RTR01` gõ `show ip bgp summary` cho tới khi cả 3 neighbor có **số prefix** ở cột cuối (`172.16.12.2` = 1, `172.16.13.2` = 1, `203.0.113.1` = 4). Số 0 hoặc chữ `Idle`/`Active` nghĩa là chưa xong.
4. **Xin lại IP cho các PC** (PC boot xong trước khi mạng sẵn sàng nên lần xin đầu thường hỏng): trên PC-HQ1, PC-HQ2, IP-PHONE01, PC-HN1, PC-HN2, PC-DN1 gõ `ip dhcp`, phải thấy `DORA IP ...`. Nếu PC-HQ2 (Guest) không nhận, gõ lại lần nữa. `IOT-DN1` dùng IP tĩnh `10.30.0.10/18`, không cần làm gì.
5. Kiểm tra nhanh:
   - `HCMC-DIST-SW01`: `show standby brief` → mọi VLAN Active, priority 110.
   - `HCMC-CORE-SW01`: `show ip ospf neighbor` → 3 neighbor FULL.
   - PC-HQ1: `ping 10.20.16.10` → trả lời (đi qua tunnel sang Hà Nội).

## 5. Kịch bản demo (≤ 15 phút)

Thứ tự theo mục 3 của plan, mỗi step gõ 1–2 lệnh chính. Cột "Nói" là ý cần trình bày.

| Thời điểm | Step | Thiết bị | Lệnh | Phải thấy | Nói |
|---|---|---|---|---|---|
| 0:00 | 1–2 | — | Mở `TVI-Topology.drawio` (Physical, Logical) và `TVI-IP-Schema.md` | 3 site, demarcation, VLAN/subnet, area OSPF, VLSM + IPv6 | Demarcation là Gi0/0 mỗi router; mỗi site 1 khối /16; VLSM theo số host × 1.5 |
| 1:30 | 3 | HCMC-CORE-SW01 | `show etherchannel summary` | Po1, Po2 (SU), cổng (P), LACP | Gộp 2 cổng: thêm băng thông, hỏng 1 cổng vẫn chạy |
| | 3 | HCMC-DIST-SW02 | `show spanning-tree vlan 10` | Po3 Altn BLK | Root ép bằng priority, vòng lặp bị chặn ở đường dự phòng |
| 2:30 | 4 | HCMC-DIST-SW01 | `show standby brief` | Active 110 P, VIP .1 | PC chỉ biết gateway .1, một DIST hỏng thì con kia nhận |
| | 4 | PC-HN1 | `show ip` | 10.20.16.x, DNS 10.10.47.10, DHCP SERVER 172.16.12.1 | DHCP tập trung ở HQ, cấp qua tunnel nhờ helper-address |
| | 4 | HANOI-RND-RTR01 | `ping srv.tvi.lab` | Phân giải qua 10.10.47.10 [OK] | DNS tập trung phục vụ cả chi nhánh |
| 3:30 | 5 | HCMC-CORE-SW01 | `show ip ospf neighbor`; `show ip ospf \| include Area\|area border` | FULL với EDGE (area 0), DIST1/DIST2 (area 10); "area border router" | OSPF multi-area, CORE là ABR |
| | 5 | HCMC-EDGE-RTR01 | `show ip route ospf` | `O IA 10.10.0.0/18` | ABR tóm tắt khối distribution, area 0 gọn |
| 5:00 | 6 | PC-HQ1 rồi HCMC-EDGE-RTR01 | `ping 10.20.16.10 -c 5`; rồi `show ip bgp summary`, `show ip route bgp`, `show crypto ipsec sa \| include encaps\|decaps` | 3 neighbor có prefix; 1 tuyến /16 mỗi chi nhánh; bộ đếm encaps/decaps tăng | eBGP với ISP + eBGP qua tunnel IPsec; chi nhánh tóm tắt /16 |
| 6:30 | 7 | PC-HQ2 (Guest) | `ping 10.10.47.10`; `ping 8.8.8.8` | Nội bộ: administratively prohibited; Internet: trả lời | Guest chỉ ra Internet (ACL GUEST-IN) |
| | 7 | IOT-DN1 | `ping 10.10.47.10`; `ping 10.30.80.10`; `ping 8.8.8.8` | Server và Internet trả lời; Corp bị chặn | IoT chỉ tới server và Internet (ACL IOT-ISOLATION) |
| | 7 | ISP-RTR01 rồi HCMC-EDGE-RTR01 | `telnet 203.0.113.2 8443` (thấy `Open`, gõ Ctrl+Shift+6 rồi x để thoát); rồi `show ip nat translations` | Dòng PAT `10.10.x → 203.0.113.2` + static `203.0.113.2:8443 ↔ 10.10.47.10:443` | PAT cho user, static NAT cho dịch vụ HTTPS nội bộ |
| | 7 | ISP-RTR01 | `telnet 203.0.113.2` | Connection refused | Telnet tắt, chỉ SSHv2 |
| 8:00 | 8 | IP-PHONE01; PC-HQ1 | `ping 10.20.16.10 -c 20`; `ping 10.20.16.10 -P 17 -p 3478 -c 5` | Trả lời đều | Tạo lưu lượng voice và video giả lập |
| | 8 | HCMC-EDGE-RTR01 | `show policy-map interface Gi0/1.900 input`; `show policy-map interface Gi0/0 output` | VOICE `set dscp ef`, VIDEO `set dscp af31`; DSCP-EF trong hàng priority tăng | Đánh dấu ở biên, voice đi hàng đợi ưu tiên trên WAN |
| 9:00 | 10 | PC-HQ1 | `trace 10.20.16.10` | Đi qua 10.10.255.65 rồi 172.16.12.2 | Liên site đi qua tunnel mã hoá |
| | 10 | PC-DN1 | `trace 8.8.8.8` | 2 hop, qua 203.0.113.9 | Chi nhánh ra Internet tại chỗ, không vòng về HQ |
| 10:00 | 10 | Failover | Xem mục 7 | DIST-SW02 lên Active, không mất gói, SW01 lấy lại Active | Tracking + OSPF + HSRP, hội tụ dưới 3 phút |
| 12:30 | 9 | AUTOMATION | Xem mục 6 | Lần chạy lại "no changes"; node tắt báo timeout | Inventory riêng, không lưu mật khẩu, idempotent, try/except |
| 15:00 | — | — | Hỏi đáp | — | — |

## 6. Chạy automation (Step 9)

Mở console node `AUTOMATION`:

```bash
cd /root/Automation
cat inventory.yaml                       # inventory tách riêng khỏi code
grep -n -i password auto_provision.py    # chỉ thấy getpass, không có mật khẩu
export TVI_USER=admin
read -s TVI_PASS && export TVI_PASS      # gõ mật khẩu, không hiện ra màn hình
python3 auto_provision.py                # mọi thiết bị báo "no changes"
```

Thử xử lý lỗi:

1. Trong GNS3 chuột phải `HANOI-RND-SW02` → Stop.
2. Chạy lại `python3 auto_provision.py`: thiết bị đó báo `connection timed out`, 9 thiết bị còn lại vẫn chạy xong.
3. Xem kết quả: `ls backups/` (tên file dạng `HOST_20261114T105841_backup.cfg`, timestamp ISO 8601) và `tail -n 20 logs/automation.log` (có dòng INFO và ERROR).
4. Chuột phải `HANOI-RND-SW02` → Start, đợi khoảng 2 phút cho nó lên lại.

## 7. Demo failover (Step 10)

1. PC-HQ1: `ping 10.20.16.10 -c 150` (để chạy, mở console khác cho các bước sau).
2. HCMC-DIST-SW01: `configure terminal` → `interface Port-channel1` → `shutdown`.
3. HCMC-DIST-SW02: `show standby brief` → mọi VLAN chuyển Active.
4. HCMC-DIST-SW01: `no shutdown` (vẫn trong `interface Port-channel1`) → `end`; khoảng 1 phút sau `show standby brief` → SW01 Active lại nhờ preempt.
5. Quay lại PC-HQ1: đếm số dòng timeout. Lần chạy thử 14/11/2026 mất 0/150 gói (`Evidence/S10_failover.txt`).

## 8. Tắt lab sau khi demo

1. Không cần `write memory`: cấu hình trên mọi thiết bị đã được lưu.
2. GNS3 → Stop all nodes, rồi đóng GNS3 (GNS3 VM tự tắt theo).
