"""Generate TVI-Topology.drawio: 2 plain pages (Physical, Logical) from ../design/TVI-Plan-v1.2.md 2.1-2.4.
Usage: python docs/topology/make_topology.py [output.drawio]
"""
import html
import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "TVI-Topology.drawio")

ICON = {
    "router": "shape=mxgraph.cisco.routers.router;",
    "l3": "shape=mxgraph.cisco.switches.layer_3_switch;",
    "l2": "shape=mxgraph.cisco.switches.workgroup_switch;",
    "pc": "shape=mxgraph.cisco.computers_and_peripherals.pc;",
    "phone": "shape=mxgraph.cisco.modems_and_phones.ip_phone;",
    "server": "shape=mxgraph.cisco.servers.fileserver;",
    "auto": "shape=mxgraph.cisco.computers_and_peripherals.workstation;",
}
SIZE = {"router": (56, 38), "l3": (52, 52), "l2": (64, 32), "pc": (48, 44), "phone": (40, 40),
        "server": (36, 54), "auto": (52, 46)}

# line styles: every type looks clearly different
ETH = "endArrow=none;html=1;strokeWidth=1.5;strokeColor=#000000;"
WAN = "endArrow=none;html=1;strokeWidth=2.5;strokeColor=#666666;"
TRUNK = "endArrow=none;html=1;strokeWidth=3;strokeColor=#1f6fc5;"
ECH = "endArrow=none;html=1;strokeWidth=6;strokeColor=#000000;"
BLK = "endArrow=none;html=1;strokeWidth=3;strokeColor=#1f6fc5;dashed=1;dashPattern=4 4;opacity=50;"
TUN = "endArrow=none;html=1;strokeWidth=2.5;strokeColor=#d6001c;dashed=1;dashPattern=10 6;"
LAN = "endArrow=none;html=1;strokeWidth=1.5;strokeColor=#000000;"

LBL = "edgeLabel;html=1;resizable=0;points=[];fontSize=11;labelBackgroundColor=#ffffff;"


class Page:
    def __init__(self, name, w=1500, h=980):
        self.name, self.w, self.h, self.cells, self.n, self.c = name, w, h, [], 1, {}

    def _id(self):
        self.n += 1
        return f"n{self.n}"

    def v(self, value, x, y, w, h, style):
        i = self._id()
        self.cells.append(f'<mxCell id="{i}" value="{html.escape(value)}" style="{style}" vertex="1" parent="1">'
                          f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return i

    def dev(self, key, kind, name, cx, cy, side="r"):
        w, h = SIZE[kind]
        pos = {"r": "labelPosition=right;verticalLabelPosition=middle;align=left;verticalAlign=middle;spacingLeft=6;",
               "l": "labelPosition=left;verticalLabelPosition=middle;align=right;verticalAlign=middle;spacingRight=6;",
               "b": "verticalLabelPosition=bottom;verticalAlign=top;align=center;"}[side]
        i = self.v(name, cx - w / 2, cy - h / 2, w, h,
                   ICON[kind] + "html=1;fillColor=#036897;strokeColor=#ffffff;fontSize=12;" + pos)
        self.c[key] = i

    def e(self, a, b, style, la="", lb="", mid="", pts=None, ex=None, en=None, lpos=0.7):
        st = style + (f"exitX={ex[0]};exitY={ex[1]};exitDx=0;exitDy=0;" if ex else "") + \
            (f"entryX={en[0]};entryY={en[1]};entryDx=0;entryDy=0;" if en else "")
        arr = "<Array as=\"points\">" + "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in pts) + "</Array>" if pts else ""
        i = self._id()
        self.cells.append(f'<mxCell id="{i}" value="" style="{st}" edge="1" parent="1" source="{self.c[a]}" target="{self.c[b]}">'
                          f'<mxGeometry relative="1" as="geometry">{arr}</mxGeometry></mxCell>')
        for txt, pos in ((la, -lpos), (lb, lpos), (mid, 0)):
            if txt:
                j = self._id()
                self.cells.append(f'<mxCell id="{j}" value="{html.escape(txt)}" style="{LBL}" vertex="1" connectable="0" parent="{i}">'
                                  f'<mxGeometry x="{pos}" relative="1" as="geometry"><mxPoint as="offset"/></mxGeometry></mxCell>')

    def box(self, title, x, y, w, h, bottom=False):
        self.v(title, x, y, w, h, "rounded=1;arcSize=3;html=1;whiteSpace=wrap;fillColor=#ffffff;strokeColor=#999999;"
               "strokeWidth=1.5;align=left;spacingLeft=10;spacingTop=6;spacingBottom=6;fontSize=14;fontStyle=1;"
               + ("verticalAlign=bottom;" if bottom else "verticalAlign=top;"))

    def text(self, t, x, y, w, h, extra=""):
        self.v(t, x, y, w, h, "text;html=1;align=left;verticalAlign=middle;fontSize=12;" + extra)

    def legend(self, rows, x, y):
        """rows: (style, label). Draws a sample line next to each label."""
        self.v("", x, y, 300, 26 + 24 * len(rows), "rounded=1;arcSize=6;html=1;fillColor=#ffffff;strokeColor=#999999;")
        self.text("<b>Legend</b>", x + 10, y + 4, 200, 20)
        for k, (style, label) in enumerate(rows):
            yy = y + 36 + 24 * k
            i = self._id()
            self.cells.append(f'<mxCell id="{i}" value="" style="{style}" edge="1" parent="1"><mxGeometry relative="1" as="geometry">'
                              f'<mxPoint x="{x + 12}" y="{yy}" as="sourcePoint"/><mxPoint x="{x + 72}" y="{yy}" as="targetPoint"/>'
                              f'</mxGeometry></mxCell>')
            self.text(label, x + 84, yy - 10, 210, 20)

    def xml(self, pid):
        return (f'<diagram id="{pid}" name="{self.name}"><mxGraphModel grid="1" gridSize="10" page="1" '
                f'pageWidth="{self.w}" pageHeight="{self.h}"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
                f'{"".join(self.cells)}</root></mxGraphModel></diagram>')


def frame(p, titles):
    """ISP box + three site boxes (same position on both pages)."""
    p.box(titles[0], 600, 30, 300, 150)
    p.box(titles[1], 20, 230, 820, 700, bottom=True)
    p.box(titles[2], 860, 230, 300, 700, bottom=True)
    p.box(titles[3], 1180, 230, 300, 700, bottom=True)


# centres shared by both pages
ISP, EDGE, CORE, D1, D2, ACC = (750, 110), (430, 300), (430, 420), (230, 540), (630, 540), (430, 680)
HR, HS1, HS2, DR, DS = (950, 300), (950, 440), (950, 580), (1250, 300), (1250, 440)

# ================================================================ PHYSICAL
P = Page("Physical")
frame(P, ["ISP (provider)", "HQ – Ho Chi Minh City", "Hanoi – R&amp;D", "Da Nang – Logistics"])
P.legend([(WAN, "WAN link to ISP"), (ETH, "Ethernet (access)"), (TRUNK, "802.1Q trunk"),
          (ECH, "EtherChannel (LACP)"), (BLK, "Trunk blocked by STP")], 20, 20)
P.dev("ISP", "router", "ISP-RTR01", *ISP, side="b")
P.dev("EDGE", "router", "HCMC-EDGE-RTR01", *EDGE)
P.dev("CORE", "l3", "HCMC-CORE-SW01", *CORE)
P.dev("D1", "l3", "HCMC-DIST-SW01", *D1, side="l")
P.dev("D2", "l3", "HCMC-DIST-SW02", *D2)
P.dev("ACC", "l2", "HCMC-ACC-SW01", *ACC)
hosts = [("PC1", "pc", "PC-HQ1", 90, "Gi0/2"), ("PC2", "pc", "PC-HQ2", 240, "Gi0/3"), ("PH", "phone", "IP-PHONE01", 390, "Gi1/0"),
         ("SRV", "server", "SRV-DHCP-DNS", 540, "Gi1/1"), ("AUTO", "auto", "AUTOMATION", 690, "Gi1/2")]
for key, kind, name, x, port in hosts:
    P.dev(key, kind, name, x, 850, side="b")
    P.e("ACC", key, ETH, la=port, lpos=0.45)
P.e("ISP", "EDGE", WAN, la="Gi0/0", lb="Gi0/0", pts=[(430, 110)], ex=(0, 0.5))
P.e("EDGE", "CORE", ETH, la="Gi0/1", lb="Gi0/0")
P.e("CORE", "D1", ECH, mid="Po1", la="Gi0/1-2", lb="Gi0/1-2")
P.e("CORE", "D2", ECH, mid="Po2", la="Gi0/3,Gi1/0", lb="Gi0/1-2")
P.e("D1", "D2", ECH, mid="Po3", la="Gi1/0-1", lb="Gi1/0-1")
P.e("D1", "ACC", TRUNK, la="Gi0/3", lb="Gi0/0")
P.e("D2", "ACC", BLK, la="Gi0/3", lb="Gi0/1")

P.dev("HR", "router", "HANOI-RND-RTR01", *HR)
P.dev("HS1", "l3", "HANOI-RND-SW01", *HS1)
P.dev("HS2", "l2", "HANOI-RND-SW02", *HS2)
P.dev("HP1", "pc", "PC-HN1", 900, 720, side="b")
P.dev("HP2", "pc", "PC-HN2", 1040, 720, side="b")
P.e("ISP", "HR", WAN, la="Gi0/1", lb="Gi0/0", pts=[(950, 118)], ex=(1, 0.7))
P.e("HR", "HS1", TRUNK, la="Gi0/1", lb="Gi0/0")
P.e("HS1", "HS2", ECH, mid="Po1", la="Gi0/1-2", lb="Gi0/1-2")
P.e("HS2", "HP1", ETH, la="Gi0/3", lpos=0.5)
P.e("HS2", "HP2", ETH, la="Gi1/0", lpos=0.5)

P.dev("DR", "router", "DANANG-LOG-RTR01", *DR)
P.dev("DS", "l3", "DANANG-LOG-SW01", *DS)
P.dev("DP", "pc", "PC-DN1", 1250, 580, side="b")
P.e("ISP", "DR", WAN, la="Gi0/2", lb="Gi0/0", pts=[(1250, 102)], ex=(1, 0.3))
P.e("DR", "DS", TRUNK, la="Gi0/1", lb="Gi0/0")
P.e("DS", "DP", ETH, la="Gi0/1", lpos=0.5)
P.dev("DI", "pc", "IOT-DN1", 1390, 580, side="b")
P.e("DS", "DI", ETH, la="Gi0/2", lpos=0.5)

# ================================================================ LOGICAL
L = Page("Logical")
frame(L, ["ISP · AS 65000", "HQ · AS 65001 · 10.10.0.0/16", "Hanoi · AS 65002 · 10.20.0.0/16",
          "Da Nang · AS 65003 · 10.30.0.0/16"])
L.legend([(WAN, "WAN /30 (eBGP to ISP)"), (ETH, "Routed link (OSPF)"), (TUN, "GRE/IPsec tunnel (eBGP)"),
          (LAN, "VLAN subnet")], 20, 20)
L.c["NET"] = L.v("Internet<br>8.8.8.0/24", 440, 35, 120, 70, "ellipse;shape=cloud;html=1;fillColor=#ffffff;strokeColor=#666666;fontSize=12;")
L.dev("ISP", "router", "ISP-RTR01", *ISP, side="b")
L.e("NET", "ISP", WAN, pts=[(750, 70)], ex=(1, 0.5), en=(0.5, 0))
for t, x in (("OSPF areas 0 + 10", 730), ("OSPF areas 0 + 20", 1050), ("OSPF areas 0 + 30", 1370)):
    L.text(t, x - 40, 236, 140, 20, "fontSize=11;fontColor=#666666;align=right;")
L.dev("EDGE", "router", "HCMC-EDGE-RTR01", *EDGE, side="l")
L.dev("CORE", "l3", "HCMC-CORE-SW01", *CORE)
L.dev("D1", "l3", "HCMC-DIST-SW01", *D1, side="l")
L.dev("D2", "l3", "HCMC-DIST-SW02", *D2)
L.e("ISP", "EDGE", WAN, mid="203.0.113.0/30", pts=[(430, 110)], ex=(0, 0.5))
L.e("EDGE", "CORE", ETH, mid="10.10.255.64/30")
L.e("CORE", "D1", ETH, mid="10.10.255.68/30")
L.e("CORE", "D2", ETH, mid="10.10.255.72/30")
vl = L.v("<b>VLANs (gateway = HSRP VIP .1)</b><br>"
         "10 EXEC_FINANCE – 10.10.44.0/23<br>40 GUEST – 10.10.40.0/22<br>50 VOICE – 10.10.0.0/20<br>"
         "99 MANAGEMENT – 10.10.46.0/24<br>100 SERVERS – 10.10.47.0/24",
         260, 680, 340, 120, "rounded=1;arcSize=6;html=1;whiteSpace=wrap;align=left;spacingLeft=10;fillColor=#ffffff;"
         "strokeColor=#000000;fontSize=12;")
L.c["VL"] = vl
L.e("D1", "VL", LAN, en=(0.1, 0))
L.e("D2", "VL", LAN, en=(0.9, 0))

L.dev("HR", "router", "HANOI-RND-RTR01", *HR)
L.dev("HS1", "l3", "HANOI-RND-SW01", *HS1)
L.e("ISP", "HR", WAN, mid="203.0.113.4/30", pts=[(950, 118)], ex=(1, 0.7))
L.e("HR", "HS1", ETH, mid="VLAN 99 10.20.32.0/25")
hv = L.v("<b>VLANs</b><br>20 RND_ENGINEERING – 10.20.16.0/21<br>40 GUEST – 10.20.30.0/23<br>99 MANAGEMENT – 10.20.32.0/25",
         870, 560, 280, 80, "rounded=1;arcSize=6;html=1;whiteSpace=wrap;align=left;spacingLeft=8;fillColor=#ffffff;"
         "strokeColor=#000000;fontSize=11;")
L.c["HV"] = hv
L.e("HS1", "HV", LAN)

L.dev("DR", "router", "DANANG-LOG-RTR01", *DR)
L.dev("DS", "l3", "DANANG-LOG-SW01", *DS)
L.e("ISP", "DR", WAN, mid="203.0.113.8/30", pts=[(1250, 102)], ex=(1, 0.3))
L.e("DR", "DS", ETH, mid="VLAN 99 10.30.90.0/24")
dv = L.v("<b>VLANs</b><br>30 LOGISTICS_OPS – 10.30.80.0/22<br>40 GUEST – 10.30.88.0/23<br>99 MANAGEMENT – 10.30.90.0/24<br>"
         "60 IOT – 10.30.0.0/18 (ACL IOT-ISOLATION)",
         1190, 560, 280, 96, "rounded=1;arcSize=6;html=1;whiteSpace=wrap;align=left;spacingLeft=8;fillColor=#ffffff;"
         "strokeColor=#000000;fontSize=11;")
L.c["DV"] = dv
L.e("DS", "DV", LAN)
L.e("EDGE", "HR", TUN, mid="Tunnel0 · 172.16.12.0/30", ex=(1, 0.5), en=(0, 0.5))
L.e("EDGE", "DR", TUN, mid="Tunnel1 · 172.16.13.0/30", pts=[(408, 12), (1265, 12)], ex=(0.12, 0), en=(0.75, 0))

xml = '<mxfile host="Electron">' + P.xml("physical") + L.xml("logical") + "</mxfile>"
open(OUT, "w", encoding="utf-8").write(xml)
sys.stdout.write(f"wrote {OUT} (2 pages)\n")
