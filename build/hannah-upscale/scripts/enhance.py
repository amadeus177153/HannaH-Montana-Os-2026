#!/usr/bin/env python3
"""Upscayl batch restoration from the best original source of each icon."""
from pathlib import Path
from PIL import Image, ImageOps
import collections
import hashlib
import json
import math
import os
import shutil
import subprocess
import time

B = Path('/mnt/discoo/OsISO/hannah-upscale')
O = B.parent / 'hannah-modern/original-root'
ENGINE = B / 'tools/squashfs-root/resources/bin/upscayl-bin'
MODELS = ENGINE.parent.parent / 'models'
manifest = {'tool': 'Upscayl 2.15.0', 'icons': {}, 'wallpapers': {}, 'sources': {}}

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def run_batch(inputs, outputs, model, logname):
    outputs.mkdir(parents=True, exist_ok=True)
    pending = [p for p in inputs.glob('*.png') if not (outputs / p.name).exists()]
    if not pending:
        return
    # Resume without recomputing completed images or reloading a model per file.
    todo = inputs.parent / (inputs.name + '-pending')
    if todo.exists(): shutil.rmtree(todo)
    todo.mkdir()
    for p in pending: os.link(p, todo / p.name)
    print(f'{logname}: processing {len(pending)} images using {model}', flush=True)
    with (B / 'logs' / logname).open('w') as log:
        subprocess.run([str(ENGINE), '-i', str(todo), '-o', str(outputs),
            '-m', str(MODELS), '-n', model, '-s', '4', '-t', '128',
            '-j', '1:1:2', '-f', 'png'], stdout=log, stderr=log, check=True)
    assert all((outputs / p.name).is_file() for p in pending)

def record_source(p, im):
    k = str(p.relative_to(O))
    manifest['sources'][k] = {'sha256': sha(p), 'size': list(im.size)}
    return k

# Wallpaper masters: preserve original aspect ratio and colors; select the
# photo model only for the two photographs, and digital art for the composites.
for group, numbers, model in [('art', [1,2,3], 'digital-art-4x'),
                               ('photo', [4,5], 'high-fidelity-4x')]:
    inputs = B / 'work' / ('wallpapers-' + group)
    outputs = B / 'work' / ('wallpapers-' + group + '-4x')
    inputs.mkdir(parents=True, exist_ok=True)
    sources = {}
    for n in numbers:
        p = next((O / 'usr/share/wallpapers').glob(f'hannah_montana_{n}.*'))
        im = Image.open(p).convert('RGBA')
        im.save(inputs / f'{n}.png')
        sources[n] = p
    run_batch(inputs, outputs, model, f'upscayl-wallpapers-{group}.log')
    dest = B / 'enhanced/wallpapers'
    dest.mkdir(parents=True, exist_ok=True)
    for n, p in sources.items():
        orig = Image.open(p).convert('RGBA')
        src = record_source(p, orig)
        ai = Image.open(outputs / f'{n}.png').convert('RGBA')
        size = (4096, round(orig.height * 4096 / orig.width))
        ai = ai.resize(size, Image.Resampling.LANCZOS)
        # Original opacity is authoritative; never invent opaque backgrounds.
        ai.putalpha(orig.getchannel('A').resize(size, Image.Resampling.LANCZOS))
        output = dest / f'hannah_montana_{n}.png'
        ai.save(output, compress_level=6)
        manifest['wallpapers'][str(n)] = {'source': src, 'output': str(output.relative_to(B)),
            'size': list(size), 'model': model, 'sha256': sha(output)}
        print(f'Wallpaper {n}: {orig.size} -> {size}', flush=True)

# Identify one best source for every icon name/context, irrespective of the
# inaccurate nominal dimensions in some directories of the 2009 theme.
icon_root = O / 'usr/share/icons/hannah_montana'
groups = collections.defaultdict(list)
for p in icon_root.rglob('*.png'):
    try:
        with Image.open(p) as im:
            rel = p.relative_to(icon_root)
            if len(rel.parts) < 3: continue
            groups['/'.join(rel.parts[1:])].append((im.width * im.height, p))
    except (OSError, ValueError):
        continue
inputs = B / 'work/icons'
outputs = B / 'work/icons-4x'
inputs.mkdir(parents=True, exist_ok=True)
plans = {}
for key, choices in groups.items():
    p = max(choices, key=lambda x: x[0])[1]
    im = Image.open(p).convert('RGBA')
    record_source(p, im)
    frames = []
    is_strip = key.startswith('animations/') and im.height > im.width * 2
    count = math.ceil(im.height / im.width) if is_strip else 1
    for i in range(count):
        frame = im.crop((0, i * im.width, im.width, (i+1) * im.width)) if is_strip else im
        digest = hashlib.sha256(frame.tobytes() + str(frame.size).encode()).hexdigest()
        target = inputs / (digest + '.png')
        if not target.exists(): frame.save(target)
        frames.append(digest)
    plans[key] = {'source': str(p.relative_to(O)), 'source_size': list(im.size),
                   'frames': frames, 'strip': is_strip}
print(f'Icons: {len(groups)} identities; {len(list(inputs.glob("*.png")))} unique source frames', flush=True)
run_batch(inputs, outputs, 'digital-art-4x', 'upscayl-icons.log')
dest = B / 'enhanced/icons'
dest.mkdir(parents=True, exist_ok=True)
for key, plan in plans.items():
    orig = Image.open(O / plan['source']).convert('RGBA')
    if plan['strip']:
        width = orig.width * 4
        result = Image.new('RGBA', (width, orig.height * 4))
        for i, digest in enumerate(plan['frames']):
            frame = Image.open(outputs / (digest+'.png')).convert('RGBA')
            result.paste(frame, (0, i * width))
    else:
        result = Image.open(outputs / (plan['frames'][0]+'.png')).convert('RGBA')
    result.putalpha(orig.getchannel('A').resize(result.size, Image.Resampling.LANCZOS))
    target = dest / key
    target.parent.mkdir(parents=True, exist_ok=True)
    result.save(target, compress_level=6)
    manifest['icons'][key] = {**plan, 'output': str(target.relative_to(B)),
                              'size': list(result.size), 'sha256': sha(target)}
(B / 'artifacts/enhancement-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(f'Finished: {len(manifest["wallpapers"])} wallpapers, {len(manifest["icons"])} icon identities', flush=True)
