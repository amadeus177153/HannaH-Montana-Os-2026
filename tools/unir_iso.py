#!/usr/bin/env python3
"""Join this release's ISO parts after checking all SHA-256 hashes (Python 3)."""
import hashlib
from pathlib import Path
import sys

NAME = 'hannah-montana-os-26.04.1-2026-amd64.iso'
SHA256 = '0e8320f72fbbd5a646f155ad03944cd74ac4404cf83d6e5a4686eb59a8641668'
SIZE = 5554634752
PART_SIZE = 1900000000


def join(folder):
    output = folder / NAME
    partial = folder / (NAME + '.tmp')
    parts = [folder / (NAME + '.part%03d' % i) for i in range(1, 4)]
    if output.exists():
        raise ValueError('La ISO de destino ya existe; no se sobrescribió: ' + str(output))
    entries = {}
    for line in (folder / 'SHA256SUMS.parts').read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        if name in entries or len(digest) != 64:
            raise ValueError('Manifiesto de partes inválido')
        entries[name] = digest
    if set(entries) != {p.name for p in parts}:
        raise ValueError('El manifiesto debe contener exactamente las tres partes esperadas')
    for i, part in enumerate(parts):
        expected = PART_SIZE if i < 2 else SIZE - 2 * PART_SIZE
        if part.stat().st_size != expected:
            raise ValueError('Parte incompleta o incorrecta: ' + part.name)
    full = hashlib.sha256()
    # Exclusive creation also protects an existing interrupted output.
    with partial.open('xb') as target:
        try:
            for part in parts:
                print('Verificando y uniendo ' + part.name, flush=True)
                digest = hashlib.sha256()
                with part.open('rb') as source:
                    for chunk in iter(lambda: source.read(8 * 1024 * 1024), b''):
                        digest.update(chunk)
                        full.update(chunk)
                        target.write(chunk)
                if digest.hexdigest() != entries[part.name]:
                    raise ValueError('SHA-256 incorrecto: ' + part.name)
            if target.tell() != SIZE or full.hexdigest() != SHA256:
                raise ValueError('La ISO completa no coincide con la versión publicada')
        except BaseException:
            target.close()
            partial.unlink()
            raise
    # Check again in case another process created the destination while joining.
    if output.exists():
        raise ValueError('El destino apareció durante la unión; se conserva el archivo .tmp')
    partial.rename(output)
    print('ISO reconstruida y SHA-256 verificado: ' + str(output))


if __name__ == '__main__':
    try:
        join(Path(sys.argv[1]) if len(sys.argv) == 2 else Path(__file__).resolve().parent)
    except (OSError, ValueError) as exc:
        print('Error: ' + str(exc), file=sys.stderr)
        sys.exit(1)
