#!/bin/bash
# Assemble the staged HD edition. The standalone update package is not retained.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
work_dir="$(dirname -- "$script_dir")"
iso_dir="$(dirname -- "$work_dir")"
if [ -e "$iso_dir/hannah-montana-os-26.04.1-hd-amd64.iso" ]; then
    printf '%s\n' 'Preserve the existing HD ISO before rebuilding.' >&2
    exit 1
fi
test -f "$work_dir/artifacts/hd-assets-sha256.json"
docker run --rm -v "$iso_dir:/data" hannah-iso-builder:26.04 bash -euc '
    if [ ! -f /data/hannah-hd/rootfs/tmp/hannah-source-initrd ]; then
        xorriso -osirrox on -indev /data/kubuntu-26.04.1-desktop-amd64.iso -extract /casper/initrd /data/hannah-hd/rootfs/tmp/hannah-source-initrd
    fi
    python3 /data/hannah-hd/scripts/repack_initrd.py
'
docker run --rm --cap-add SYS_ADMIN --cap-add SYS_NICE -v "$iso_dir:/data" \
    hannah-iso-preview:26.04 bash /data/hannah-hd/scripts/preview.sh
docker run --rm -v "$iso_dir:/data" hannah-iso-builder:26.04 bash -euc '
    python3 /data/hannah-hd/scripts/package_iso.py
    python3 /data/hannah-hd/scripts/verify_iso.py
'
