from pathlib import Path
import subprocess,hashlib,json
B=Path('/data/hannah-repair');iso=B.parent/'hannah-montana-os-26.04.1-hd-fixed-amd64.iso'
assert iso.is_file()
# Validate actual ISO files, not only staging.
(B/'final.squashfs').unlink(missing_ok=True)
subprocess.run(['xorriso','-osirrox','on','-indev',str(iso),'-extract','/casper/filesystem.squashfs',str(B/'final.squashfs')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
sq=B/'final.squashfs'
def read(p):return subprocess.check_output(['unsquashfs','-cat',str(sq),p])
assert b'FollowsColorScheme=true' in read('usr/share/icons/hannah_montana/index.theme')
assert b'widgetStyle=Breeze' in read('etc/skel/.config/kdeglobals')
assert b'QT_QUICK_BACKEND=software' in read('etc/xdg/plasma-workspace/env/hannah-compat.sh')
assert b'org.kde.plasma.keyboard.desktop' in read('etc/skel/.config/kwinrc')
assert b'plasma-dbus-run-session-if-needed' in read('usr/libexec/start-kubuntu-live-env')
for p in ['usr/share/icons/hannah_montana/128x128/apps/systemsettings.png','usr/share/icons/hannah_montana/128x128/categories/applications-internet.png','usr/share/plasma/desktoptheme/hannah_montana/icons/network.svgz']:
 assert read(p)==(B/'rootfs'/p).read_bytes(),p
layout=subprocess.check_output(['xorriso','-indev',str(iso),'-report_el_torito','plain','-report_system_area','plain'],stderr=subprocess.STDOUT).decode()
(B/'artifacts/final-boot-layout.txt').write_text(layout)
assert 'UEFI' in layout and 'BIOS' in layout
h=hashlib.sha256()
with iso.open('rb') as f:
 for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
assert h.hexdigest() in iso.with_name(iso.name+'.sha256').read_text()
(B/'artifacts/iso-static-validation.json').write_text(json.dumps({'sha256':h.hexdigest(),'actual_iso_files_checked':True,'BIOS_and_UEFI_boot_records':True,'touch_configuration_present':True},indent=2)+'\n')
print('Actual ISO payload, checksum, BIOS/UEFI boot records and touch settings verified',flush=True)
