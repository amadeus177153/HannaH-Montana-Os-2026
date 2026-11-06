#!/usr/bin/env python3
"""Preserve the original early microcode CPIO prefix, change only main userspace."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

B = Path(sys.argv[1] if len(sys.argv) > 1 else '/data/hannah-hd')
R = B / 'rootfs'
I = B / 'iso'
original = R / 'tmp/hannah-source-initrd'
assert original.exists(), 'Extract the source initrd with unmkinitramfs first'
data = original.read_bytes()
offset = 0
# Do not search for compression magic: firmware files inside the uncompressed
# CPIO prefix are themselves .zst files. Walk complete newc records instead.
while offset < len(data):
    while offset < len(data) and data[offset] == 0:
        offset += 1
    if data[offset:offset + 6] not in (b'070701', b'070702'):
        break
    fields = [int(data[offset + 6 + j * 8:offset + 14 + j * 8], 16) for j in range(13)]
    content = (offset + 110 + fields[11] + 3) & ~3
    offset = (content + fields[6] + 3) & ~3
assert offset > 0 and data[offset:offset + 4] == bytes.fromhex('28b52ffd'), 'Unexpected source initramfs layout'
prefix = data[:offset]
# Independently unpack the Zstandard main archive; do not merge early microcode.
compressed = B / 'initrd-main.zst'
compressed.write_bytes(data[offset:])
main = B / 'initrd-main'
if main.exists():
    shutil.rmtree(main)
main.mkdir()
decomp = subprocess.Popen(['zstd', '-dc', str(compressed)], stdout=subprocess.PIPE)
subprocess.run(['cpio', '-idmu', '--no-absolute-filenames', '--quiet'],
               cwd=main, stdin=decomp.stdout, check=True)
decomp.stdout.close()
assert decomp.wait() == 0
uuid = (main / 'conf/uuid.conf').read_bytes()
assert uuid.strip() == (I / '.disk/casper-uuid-generic').read_bytes().strip()
dest = main / 'usr/share/plymouth/themes/hannah-montana'
shutil.copytree(R / 'usr/share/plymouth/themes/hannah-montana', dest, symlinks=True)
link = main / 'usr/share/plymouth/themes/default.plymouth'
link.unlink()
link.symlink_to('/usr/share/plymouth/themes/hannah-montana/hannah-montana.plymouth')
(main / 'etc/plymouth/plymouthd.conf').write_text('[Daemon]\nTheme=hannah-montana\n')
# Preserve the live username expected by the stock installer launcher.
conf = '''export USERNAME="kubuntu"
export USERFULLNAME="Hannah Montana OS"
export HOST="hannah-montana"
export BUILD_SYSTEM="Ubuntu"
export FLAVOUR="kubuntu"
'''
(main / 'etc/casper.conf').write_text(conf)
(R / 'etc/casper.conf').write_text(conf)
# Record metadata and source hashes before creating a replacement archive.
report = {'early_cpio_bytes': offset, 'early_cpio_sha256': hashlib.sha256(prefix).hexdigest(),
          'casper_uuid': uuid.decode().strip(),
          'kernel_sha256': hashlib.sha256((I / 'casper/vmlinuz').read_bytes()).hexdigest(),
          'compression': 'zstd', 'original_initrd_sha256': hashlib.sha256(data).hexdigest()}
out = I / 'casper/initrd'
out.chmod(0o644)
with out.open('wb') as f:
    f.write(prefix)
    # CPIO metadata remains from the original main archive except for artwork.
    find = subprocess.Popen(['find', '.', '-print0'], cwd=main, stdout=subprocess.PIPE)
    cpio = subprocess.Popen(['cpio', '--null', '-o', '--format=newc', '--quiet'],
                            cwd=main, stdin=find.stdout, stdout=subprocess.PIPE)
    find.stdout.close()
    zstd = subprocess.run(['zstd', '-q', '-T4', '-10', '-c'], stdin=cpio.stdout, stdout=f)
    cpio.stdout.close()
    assert zstd.returncode == 0 and cpio.wait() == 0 and find.wait() == 0
assert out.read_bytes()[:offset] == prefix
report['new_initrd_sha256'] = hashlib.sha256(out.read_bytes()).hexdigest()
(B / 'artifacts/initrd-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
compressed.unlink()
