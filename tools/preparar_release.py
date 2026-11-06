#!/usr/bin/env python3
"""Prepare GitHub release parts without changing the original ISO."""
import hashlib
from pathlib import Path
import shutil
import sys

NAME = 'hannah-montana-os-26.04.1-2026-amd64.iso'
EXPECTED = '0e8320f72fbbd5a646f155ad03944cd74ac4404cf83d6e5a4686eb59a8641668'
SIZE = 5554634752
PART_SIZE = 1900000000


def prepare(source, folder):
    if source.stat().st_size != SIZE:
        raise ValueError('Tamaño inesperado de la ISO')
    folder.mkdir(parents=True, exist_ok=False)
    digest = hashlib.sha256()
    entries = []
    with source.open('rb') as image:
        for index in range(1, 4):
            name = NAME + '.part%03d' % index
            part_digest = hashlib.sha256()
            remaining = min(PART_SIZE, SIZE - (index - 1) * PART_SIZE)
            with (folder / name).open('xb') as target:
                while remaining:
                    chunk = image.read(min(8 * 1024 * 1024, remaining))
                    if not chunk:
                        raise ValueError('ISO truncada')
                    digest.update(chunk)
                    part_digest.update(chunk)
                    target.write(chunk)
                    remaining -= len(chunk)
            entries.append(part_digest.hexdigest() + '  ' + name + '\n')
            print('Preparada ' + name, flush=True)
        if image.read(1) or digest.hexdigest() != EXPECTED:
            raise ValueError('La ISO no coincide con la versión validada; no publicar las partes')
    (folder / 'SHA256SUMS.parts').write_text(''.join(entries))
    (folder / 'SHA256SUMS').write_text(EXPECTED + '  ' + NAME + '\n')
    shutil.copy2(Path(__file__).with_name('unir_iso.py'), folder / 'unir_iso.py')
    print('ISO de origen verificada. Partes listas en ' + str(folder), flush=True)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('Uso: python preparar_release.py ISO DIRECTORIO_NUEVO')
    try:
        prepare(Path(sys.argv[1]), Path(sys.argv[2]))
    except (OSError, ValueError) as exc:
        sys.exit(str(exc))
