#!/usr/bin/env bash
# Publish only after every asset has uploaded successfully. Existing releases are untouched.
set -euo pipefail
repo='amadeus177153/HannaH-Montana-Os-2026'
tag='v26.04.1-2026'
script_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
release_dir="${1:?Uso: publicar_release.sh DIRECTORIO_DE_PARTES}"
iso='hannah-montana-os-26.04.1-2026-amd64.iso'
gh auth status --hostname github.com
(cd -- "$release_dir" && sha256sum -c SHA256SUMS.parts)
assets=("$release_dir/$iso.part001" "$release_dir/$iso.part002" "$release_dir/$iso.part003" "$release_dir/SHA256SUMS" "$release_dir/SHA256SUMS.parts" "$release_dir/unir_iso.py")
for asset in "${assets[@]}"; do test -f "$asset"; done
gh release create "$tag" --repo "$repo" --target main --draft \
  --title 'Hannah Montana OS 26.04.1 · Edición 2026' \
  --notes-file "$script_dir/../docs/RELEASE.md"
for asset in "${assets[@]}"; do
  gh release upload "$tag" "$asset" --repo "$repo"
done
gh release edit "$tag" --repo "$repo" --draft=false --latest
gh release view "$tag" --repo "$repo" --json url,assets
