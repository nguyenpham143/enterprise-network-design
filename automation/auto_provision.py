"""TVI network automation (Step 9).

For each device in inventory.yaml:
  1. back up `show running-config` + `show ip interface brief` (before)
  2. send only the missing baseline lines (AAA, NTP, Syslog, banner) and missing VLANs
  3. if something was sent: save the config and back up again (after);
     otherwise log "no changes" (idempotent, no write memory)
A device that is down or rejects the login is logged and skipped; the run continues.

Credentials are never stored here: TVI_USER / TVI_PASS environment variables, or getpass.

Usage:
  python3 auto_provision.py                     # all devices
  python3 auto_provision.py HCMC-ACC-SW01 ...   # only the listed hostnames
"""
import logging
import os
import re
import sys
from datetime import datetime
from getpass import getpass

import yaml
from netmiko import ConnectHandler, NetmikoAuthenticationException, NetmikoTimeoutException

BASE = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(BASE, "backups")
LOG_DIR = os.path.join(BASE, "logs")

BANNER_TEXT = "Unauthorized access to TVI network is prohibited"
# Order matters: aaa new-model must come before the other aaa lines.
BASELINE = [
    "aaa new-model",
    "aaa authentication login default local",
    "aaa authorization exec default local",
    "ntp server 10.10.47.10",
    "logging host 10.10.47.10",
]

log = logging.getLogger("tvi")


def setup_logging():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    for h in (logging.FileHandler(os.path.join(LOG_DIR, "automation.log")), logging.StreamHandler()):
        h.setFormatter(fmt)
        log.addHandler(h)


def load_inventory(path=os.path.join(BASE, "inventory.yaml")):
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["devices"], data["vlan_names"]


def get_credentials():
    user = os.environ.get("TVI_USER") or input("SSH username: ")
    pwd = os.environ.get("TVI_PASS") or getpass("SSH password: ")
    return user, pwd


def backup(conn, hostname, stage):
    """Save running-config + interface summary to backups/<hostname>_<timestamp>_backup.cfg."""
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")  # ISO 8601 basic format
    path = os.path.join(BACKUP_DIR, f"{hostname}_{stamp}_backup.cfg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"! {hostname} - {stage} - {stamp}\n")
        f.write(conn.send_command("show running-config") + "\n\n")
        f.write(conn.send_command("show ip interface brief") + "\n")
    log.info("%s: %s backup saved to %s", hostname, stage, os.path.relpath(path, BASE))
    return path


def missing_commands(conn, dev, vlan_names):
    """Compare the wanted state with the device and return only what is missing."""
    run = conn.send_command("show running-config")
    running = {line.strip() for line in run.splitlines()}
    cmds = [c for c in BASELINE if c not in running]
    if BANNER_TEXT not in run:
        cmds.append(f"banner motd ^{BANNER_TEXT}^")
    if dev["vlans"]:
        vlan_table = conn.send_command("show vlan brief")
        for vid in dev["vlans"]:
            name = vlan_names[vid]
            if not re.search(rf"^{vid}\s+{name}\b", vlan_table, re.M):
                cmds += [f"vlan {vid}", f"name {name}", "exit"]
    return cmds


def provision(dev, vlan_names, user, pwd):
    name = dev["hostname"]
    params = {"device_type": dev["device_type"], "host": dev["ip"], "port": dev.get("port", 22),
              "username": user, "password": pwd, "timeout": 10}
    try:
        with ConnectHandler(**params) as conn:
            conn.enable()
            backup(conn, name, "before")
            cmds = missing_commands(conn, dev, vlan_names)
            if not cmds:
                log.info("%s: no changes", name)
                return
            out = conn.send_config_set(cmds)
            if "Invalid input" in out:
                log.error("%s: device rejected a command:\n%s", name, out)
            conn.save_config()
            backup(conn, name, "after")
            log.info("%s: applied %d command(s): %s", name, len(cmds), "; ".join(cmds))
    except NetmikoTimeoutException:
        log.error("%s (%s): connection timed out", name, dev["ip"])
    except NetmikoAuthenticationException:
        log.error("%s (%s): authentication failed", name, dev["ip"])
    except Exception as exc:  # any other problem: log it and continue with the next device
        log.error("%s (%s): unexpected error: %s", name, dev["ip"], exc)


def main():
    setup_logging()
    devices, vlan_names = load_inventory()
    only = set(sys.argv[1:])
    if only:
        devices = [d for d in devices if d["hostname"] in only]
    user, pwd = get_credentials()
    log.info("=== run started: %d device(s) ===", len(devices))
    for dev in devices:
        provision(dev, vlan_names, user, pwd)
    log.info("=== run finished ===")


if __name__ == "__main__":
    main()
