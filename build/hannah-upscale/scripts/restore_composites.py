#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import subprocess,json,hashlib
B=Path('/mnt/discoo/OsISO/hannah-upscale')
O=B.parent/'hannah-modern/original-root/usr/share/wallpapers'
inputs=B/'work/composite-photos';inputs.mkdir(exist_ok=True)
outputs=B/'work/composite-photos-4x';outputs.mkdir(exist_ok=True)
for n in [1,3]:
    Image.open(O/f'hannah_montana_{n}.png').convert('RGBA').save(inputs/f'{n}.png')
engine=B/'tools/squashfs-root/resources/bin/upscayl-bin'
with (B/'logs/upscayl-composites.log').open('w') as log:
    subprocess.run([str(engine),'-i',str(inputs),'-o',str(outputs),'-m',str(engine.parent.parent/'models'),
                    '-n','high-fidelity-4x','-s','4','-t','128','-j','1:1:2'],stdout=log,stderr=log,check=True)
for n in [1,3]:
    src=Image.open(O/f'hannah_montana_{n}.png').convert('RGBA')
    size=(4096,3072)
    ai=Image.open(outputs/f'{n}.png').convert('RGBA').resize(size,Image.Resampling.LANCZOS)
    base=src.resize(size,Image.Resampling.LANCZOS)
    # Preserve recognizable photographic detail and tiny original lettering.
    out=Image.blend(base,ai,0.65)
    # The Tux shirt contains a very small printed logo. Retain that source detail.
    box=(round(size[0]*.83),round(size[1]*.055),size[0],round(size[1]*.28))
    out.paste(Image.blend(base.crop(box),ai.crop(box),0.20),box)
    out.putalpha(base.getchannel('A'))
    out.save(B/f'enhanced/wallpapers/hannah_montana_{n}.png',compress_level=6)
    out.resize((1024,768),Image.Resampling.LANCZOS).save(B/f'artifacts/wallpaper-{n}-final-preview.png')
print('Composite photographic regions restored with high-fidelity model and original detail retention')
