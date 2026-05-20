#!/usr/bin/env bash
# Render each paper/figures/fig-*.tex to a standalone PDF + PNG
# so the web client can embed the figures inline beside the proof
# on the claim page.
#
# Why this exists: each fig-*.tex defines a `\begin{figure}` wrapping
# a `\begin{tikzpicture}`. When the main paper builds, those figures
# float into the rendered PDF. To show a single figure inline on a
# claim page, we need it as a standalone image — that's what this
# script produces.
#
# Output: paper/figures/fig-<id>.{pdf,png}, one of each per source
# .tex file. The .pdf is the tectonic-compiled vector; the .png is
# a 300dpi rasterisation via ImageMagick (which delegates to
# ghostscript for PDF parsing). The .png is what the web client
# embeds — vector via SVG would be nicer but requires an extra
# poppler/dvisvgm install; PNG-at-300dpi is indistinguishable from
# vector at the sizes we render inline.
#
# Requires: tectonic, magick (ImageMagick 7), gs (Ghostscript).
#
# Usage:
#   ./scripts/render-figures.sh           # render all
#   ./scripts/render-figures.sh fig-i-1   # render one

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FIG_DIR="$ROOT/paper/figures"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

for tool in tectonic magick gs; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "ERROR: $tool not found in PATH." >&2
    echo "Install:" >&2
    case "$tool" in
      tectonic) echo "  brew install tectonic" >&2 ;;
      magick) echo "  brew install imagemagick" >&2 ;;
      gs) echo "  brew install ghostscript" >&2 ;;
    esac
    exit 127
  fi
done

# Filter to a specific figure if a stem was passed; otherwise render all.
if [[ $# -gt 0 ]]; then
  TARGETS=()
  for stem in "$@"; do
    [[ -f "$FIG_DIR/${stem}.tex" ]] || { echo "missing: $FIG_DIR/${stem}.tex" >&2; exit 2; }
    TARGETS+=("$FIG_DIR/${stem}.tex")
  done
else
  TARGETS=("$FIG_DIR"/fig-*.tex)
fi

PREAMBLE='\documentclass[tikz, border=2pt]{standalone}
\usepackage{tikz}
\usetikzlibrary{calc, angles, quotes, intersections, through}
\begin{document}'
POSTAMBLE='\end{document}'

for tex in "${TARGETS[@]}"; do
  stem="$(basename "$tex" .tex)"
  out_pdf="$FIG_DIR/${stem}.pdf"
  out_png="$FIG_DIR/${stem}.png"

  # Each fig-*.tex is wrapped in a `\begin{figure}[H]` ... `\caption{}`
  # block — strip those and keep only the `tikzpicture` for the
  # standalone wrapper. We also drop the `\label` (which the
  # standalone build doesn't need).
  tikzpic=$(awk '
    /\\begin{tikzpicture}/ { capture=1 }
    capture { print }
    /\\end{tikzpicture}/ { capture=0 }
  ' "$tex")

  if [[ -z "$tikzpic" ]]; then
    echo "warn: no \\begin{tikzpicture}…\\end{tikzpicture} block found in $tex, skipping" >&2
    continue
  fi

  wrapped_tex="$WORK_DIR/${stem}.tex"
  printf '%s\n%s\n%s\n' "$PREAMBLE" "$tikzpic" "$POSTAMBLE" > "$wrapped_tex"

  # Tectonic chatters about cache hits + xdvipdfmx; redirect noise.
  tectonic --outdir "$WORK_DIR" "$wrapped_tex" >/dev/null 2>&1 || {
    echo "ERROR: tectonic failed on $stem.tex" >&2
    continue
  }

  cp "$WORK_DIR/${stem}.pdf" "$out_pdf"
  # IM7 syntax: density before input, background+flatten after, so the
  # alpha channel is composed against a solid white before encoding the
  # PNG (avoids a transparent background that disappears against a dark
  # site theme).
  magick -density 300 -background white "$out_pdf" -flatten "$out_png"

  size_pdf=$(wc -c < "$out_pdf" | tr -d ' ')
  size_png=$(wc -c < "$out_png" | tr -d ' ')
  echo "rendered $stem: pdf=${size_pdf}B png=${size_png}B"
done

echo "Done. Outputs in $FIG_DIR/*.{pdf,png}"
