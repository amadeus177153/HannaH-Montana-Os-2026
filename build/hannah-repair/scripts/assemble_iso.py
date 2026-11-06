#!/usr/bin/env python3
"""Reapply the exact source boot options to the newly mapped ISO filesystem."""
from pathlib import Path
import hashlib
import json
import re
import shlex
import subprocess
import sys

B = Path(sys.argv[1] if len(sys.argv) > 1 else '/data/hannah-repair')
SRC = B.parent / 'kubuntu-26.04.1-desktop-amd64.iso'
OUT = B.parent / 'hannah-montana-os-26.04.1-hd-fixed-amd64.iso'
assert not OUT.exists(), f'Refusing to overwrite {OUT}'
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()
source = subprocess.run(['xorriso', '-indev', str(SRC), '-report_el_torito', 'cmd'],
    capture_output=True, text=True, check=True)
# stdout is a shell-quoted argument report, not a command to execute as shell.
lines = [l for l in source.stdout.splitlines() if l.startswith('-')]
args = []
for line in lines:
    if not line.startswith('-volid '):
        args.extend(shlex.split(line))
match = re.search(r"-volume_date uuid\s+'?([0-9]{16})", source.stdout)
assert match and args, source.stdout
uuid = match.group(1)
(B / 'artifacts/source-boot-options.txt').write_text(source.stdout)
subprocess.run(['xorriso', '-indev', str(SRC), '-outdev', str(OUT),
    '-map', str(B / 'iso'), '/', *args,
    '-volid', 'HANNAH_26_04_1_HD_FIXED',
    '-volume_date', 'uuid', uuid,
    '-padding', 'included', '-commit', '-end'], check=True)
digest = sha(OUT)
OUT.with_name(OUT.name + '.sha256').write_text(f'{digest}  {OUT.name}\n')
report = {'output': OUT.name, 'bytes': OUT.stat().st_size, 'sha256': digest,
          'base_sha256': sha(SRC), 'source_date_uuid': uuid,
          'boot_layout': 'official BIOS/UEFI boot options reapplied from xorriso report',
          'hardware_boot_tested': False, 'full_disk_install_tested': False,
          'virtual_machine_used': False}
(B / 'artifacts/build-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2), flush=True)
