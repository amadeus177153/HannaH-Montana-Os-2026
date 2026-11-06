#!/bin/bash
# Rebuild workflow. Run with bash; Docker must be accessible to the current user.
# A fresh extracted work tree is required; source ISOs are never modified.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
work_dir="$(dirname -- "$script_dir")"
iso_dir="$(dirname -- "$work_dir")"
if [ -e "$work_dir/rootfs" ] || [ -e "$iso_dir/hannah-montana-os-26.04.1-desktop-amd64.iso" ]; then
    printf '%s\n' 'This workflow needs a fresh work directory and no existing output ISO.' >&2
    printf '%s\n' 'Preserve your current build before rebuilding. See the individual Python scripts for resuming.' >&2
    exit 1
fi
cd "$iso_dir"
printf '%s\n' '831e4d4bb85098339ba43d3502cd6619b27e76daf37246a084cd68a6413090b8  kubuntu-26.04.1-desktop-amd64.iso' \
    '9f9efd4c401e5274b9bca6809cc88b0cfd880a7ae4f5d9c2aa432d7a33e217be  hannah_montana_linux_x86_basic_edition.iso' | sha256sum -c
docker build -t hannah-iso-builder:26.04 "$script_dir"
mkdir -p "$work_dir/logs" "$work_dir/artifacts" "$work_dir/iso" "$work_dir/original"
docker run --rm -v "$iso_dir:/data" hannah-iso-builder:26.04 bash -euc '
    xorriso -osirrox on -indev /data/kubuntu-26.04.1-desktop-amd64.iso -extract / /data/hannah-modern/iso
    xorriso -osirrox on -indev /data/hannah_montana_linux_x86_basic_edition.iso -extract / /data/hannah-modern/original
    unsquashfs -no-progress -processors 6 -d /data/hannah-modern/rootfs /data/hannah-modern/iso/casper/filesystem.squashfs
    unsquashfs -no-progress -processors 4 -d /data/hannah-modern/original-root /data/hannah-modern/original/casper/filesystem.squashfs
    chroot /data/hannah-modern/rootfs dpkg-query -W -f="\${Package} \${Version}\n" > /data/hannah-modern/artifacts/base-packages.txt
    cp /data/hannah-modern/iso/casper/initrd /data/hannah-modern/rootfs/tmp/hannah-source-initrd
    python3 /data/hannah-modern/scripts/customize.py
    python3 /data/hannah-modern/scripts/repack_initrd.py
'
docker build -t hannah-iso-preview:26.04 -f "$script_dir/Dockerfile.preview" "$script_dir"
docker run --rm --cap-add SYS_ADMIN --cap-add SYS_NICE -v "$iso_dir:/data" \
    hannah-iso-preview:26.04 bash /data/hannah-modern/scripts/preview.sh
docker run --rm -v "$iso_dir:/data" hannah-iso-builder:26.04 bash -euc '
    python3 /data/hannah-modern/scripts/package_iso.py
    python3 /data/hannah-modern/scripts/verify_iso.py
'
