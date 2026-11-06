from pathlib import Path
import configparser,io
R=Path('/data/hannah-repair/rootfs')
for base in ['etc/xdg','etc/skel/.config']:
 f=R/base/'kwinrc';c=configparser.ConfigParser(interpolation=None);c.optionxform=str;c.read(f)
 c['Wayland']={'InputMethod[$e]':'/usr/share/applications/org.kde.plasma.keyboard.desktop','VirtualKeyboardEnabled':'true'}
 if 'Input' not in c:c['Input']={}
 c['Input']['TabletMode']='auto'
 s=io.StringIO();c.write(s,space_around_delimiters=False);f.write_text(s.getvalue())
# Boot-time safe graphics option. QtQuick software is also used on normal boot.
f=R/'etc/xdg/plasma-workspace/env/hannah-compat.sh'
f.write_text('''#!/bin/sh
export QT_QUICK_BACKEND=software
if grep -qw hannah_safe_graphics=1 /proc/cmdline; then
    export LIBGL_ALWAYS_SOFTWARE=1
fi
''');f.chmod(0o755)
print('Wayland touch, automatic tablet mode, Plasma Keyboard enabled')
