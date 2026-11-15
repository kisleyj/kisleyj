#!/usr/bin/env python3
"""Renderiza o SVG dinâmico do JeffersonOS em um GIF de animação discreta.

Cada execução usa o SVG atual: as estatísticas no GIF acompanham o workflow.
Sem JS, sem fontes externas, sem chamadas à internet. Os pixels estáticos
permanecem idênticos em todos os quadros; só reflexo/borda/indicador se movem.
"""
from __future__ import annotations

import io
import math
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'assets' / 'dashboard-red.svg'
DEST = ROOT / 'assets' / 'dashboard-red.gif'
PREVIEW = ROOT / 'preview-dashboard-red-animado.png'

# 16 quadros a 160 ms: loop 2,56 s. Reflexo e brilho suaves, sem piscar rápido.
FRAMES = 16
DURATION_MS = 160
WIDTH, HEIGHT = 1044, 648  # 90% do SVG, legível e mais leve que 1160×720.


def base_image() -> Image.Image:
    raster = cairosvg.svg2png(url=str(SOURCE), output_width=WIDTH,
                              output_height=HEIGHT)
    return Image.open(io.BytesIO(raster)).convert('RGB')


def frame(base: Image.Image, k: int) -> Image.Image:
    t = k / FRAMES
    w, h = base.size
    scale = w / 1160
    colored = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    brush = ImageDraw.Draw(colored, 'RGBA')
    # Reflexo fino no vidro; não passa por cima dos números.
    x = int((64 + 1050 * t) * scale)
    y = round(7 * scale)
    right = min(w - 18, x + round(108 * scale))
    brush.line([(x, y), (right, y)], fill=(255, 200, 211, 120), width=max(1, round(2*scale)))
    # Brilho suave correndo na borda superior, sem flash.
    halo = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    hh = ImageDraw.Draw(halo, 'RGBA')
    hh.ellipse((x-25, y-13, x+62, y+15), fill=(247, 72, 107, 48))
    halo = halo.filter(ImageFilter.GaussianBlur(radius=9))
    colored.alpha_composite(halo)
    # Indicador de atividade respirando calmamente, sem implicar servidor online.
    alpha = round(100 + 85 * (0.5 + 0.5 * math.sin(t * 2 * math.pi)))
    cx, cy, rad = round(1092*scale), round(41*scale), round(3.5*scale)
    brush.ellipse((cx-rad, cy-rad, cx+rad, cy+rad), fill=(245, 115, 133, alpha))
    out = Image.alpha_composite(base.convert('RGBA'), colored)
    return out.convert('RGB')


def main() -> None:
    base = base_image()
    frames = [frame(base, k) for k in range(FRAMES)]
    # Paleta única compartilhada evita cintilação de cores ao alternar quadros.
    palette_image = base.quantize(colors=192, method=Image.Quantize.MEDIANCUT)
    frames_pal = [im.quantize(palette=palette_image, dither=Image.Dither.NONE)
                  for im in frames]
    dest_tmp = DEST.with_suffix('.tmp.gif')
    frames_pal[0].save(dest_tmp, format='GIF', save_all=True,
                       append_images=frames_pal[1:], optimize=True,
                       duration=DURATION_MS, loop=0, disposal=2)
    if not DEST.exists() or DEST.read_bytes() != dest_tmp.read_bytes():
        dest_tmp.replace(DEST)
        print(f'GIF atualizado: {DEST.name}; {FRAMES} quadros; {DEST.stat().st_size // 1024} KiB')
    else:
        dest_tmp.unlink()
        print('GIF sem mudanças — nenhuma alteração no histórico.')
    frames[4].save(PREVIEW, optimize=True)


if __name__ == '__main__':
    main()
