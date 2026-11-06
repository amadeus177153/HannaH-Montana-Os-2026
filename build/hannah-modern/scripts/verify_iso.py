#!/usr/bin/env python3
"""Read the finished ISO back and validate its actual packaged contents."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import yaml

B = Path(sys.argv[1] if len(sys.argv) > 1 else '/data/hannah-modern')
BASE = B.parent
ISO = BASE / 'hannah-montana-os-26.04.1-desktop-amd64.iso'
SRC = BASE / 'kubuntu-26.04.1-desktop-amd64.iso'
V = B / 'verification'
V.mkdir(exist_ok=True)
TREE = V / 'iso'
ROOT = V / 'rootfs'
checks = {}

def sha(path, algorithm='sha256'):
    h = hashlib.new(algorithm)
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def check(name, condition, detail=True):
    checks[name] = {'passed': bool(condition), 'detail': detail}
    print(('PASS ' if condition else 'FAIL ') + name, flush=True)
    assert condition, name

def run(args):
    return subprocess.check_output(args, stderr=subprocess.STDOUT).decode(errors='replace')

check('official_base_sha256', sha(SRC) == '831e4d4bb85098339ba43d3502cd6619b27e76daf37246a084cd68a6413090b8')
check('original_hannah_iso_unchanged',
      sha(BASE / 'hannah_montana_linux_x86_basic_edition.iso') == '9f9efd4c401e5274b9bca6809cc88b0cfd880a7ae4f5d9c2aa432d7a33e217be')
check('finished_iso_sha256', sha(ISO) == ISO.with_name(ISO.name + '.sha256').read_text().split()[0])
reports = {}
for label, path in [('base', SRC), ('final', ISO)]:
    reports[label] = run(['xorriso', '-indev', str(path), '-report_el_torito', 'plain',
                          '-report_system_area', 'plain', '-pvd_info'])
    (B / f'artifacts/{label}-boot-layout.txt').write_text(reports[label])
check('bios_and_uefi_boot_entries', all(re.search(r'El Torito boot img\s*:\s*\d+\s+' + kind,
      reports['final']) for kind in ['BIOS', 'UEFI']))
check('hybrid_mbr_gpt', all(s in reports['final'] for s in ['grub2-mbr', 'GPT', '28732ac11ff8d211ba4b00a0c93ec93b']))
source_uuid = json.loads((B / 'artifacts/build-report.json').read_text())['source_date_uuid']
check('iso_filesystem_timestamp_uuid_preserved', source_uuid in reports['final'] and source_uuid in reports['base'])

def efi_partition(path, report):
    match = re.search(r'El Torito boot img\s*:\s*\d+\s+UEFI\s+y\s+none\s+\S+\s+\S+\s+(\d+)\s+(\d+)', report)
    assert match, report
    length, lba = map(int, match.groups())
    with path.open('rb') as f:
        f.seek(lba * 2048)
        return f.read(length * 512)

check('entire_efi_boot_partition_unchanged',
      efi_partition(ISO, reports['final']) == efi_partition(SRC, reports['base']))
with SRC.open('rb') as a, ISO.open('rb') as b:
    check('bios_mbr_boot_code_unchanged', a.read(432) == b.read(432))
if not TREE.exists():
    print('Reading finished ISO back from disk...', flush=True)
    subprocess.run(['xorriso', '-osirrox', 'on', '-indev', str(ISO), '-extract', '/', str(TREE)], check=True)
for filename, algorithm in [('SHA256SUMS', 'sha256'), ('md5sum.txt', 'md5')]:
    lines = (TREE / filename).read_text().splitlines()
    failures = []
    for line in lines:
        digest, name = line.split(None, 1)
        path = TREE / name.strip().removeprefix('./')
        if sha(path, algorithm) != digest:
            failures.append(name)
    check(f'iso_internal_{algorithm}_all_files', not failures,
          {'files': len(lines), 'failures': failures})
for name in ['bootx64.efi', 'grubx64.efi', 'mmx64.efi']:
    check('efi_file_unchanged_' + name, sha(TREE / 'EFI/boot' / name) == sha(B / 'iso/EFI/boot' / name))
ireport = json.loads((B / 'artifacts/initrd-report.json').read_text())
check('casper_initramfs_uuid_matches_iso',
      (TREE / '.disk/casper-uuid-generic').read_text().strip() == ireport['casper_uuid'])
check('signed_kernel_unchanged', sha(TREE / 'casper/vmlinuz') == ireport['kernel_sha256'])
new_initrd = TREE / 'casper/initrd'
with new_initrd.open('rb') as f:
    prefix = f.read(ireport['early_cpio_bytes'])
check('cpu_microcode_and_early_firmware_unchanged',
      hashlib.sha256(prefix).hexdigest() == ireport['early_cpio_sha256'])
check('initramfs_matches_build', sha(new_initrd) == ireport['new_initrd_sha256'])

if not ROOT.exists():
    print('Fully decompressing final live filesystem...', flush=True)
    subprocess.run(['unsquashfs', '-no-progress', '-processors', '6', '-d', str(ROOT),
                    str(TREE / 'casper/filesystem.squashfs')], check=True)
check('dpkg_audit', not run(['chroot', str(ROOT), 'dpkg', '--audit']).strip())
check('artwork_package_integrity', not run(['chroot', str(ROOT), 'dpkg', '-V', 'hannah-montana-artwork']).strip())
manifest = subprocess.check_output(['chroot', str(ROOT), 'dpkg-query', '-W', '-f=${Package} ${Version}\n'])
check('manifest_matches_installed_packages', manifest == (TREE / 'casper/filesystem.manifest').read_bytes())
base_packages = set((B / 'artifacts/base-packages.txt').read_text().splitlines())
final_packages = set(manifest.decode().splitlines())
check('all_modern_base_packages_preserved', base_packages.issubset(final_packages) and
      final_packages - base_packages == {'hannah-montana-artwork 26.04.1-1'})
check('firefox_offline_snap_seed_preserved',
      any('firefox' in p.name for p in (ROOT / 'var/lib/snapd/seed/snaps').glob('*.snap')))
versions = [p.name for p in (ROOT / 'usr/lib/modules').iterdir()]
check('kernel_modules_match', versions == ['7.0.0-30-generic'], versions)
check('kernel_supports_zstd_squashfs',
      'CONFIG_SQUASHFS_ZSTD=y' in (ROOT / 'boot/config-7.0.0-30-generic').read_text())
check('kwin_required_capability_preserved',
      os.getxattr(ROOT / 'usr/bin/kwin_wayland', 'security.capability') ==
      os.getxattr(B / 'rootfs/usr/bin/kwin_wayland', 'security.capability'))
for app in ['calamares', 'plasmashell', 'kwin_wayland', 'startplasma-wayland', 'sddm-greeter-qt6']:
    result = run(['chroot', str(ROOT), 'ldd', '/usr/bin/' + app])
    check('shared_libraries_' + app, 'not found' not in result)
artwork = json.loads((B / 'artifacts/original-artwork-sha256.json').read_text())
bad = [name for name, digest in artwork.items()
       if not (ROOT / name).is_file() or sha(ROOT / name) != digest]
check('original_artwork_byte_exact', not bad, {'files': len(artwork), 'failures': bad})
settings = yaml.safe_load((ROOT / 'etc/calamares/settings.conf').read_text())
check('installer_hannah_branding', settings['branding'] == 'hannah-montana' and
      (ROOT / 'etc/calamares/branding/hannah-montana/branding.desc').is_file())
bl = yaml.safe_load((ROOT / 'etc/calamares/modules/bootloader.conf').read_text())
check('signed_ubuntu_efi_install_path_preserved', bl['efiBootloaderId'] == 'ubuntu')
unpack = yaml.safe_load((ROOT / 'etc/calamares/modules/unpackfs.conf').read_text())
check('installer_targets_real_iso_squashfs',
      unpack['unpack'][0]['source'] == '/cdrom/casper/filesystem.squashfs')
check('no_obsolete_2009_repositories', not any('jaunty' in p.read_text(errors='replace')
      for p in (ROOT / 'etc/apt').rglob('*') if p.is_file() and p.suffix in ['.list', '.sources']))
check('ubuntu_repository_identity_preserved', '\nID=ubuntu\n' in (ROOT / 'usr/lib/os-release').read_text())
check('live_desktop_entry_script', 'exec /usr/bin/startplasma-wayland' in
      (ROOT / 'usr/libexec/start-kubuntu-live-env').read_text())
check('installed_welcome_is_hannah',
      (ROOT / 'usr/share/plasma/plasma-welcome/extra-pages/00-HannahMontana.qml').is_file() and
      not (ROOT / 'usr/share/plasma/plasma-welcome/extra-pages/01-Kubuntu.qml').exists())
check('no_build_temporary_data', not list((ROOT / 'tmp').iterdir()))
for name in ['desktop-native.png', 'login-native.png', 'installer-native.png', 'welcome-native.png']:
    check('native_render_' + name, (B / 'artifacts' / name).stat().st_size > 20000)

report = {'all_checks_passed': True, 'checks': checks,
          'physical_pc_boot_tested': False, 'complete_installation_tested': False,
          'vm_used': False,
          'limitations': ['Native UI rendering is not a kernel boot test.',
                          'No real disks were exposed to installer rendering tests.',
                          'Secure Boot and device support require testing on the target PC.']}
(B / 'artifacts/validation-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(f'ALL {len(checks)} CHECKS PASSED; physical boot/install remain untested.', flush=True)
