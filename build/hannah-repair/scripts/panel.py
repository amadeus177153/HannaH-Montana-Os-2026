from pathlib import Path
import configparser,io
R=Path('/data/hannah-repair/rootfs');icons=R/'usr/share/icons/hannah_montana';n=0
for p in icons.rglob('*.png'):
 if p.parent.name=='status' or p.stem.startswith(('audio-','network-','bluetooth','battery','input-keyboard','notification')):
  p.unlink();n+=1
f=icons/'index.theme';c=configparser.ConfigParser(interpolation=None);c.optionxform=str;c.read(f);c['Icon Theme']['FollowsColorScheme']='true'
s=io.StringIO();c.write(s,space_around_delimiters=False);f.write_text(s.getvalue())
print('Modern inherited status icons; removed',n,'legacy overrides')
