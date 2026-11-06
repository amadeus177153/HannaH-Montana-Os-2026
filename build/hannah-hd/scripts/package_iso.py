#!/usr/bin/env python3
"""Finalize manifests/checksums and replay the official hybrid boot layout."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys

B = Path(sys.argv[1] if len(sys.argv) > 1 else '/data/hannah-hd')
R = B / 'rootfs'
I = B / 'iso'
OUT = B.parent / 'hannah-montana-os-26.04.1-hd-amd64.iso'
SRC = B.parent / 'kubuntu-26.04.1-desktop-amd64.iso'

def sha(path, alg='sha256'):
    h = hashlib.new(alg)
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

assert not OUT.exists(), f'Refusing to overwrite {OUT}'
assert (B / 'artifacts/initrd-report.json').is_file()
# Remove only build/test state inside the extracted filesystem, never host state.
for d in ['tmp', 'var/tmp', 'root/.cache', 'root/.config', 'root/.local']:
    p = R / d
    if p.exists():
        for f in p.iterdir():
            if f.is_symlink() or not f.is_dir():
                f.unlink()
            else:
                shutil.rmtree(f)
for d in ['tmp', 'var/tmp']:
    (R / d).chmod(0o1777)
for name in ['var/log/Calamares.log', 'var/log/calamares.log']:
    (R / name).unlink(missing_ok=True)
assert not list((R / 'proc').iterdir()), 'Unmount the preview proc filesystem first'
assert not list((R / 'sys').iterdir()), 'Unexpected mounted sys filesystem'

(I / '.disk/info').chmod(0o644)
(I / '.disk/info').write_text('Hannah Montana OS 26.04.1 HD amd64 - Kubuntu 26.04.1 LTS base\n')
grub = I / 'boot/grub/grub.cfg'
grub.chmod(0o644)
grub.write_text('''set timeout=15
loadfont unicode
insmod all_video
insmod gfxterm
insmod png
set gfxmode=auto
terminal_output gfxterm
background_image /boot/grub/hannah.png
set menu_color_normal=white/black
set menu_color_highlight=yellow/magenta

menuentry "Probar o instalar Hannah Montana OS HD" {
    set gfxpayload=keep
    linux /casper/vmlinuz --- quiet splash
    initrd /casper/initrd
}
menuentry "Hannah Montana OS (graficos seguros / safe graphics)" {
    set gfxpayload=keep
    linux /casper/vmlinuz nomodeset --- quiet splash
    initrd /casper/initrd
}
if [ "$grub_platform" = "efi" ]; then
    menuentry "Arrancar el siguiente volumen" { exit 1; }
    menuentry "Configuracion del firmware UEFI" { fwsetup; }
fi
''')
shutil.copy2(R / 'usr/share/wallpapers/hannah_montana_1.png',
             I / 'boot/grub/hannah.png')
# The already installed artwork is in the live filesystem. Keep the standalone
# update package outside the ISO to avoid storing a second 500 MB copy.
(I / 'hannah-montana-artwork.deb').unlink(missing_ok=True)
readme = B / 'LEEME-INSTALACION.txt'
if readme.exists():
    shutil.copy2(readme, I / 'LEEME-INSTALACION.txt')

manifest = subprocess.check_output(['chroot', str(R), 'dpkg-query', '-W',
                                   '-f=${Package} ${Version}\n'])
(I / 'casper/filesystem.manifest').write_bytes(manifest)
(B / 'artifacts/final-packages.txt').write_bytes(manifest)
size = subprocess.check_output(['du', '-sx', '--block-size=1', str(R)]).split()[0]
(I / 'casper/filesystem.size').write_bytes(size + b'\n')
squash = I / 'casper/filesystem.squashfs'
# The official squashfs is still available unmodified in the source ISO.
squash.unlink()
subprocess.run(['mksquashfs', str(R), str(squash), '-noappend', '-comp', 'zstd',
    '-Xcompression-level', '15', '-b', '1048576', '-processors', '6',
    '-mem', '3G', '-no-progress'], check=True)

# Match the official integrity-check exclusion of boot records patched by libisofs.
excluded = {'md5sum.txt', 'SHA256SUMS', 'boot.catalog', 'boot/grub/i386-pc/eltorito.img'}
md5_lines = []
sha_lines = []
for p in sorted(I.rglob('*')):
    rel = p.relative_to(I).as_posix()
    if p.is_file() and not p.is_symlink() and rel not in excluded:
        md5_lines.append(f'{sha(p, "md5")}  ./{rel}\n')
        sha_lines.append(f'{sha(p)}  ./{rel}\n')
for name, content in [('md5sum.txt', md5_lines), ('SHA256SUMS', sha_lines)]:
    p = I / name
    if p.exists():
        p.chmod(0o644)
    p.write_text(''.join(content))

# Reapply explicit boot options after mapping: generic replay loses the original
# boot-image node when the complete ISO tree has been replaced.
subprocess.run([sys.executable, str(B / 'scripts/assemble_iso.py'), str(B)], check=True)
