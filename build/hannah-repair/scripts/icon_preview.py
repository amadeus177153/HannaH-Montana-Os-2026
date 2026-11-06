from PIL import Image,ImageDraw
from pathlib import Path
B=Path('/data/hannah-repair');out=Image.new('RGB',(900,430),'#fff8d1');d=ImageDraw.Draw(out)
keys=['apps/systemsettings.png','apps/org.kde.dolphin.png','apps/org.kde.konsole.png','categories/applications-internet.png','devices/bluetooth.png','apps/preferences-system.png']
for col,name in enumerate(['HD anterior','HD corregida']):
 d.text((col*440+20,12),name,fill='black')
 for i,key in enumerate(keys):
  root=Path('/data/hannah-hd/rootfs') if col==0 else B/'rootfs'
  p=root/'usr/share/icons/hannah_montana/128x128'/key
  if p.exists():
   im=Image.open(p).convert('RGBA');im.thumbnail((100,100));x=col*440+(i%3)*140+20;y=45+(i//3)*180
   out.paste(im,(x,y),im);d.text((x,y+105),Path(key).stem[:20],fill='black')
out.save(B/'artifacts/comparacion-iconos.png')
