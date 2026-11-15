# TVI Automation (Step 9)

`auto_provision.py` pushes the baseline (AAA, NTP, Syslog, banner) and creates the VLANs listed in
`inventory.yaml`. It backs up each device before and after a change and logs every run.

## Requirements
Runs on the `AUTOMATION` container in GNS3 (Python 3, netmiko, pyyaml already installed).
On another machine: `pip3 install netmiko pyyaml`.

## Run
```bash
cd /root/Automation
export TVI_USER=admin
read -s TVI_PASS && export TVI_PASS      # type the password, nothing is shown
python3 auto_provision.py                # all devices in inventory.yaml
python3 auto_provision.py HCMC-ACC-SW01  # only some devices
```
If `TVI_USER` / `TVI_PASS` are not set, the script asks for them. No password is stored in any file.

## Check the result
```bash
ls backups/                 # <hostname>_<YYYYMMDDThhmmss>_backup.cfg (ISO 8601, before and after a change)
tail -n 30 logs/automation.log
```
- Second run on the same devices: each device logs `no changes` (nothing is re-sent).
- A device that is off: `connection timed out` is logged and the other devices still finish.
