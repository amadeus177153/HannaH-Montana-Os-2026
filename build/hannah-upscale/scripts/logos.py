#!/usr/bin/env python3
"""Recover the original large logo instead of enlarging its 32px thumbnail."""
from PIL import Image, ImageChops, ImageDraw, ImageOps, ImageFilter
from pathlib import Path
import json,hashlib
B=Path('/mnt/discoo/OsISO/hannah-upscale')
im=Image.open(B/'enhanced/wallpapers/hannah_montana_2.png').convert('RGBA')
h,s,v=im.convert('HSV').split()
purple=h.point(lambda x: 255 if 180 <= x <= 240 else 0)
saturated=s.point(lambda x: 255 if x >= 120 else 0)
background=ImageChops.multiply(purple,saturated)
alpha=ImageChops.invert(background)
# Remove isolated texture specks from the purple background; the letters'
# thick original outlines remain. Work at full resolution before downsampling.
alpha=alpha.filter(ImageFilter.MinFilter(7)).filter(ImageFilter.MaxFilter(7))
im.putalpha(alpha)
logo=im.crop(alpha.getbbox())
logo=ImageOps.expand(logo,border=40,fill=(0,0,0,0))
(B/'enhanced/branding').mkdir(parents=True,exist_ok=True)
logo.save(B/'enhanced/branding/logo-full.png')
# The original H emblem remains recognizable at a 32–48px launcher size.
# The complete lettering is used for the wider login/installer/boot areas.
points=[(16,255),(157,249),(137,328),(190,314),(221,258),
        (267,253),(240,345),(286,330),(395,12),(327,34),
        (283,169),(239,173),(286,53),(225,73),(181,196),(45,207)]
scale=im.width/800
mask=Image.new('L',im.size)
ImageDraw.Draw(mask).polygon([(round(x*scale),round(y*scale)) for x,y in points],fill=255)
emblem=im.copy()
emblem.putalpha(ImageChops.multiply(alpha,mask))
emblem=emblem.crop(emblem.getchannel('A').getbbox())
square=Image.new('RGBA',(max(emblem.size)+80,)*2)
square.alpha_composite(emblem,((square.width-emblem.width)//2,(square.height-emblem.height)//2))
square.resize((1024,1024),Image.Resampling.LANCZOS).save(B/'enhanced/branding/launcher.png')
preview=Image.new('RGB',(1100,650),'#6c26cf')
thumb=logo.copy();thumb.thumbnail((1000,390))
preview.paste(thumb,((1100-thumb.width)//2,15),thumb)
for i,size in enumerate([32,48,64,128]):
 icon=square.resize((size,size),Image.Resampling.LANCZOS)
 icon=icon.resize((size*2,size*2),Image.Resampling.NEAREST)
 preview.paste(icon,(100+i*245,450),icon)
preview.save(B/'artifacts/branding-preview.png')
print('Recovered full logo',logo.size,'and original H emblem',square.size)
