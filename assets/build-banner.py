#!/usr/bin/env python3
"""GitHub プロフィール README のヘッダーバナー（1600x420）を作る。

  python3 assets/build-banner.py

minoruonda.com / OGP 画像と同じ「大粒タイルの斜めウェーブ」を横長に組み直したもの。
SVG を書き出して rsvg-convert で PNG に焼く。

GitHub は README の画像を camo プロキシ経由で配信するため、SVG のまま置くと
文字が閲覧者側のフォントで描画されて崩れる。Mac のヒラギノでレンダリング済みの
PNG にすることで、どの環境から見ても同じ見た目になる。
"""
import math
import pathlib
import random
import subprocess
import sys

W, H = 1600, 400

NAVY = "#052a5a"
BLUE = "#0a4695"
BLUE_MID = "#0862aa"
BLUE_BRIGHT = "#01b6ec"
ACCENT_SOFT = "#d8f5ff"
SILVER = "#d9e1e8"
GOLD = "#f0b21f"


def lerp(a, b, t):
    return a + (b - a) * t


def hex2rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def ramp(t, stops):
    t = max(0.0, min(1.0, t))
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        if p0 <= t <= p1:
            u = 0 if p1 == p0 else (t - p0) / (p1 - p0)
            r0, g0, b0 = hex2rgb(c0)
            r1, g1, b1 = hex2rgb(c1)
            return "#%02x%02x%02x" % (int(lerp(r0, r1, u)),
                                      int(lerp(g0, g1, u)),
                                      int(lerp(b0, b1, u)))
    return stops[-1][1]


def diagonal_wave(seed=41, cell=46):
    """左下から右上へ流れる大粒タイル。文字を置く左側は薄く、右上ほど密にする。"""
    rnd = random.Random(seed)
    stops = [(0.0, BLUE), (0.42, BLUE_MID), (0.75, "#0a8dcc"), (1.0, BLUE_BRIGHT)]
    out = []
    for gy in range(-cell, H + cell, cell):
        for gx in range(0, W + cell, cell):
            # 中心線は左下→右上。sin の揺れで直線的にしない。
            line_y = 486 - 0.28 * gx + 38 * math.sin(gx / 210 + 1.1)
            band = max(0.0, 1.0 - abs(gy - line_y) / 205)
            if band <= 0:
                continue
            # 左 1/3 は文字が乗るので、出現率を落として静かにする。
            left_damp = min(1.0, 0.30 + gx / (W * 0.52))
            if rnd.random() > (0.16 + band * 0.70) * left_damp:
                continue
            progress = max(0.0, min(1.0, gx / W))
            size = cell * lerp(0.50, 0.88, band)
            op = lerp(0.28, 0.92, band) * lerp(0.55, 1.0, left_damp)
            col = ramp(progress, stops)
            if band > 0.60 and rnd.random() < 0.06:
                col = ACCENT_SOFT
            ox, oy = gx + (cell - size) / 2, gy + (cell - size) / 2
            out.append(f'<rect x="{ox:.1f}" y="{oy:.1f}" width="{size:.1f}" '
                       f'height="{size:.1f}" rx="{size * 0.12:.1f}" '
                       f'fill="{col}" opacity="{op:.2f}"/>')
    return "\n".join(out)


def build_svg():
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{NAVY}"/><stop offset="46%" stop-color="{BLUE}"/><stop offset="76%" stop-color="{BLUE_MID}"/><stop offset="100%" stop-color="{BLUE_BRIGHT}"/>
  </linearGradient>
  <linearGradient id="veil" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#031f45" stop-opacity=".62"/>
    <stop offset="46%" stop-color="#031f45" stop-opacity=".18"/>
    <stop offset="100%" stop-color="#031f45" stop-opacity="0"/>
  </linearGradient>
</defs>
<style>
  .en   {{ font-family: "Helvetica Neue",Arial,sans-serif; font-weight: 700; letter-spacing: 7px; fill: {ACCENT_SOFT}; }}
  .name {{ font-family: "Hiragino Sans","Hiragino Kaku Gothic ProN",sans-serif; font-weight: 800; fill: #fff; }}
  .id   {{ font-family: "Helvetica Neue",Arial,sans-serif; font-weight: 700; fill: #fff; opacity: .88; }}
  .lead {{ font-family: "Hiragino Sans","Hiragino Kaku Gothic ProN",sans-serif; font-weight: 600; fill: #fff; opacity: .93; }}
  .role {{ font-family: "Hiragino Sans","Hiragino Kaku Gothic ProN",sans-serif; font-weight: 600; fill: {ACCENT_SOFT}; }}
</style>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
{diagonal_wave()}
<rect width="{W}" height="{H}" fill="url(#veil)"/>

<text class="en"   x="104" y="112" font-size="32">MINORU ONDA</text>
<text class="name" x="100" y="238" font-size="104">みのるん</text>
<text class="id"   x="540" y="236" font-size="38">@minorun365</text>
<rect x="103" y="278" width="104" height="7" rx="3.5" fill="{GOLD}"/>
<text class="lead" x="103" y="342" font-size="38">AIエージェントと開発者向けツールを作っています</text>
</svg>
'''


def main():
    here = pathlib.Path(__file__).resolve().parent
    svg_path = here / "banner.svg"
    png_path = here / "banner.png"
    svg_path.write_text(build_svg())
    subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H),
                    "-o", str(png_path), str(svg_path)], check=True)
    print(f"生成: {png_path.name}（{png_path.stat().st_size // 1024}KB）")


if __name__ == "__main__":
    sys.exit(main())
