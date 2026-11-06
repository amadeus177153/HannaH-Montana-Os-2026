#!/usr/bin/env python3
"""Package restored Hannah Montana assets, including explicit HiDPI icon sizes."""
from pathlib import Path
from PIL import Image, ImageOps
import collections,configparser,hashlib,io,json,os,shutil,subprocess

B=Path('/data/hannah-hd')
U=B.parent/'hannah-upscale'
R=B/'rootfs';P=B/'artwork-package'
E=U/'enhanced'
manifest=json.loads((U/'artifacts/enhancement-manifest.json').read_text())
assert len(manifest['icons'])>1200
assert (E/'branding/launcher.png').is_file()
def write(p,s):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s);p.chmod(0o644)
def copy(s,d):
 d.parent.mkdir(parents=True,exist_ok=True)
 if d.is_symlink():d.unlink()
 shutil.copy2(s,d)
def sized(im,size,square=False):
 out=ImageOps.contain(im,(size,size),Image.Resampling.LANCZOS)
 if square:
  canvas=Image.new('RGBA',(size,size));canvas.alpha_composite(out,((size-out.width)//2,(size-out.height)//2));out=canvas
 return out
def ini(p):
 c=configparser.ConfigParser(interpolation=None,strict=False);c.optionxform=str;c.read(p);return c
def saveini(p,c):
 s=io.StringIO();c.write(s,space_around_delimiters=False);write(p,s.getvalue())

icons=P/'usr/share/icons/hannah_montana'
shutil.rmtree(icons);icons.mkdir()
sizes=[8,16,22,24,32,48,64,128,256,512]
contexts=collections.defaultdict(int)
for key,info in manifest['icons'].items():
 master=Image.open(E/'icons'/key).convert('RGBA')
 context=key.split('/')[0];contexts[context]+=1
 for size in sizes:
  dest=icons/f'{size}x{size}'/key;dest.parent.mkdir(parents=True,exist_ok=True)
  if info['strip']:
   height=round(size*info['source_size'][1]/info['source_size'][0])
   im=master.resize((size,height),Image.Resampling.LANCZOS)
  else:im=sized(master,size,True)
  im.save(dest,compress_level=6)
print(f'Generated {len(manifest["icons"])} icons at {len(sizes)} sizes',flush=True)

aliases={'org.kde.dolphin':'system-file-manager','org.kde.konsole':'konsole',
 'org.kde.kate':'accessories-text-editor','org.kde.discover':'system-software-install',
 'org.kde.okular':'okular','systemsettings':'preferences-system','firefox_firefox':'firefox',
 'org.kubuntu.manage-software':'system-software-install'}
emblem=Image.open(E/'branding/launcher.png').convert('RGBA')
for size in sizes:
 for alias,source in aliases.items():
  found=list((icons/f'{size}x{size}').glob(f'*/{source}.png'))
  dest=icons/f'{size}x{size}/apps/{alias}.png'
  if found and not dest.exists():copy(found[0],dest)
 for context,name in [('apps','start-here-hannah'),('apps','distributor-logo-hannah'),
                       ('apps','calamares'),('places','start-here'),('places','start-here-kde')]:
  dest=icons/f'{size}x{size}'/context/(name+'.png');dest.parent.mkdir(parents=True,exist_ok=True)
  emblem.resize((size,size),Image.Resampling.LANCZOS).save(dest)

# Explicit Scale=2 entries avoid choosing old low-resolution icons at HiDPI.
for nominal in [8,16,22,24,32,48,64,128,256]:
 physical=nominal*2
 if physical not in sizes:continue
 for p in (icons/f'{physical}x{physical}').rglob('*.png'):
  dest=icons/f'{nominal}x{nominal}@2'/p.relative_to(icons/f'{physical}x{physical}')
  dest.parent.mkdir(parents=True,exist_ok=True);os.link(p,dest)
mapping={'actions':'Actions','apps':'Applications','categories':'Categories','devices':'Devices',
 'emblems':'Emblems','emotes':'Emotes','mimetypes':'MimeTypes','places':'Places','status':'Status',
 'animations':'Animations','intl':'International','filesystems':'FileSystems'}
c=configparser.ConfigParser(interpolation=None);c.optionxform=str
directories=sorted({p.parent.relative_to(icons).as_posix() for p in icons.rglob('*.png')})
c['Icon Theme']={'Name':'Hannah Montana HD','Comment':'Original artwork restored with Upscayl; HiDPI assets',
 'Inherits':'breeze,hicolor','Example':'start-here-hannah','Directories':','.join(directories)}
for directory in directories:
 top=directory.split('/')[0];nominal=int(top.split('x')[0]);scale=2 if '@2' in top else 1
 context=directory.split('/')[1]
 c[directory]={'Size':str(nominal),'Scale':str(scale),'Type':'Fixed','Context':mapping.get(context,context)}
saveini(icons/'index.theme',c)

for n in range(1,6):
 src=E/f'wallpapers/hannah_montana_{n}.png';im=Image.open(src)
 pkg=P/f'usr/share/wallpapers/HannahMontana{n}'
 images=pkg/'contents/images';old=list(images.iterdir())
 for p in old:p.unlink()
 canonical=images/'4096x3072.png';copy(src,canonical)
 # Keep legacy paths working for users who install the HD .deb over version 1.
 for p in old:
  if p==canonical:continue
  if p.suffix.lower() in ['.jpg','.jpeg']:im.convert('RGB').save(p,quality=95,subsampling=0)
  else:os.link(canonical,p)
 thumb=im.copy();thumb.thumbnail((800,600));thumb.save(pkg/'contents/screenshot.png')
 meta=json.loads((pkg/'metadata.json').read_text());meta['KPlugin']['Name']=f'Hannah Montana {n} HD'
 write(pkg/'metadata.json',json.dumps(meta,indent=2)+'\n')
 # Direct legacy wallpapers used by GRUB and older configurations.
 dest=P/'usr/share/wallpapers'/f'hannah_montana_{n}.{ "jpg" if n>=4 else "png"}'
 if n>=4:im.convert('RGB').save(dest,quality=95,subsampling=0)
 else:copy(src,dest)

look=P/'usr/share/plasma/look-and-feel/org.hannahmontana.desktop'
copy(E/'wallpapers/hannah_montana_3.png',look/'contents/splash/background.png')
im=Image.open(E/'wallpapers/hannah_montana_3.png');im.thumbnail((1920,1440))
im.convert('RGB').save(look/'contents/previews/fullscreenpreview.jpg',quality=95)
im.thumbnail((800,600));im.save(look/'contents/previews/preview.png');im.save(look/'contents/previews/splash.png')
full=Image.open(E/'branding/logo-full.png').convert('RGBA')
for rel,width in [('usr/share/sddm/themes/hannah-montana/logo.png',1536),
                 ('usr/share/pixmaps/hannah-montana.png',1024),
                 ('usr/share/plymouth/themes/hannah-montana/watermark.png',768)]:
 dest=P/rel;dest.unlink(missing_ok=True)
 out=full.copy();out.thumbnail((width,width));out.save(dest)
conf=P/'usr/share/sddm/themes/hannah-montana/theme.conf'
text=conf.read_text().replace('/usr/share/sddm/themes/hannah-montana/background.svg',
                             '/usr/share/wallpapers/hannah_montana_3.png')
write(conf,text)
for path in [P/'etc/xdg/kdeglobals',P/'etc/skel/.config/kdeglobals']:
 c=ini(path);c['DesktopIcons']={'Size':'64'};saveini(path,c)
for p in list((P/'etc').rglob('*'))+list((look/'contents/layouts').glob('*.js')):
 if p.is_file() and not p.is_symlink():
  try:t=p.read_text()
  except UnicodeError:continue
  t=t.replace('HannahMontana3/contents/images/1024x768.png','HannahMontana3/contents/images/4096x3072.png')
  if p.suffix=='.js':t=t.replace('Math.max(38, Math.round(gridUnit * 2.5))','Math.max(48, Math.round(gridUnit * 3))')
  write(p,t)
style=P/'usr/share/plasma/desktoptheme/hannah_montana/plasmarc'
write(style,style.read_text().replace('defaultWidth=1024','defaultWidth=4096').replace('defaultHeight=768','defaultHeight=3072'))

control=P/'DEBIAN/control'
write(control,control.read_text().replace('Version: 26.04.1-1','Version: 26.04.1-2')
      .replace('adapted to Plasma 6','restored for Plasma 6 and HiDPI'))
for p in [P/'usr/share/hannah-montana/os-release']:
 write(p,p.read_text().replace('Hannah Montana OS 26.04.1 (','Hannah Montana OS 26.04.1 HD (')
       .replace('Hannah Montana OS community remix','Hannah Montana OS HD community remix'))
readme=P/'usr/share/doc/hannah-montana-artwork/README.es.txt'
write(readme,readme.read_text()+'''\nEdición HD: fondos de 4096x3072, iconos de hasta 512px y variantes HiDPI.
Recursos restaurados con Upscayl 2.15.0. El botón de inicio usa la H original.
Se conservan los colores, la composición y las proporciones originales.
''')
for p in P.rglob('*'):
 if not p.is_symlink():os.chown(p,0,0)
# Temporary registration with dpkg; no standalone updater is delivered.
deb=R/'tmp/hannah-hd.internal.deb'
subprocess.run(['dpkg-deb','--root-owner-group','--build',str(P),str(deb)],check=True)
subprocess.run(['chroot',str(R),'dpkg','-i','/tmp/hannah-hd.internal.deb'],check=True)
deb.unlink()

# Installer branding lives in the installer package and must be changed too.
branding=R/'etc/calamares/branding/hannah-montana'
for name in ['logo.png','icon.png']:
 out=full.copy();out.thumbnail((1536,1536));out.save(branding/name)
copy(E/'wallpapers/hannah_montana_1.png',branding/'welcome.png')
for n in range(1,6):
 old=next(p for p in branding.glob(f'hannah_montana_{n}.*') if p.suffix in ['.png','.jpg'])
 im=Image.open(E/f'wallpapers/hannah_montana_{n}.png')
 if old.suffix=='.jpg':im.convert('RGB').save(old,quality=95,subsampling=0)
 else:copy(E/f'wallpapers/hannah_montana_{n}.png',old)
about=R/'etc/xdg/kcm-about-distrorc'
write(about,about.read_text().replace('Name=Hannah Montana OS','Name=Hannah Montana OS HD'))

assets={}
for p in P.rglob('*'):
 if p.is_file() and not p.is_symlink() and p.suffix.lower() in ['.png','.jpg','.svg','.svgz']:
  rel=p.relative_to(P).as_posix();assets[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in branding.iterdir():
 if p.is_file() and p.suffix in ['.png','.jpg']:
  assets[p.relative_to(R).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
write(B/'artifacts/hd-assets-sha256.json',json.dumps(assets,indent=2)+'\n')
summary={'wallpapers':5,'wallpaper_size':[4096,3072],'icon_identities':len(manifest['icons']),
 'icon_sizes':sizes,'hidpi_scale':2,'registered_icon_directories':len(directories),
 'asset_files':len(assets),'artwork_package_version':'26.04.1-2','tool':'Upscayl 2.15.0'}
write(B/'artifacts/hd-summary.json',json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2),flush=True)
