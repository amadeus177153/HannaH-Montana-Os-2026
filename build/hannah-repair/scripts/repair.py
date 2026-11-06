from pathlib import Path
from PIL import Image,ImageOps
import json,shutil
B=Path('/data/hannah-repair');R=B/'rootfs';P=R/'usr/share/icons/hannah_montana'
m=json.loads(Path('/data/hannah-upscale/artifacts/enhancement-manifest.json').read_text());count=0
for key,info in m['icons'].items():
 im=Image.open(Path('/data/hannah-modern/original-root')/info['source']).convert('RGBA')
 for size in [8,16,22,24,32,48,64,128,256,512]:
  if info['strip']:out=im.resize((size,round(size*im.height/im.width)),Image.Resampling.LANCZOS)
  else:
   scaled=ImageOps.contain(im,(size,size),Image.Resampling.LANCZOS)
   out=Image.new('RGBA',(size,size));out.alpha_composite(scaled,((size-scaled.width)//2,(size-scaled.height)//2))
  out.save(P/f'{size}x{size}'/key);count+=1
aliases={'org.kde.dolphin':'system-file-manager','org.kde.konsole':'konsole','org.kde.kate':'accessories-text-editor','org.kde.discover':'system-software-install','org.kde.okular':'okular','systemsettings':'preferences-system','firefox_firefox':'firefox','org.kubuntu.manage-software':'system-software-install'}
for size in [8,16,22,24,32,48,64,128,256,512]:
 for alias,source in aliases.items():
  found=list((P/f'{size}x{size}').glob(f'*/{source}.png'))
  if found:(P/f'{size}x{size}/apps/{alias}.png').write_bytes(found[0].read_bytes())
style=R/'usr/share/plasma/desktoptheme/hannah_montana'
f=style/'plasmarc';f.write_text(f.read_text().replace('FallbackTheme=oxygen','FallbackTheme=default'))
source=R/'usr/share/plasma/desktoptheme/default/icons'
if source.exists():shutil.copytree(source,style/'icons',dirs_exist_ok=True)
for top in [R/'etc',R/'usr/share/plasma/look-and-feel/org.hannahmontana.desktop',R/'var/lib/sddm/.config']:
 for f in top.rglob('*'):
  if f.is_file() and not f.is_symlink() and f.stat().st_size<200000:
   try:t=f.read_text()
   except (UnicodeError,OSError):continue
   n=t.replace('widgetStyle=oxygen','widgetStyle=Breeze').replace('library=org.kde.oxygen','library=org.kde.breeze')
   if n!=t:f.write_text(n)
f=R/'usr/libexec/start-kubuntu-live-env'
f.write_text('''#!/bin/sh
export XDG_SESSION_CLASS=user
export XDG_SESSION_DESKTOP=KDE
export DESKTOP_SESSION=plasma
export QT_QPA_PLATFORMTHEME=kde
exec /usr/lib/x86_64-linux-gnu/libexec/plasma-dbus-run-session-if-needed /usr/bin/startplasma-wayland
''');f.chmod(0o755)
f=R/'etc/xdg/plasma-workspace/env/hannah-compat.sh';f.write_text('#!/bin/sh\nexport QT_QUICK_BACKEND=software\n');f.chmod(0o755)
for rel in ['run']:
 p=R/rel
 for f in p.iterdir():
  if f.is_symlink() or not f.is_dir():f.unlink()
  else:shutil.rmtree(f)
(B/'artifacts/repair.json').write_text(json.dumps({'icons_regenerated':count,'method':'original RGBA resampled together with Lanczos','qt_widget_style':'Breeze','qt_quick_backend':'software','panel_fallback':'default','hardware_failure_reproduced':False},indent=2)+'\n')
print('Repaired',count,'icons',flush=True)
