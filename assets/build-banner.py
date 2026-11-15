#!/usr/bin/env python3
"""GitHub プロフィール README のヘッダーバナー（1600x400）を作る。

  python3 assets/build-banner.py

個人テーマ minorun-glass の表紙（淡いターコイズの地＋右端の輪）を横長に組み直したもの。
SVG を書き出して rsvg-convert で PNG に焼く。

GitHub は README の画像を camo プロキシ経由で配信するため、SVG のまま置くと
文字が閲覧者側のフォントで描画されて崩れる。Mac の凸版文久見出しゴシックでレンダリング済みの
PNG にすることで、どの環境から見ても同じ見た目になる。
"""
import math
import pathlib
import random
import subprocess
import sys

W, H = 1600, 400

# minorun-glass（personal/marp/theme/minorun-glass.css）の表紙と同じ骨格：
# 淡いターコイズの地に、右端から青→ターコイズの輪が覗く。名前は凸版文久見出しゴシックの濃い墨。
BG = "#f1fafc"
TITLE = "#0d1b24"
INK = "#3b4c57"
TEAL = "#0891b2"
# CSS の conic-gradient(from 200deg, ...) と同じ色の並び
RING_STOPS = [(0.0, "#0284c7"), (0.2, "#06b6d4"), (0.4, "#22d3ee"),
              (0.6, "#a5f3fc"), (0.8, "#ecfeff"), (1.0, "#0284c7")]


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
            return "#%02x%02x%02x" % (round(lerp(r0, r1, u)),
                                      round(lerp(g0, g1, u)),
                                      round(lerp(b0, b1, u)))
    return stops[-1][1]


# 輪：スライド（1280x720）では直径560px・右へ300px はみ出し・上下中央。
# バナーは高さ400px なので直径を 0.8 倍にし、同じ割合だけ右へはみ出させる。
RING_D = 448
RING_R = RING_D / 2
RING_IN = RING_R * 0.62          # mask: transparent 0 62%
RING_CX = W + 300 * 0.8 - RING_R  # 右端から 240px はみ出す
RING_CY = H / 2


def ring():
    """SVG に conic-gradient が無いので、0.5度刻みの扇形を並べて輪を描く。"""
    out = []
    step = 0.5
    a = 0.0
    while a < 360:
        t = a / 360
        col = ramp(t, RING_STOPS)
        pts = []
        for ang, rad in ((a, RING_R), (a + step + 0.15, RING_R),
                         (a + step + 0.15, RING_IN), (a, RING_IN)):
            th = math.radians(200 + ang)       # CSS の conic は上が0度・時計回り
            pts.append(f"{RING_CX + rad * math.sin(th):.2f},{RING_CY - rad * math.cos(th):.2f}")
        out.append(f'<polygon points="{" ".join(pts)}" fill="{col}"/>')
        a += step
    return "\n".join(out)


# ── 名前ブロックを上下中央へ置くための計算 ───────────────────────
# 「英字の視覚的な上端」から「グラデーションの短い線の下端」までを1つの塊とみなし、
# その中点が H/2 に来るようベースラインを逆算する。
EN_FS, NAME_FS = 28, 100
GAP = 118                      # 英字と名前のベースライン間隔
CAP = EN_FS * 0.72
LINE_GAP, LINE_H = 34, 8       # 名前のベースラインから線の上端まで、線の太さ
BLOCK = CAP + GAP + LINE_GAP + LINE_H
EN_Y = round((H - BLOCK) / 2 + CAP)
NAME_Y = EN_Y + GAP
ID_Y = NAME_Y - 4
LINE_Y = NAME_Y + LINE_GAP


def build_svg():
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <radialGradient id="glow1" gradientUnits="userSpaceOnUse" cx="{W * 0.76:.0f}" cy="{H * 0.08:.0f}" r="520">
    <stop offset="0%" stop-color="#22d3ee" stop-opacity=".24"/><stop offset="70%" stop-color="#22d3ee" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="glow2" gradientUnits="userSpaceOnUse" cx="0" cy="{H}" r="420">
    <stop offset="0%" stop-color="#0ea5e9" stop-opacity=".08"/><stop offset="70%" stop-color="#0ea5e9" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="line" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#0ea5e9"/><stop offset="100%" stop-color="#22d3ee"/>
  </linearGradient>
</defs>
<style>
  .en   {{ font-family: "Toppan Bunkyu Midashi Gothic","Hiragino Sans",sans-serif; letter-spacing: 6px; fill: {TEAL}; }}
  .name {{ font-family: "Toppan Bunkyu Midashi Gothic","Hiragino Sans",sans-serif; fill: {TITLE}; letter-spacing: 2px; }}
  .id   {{ font-family: "Toppan Bunkyu Midashi Gothic","Hiragino Sans",sans-serif; fill: {INK}; }}
</style>
<rect width="{W}" height="{H}" fill="{BG}"/>
<rect width="{W}" height="{H}" fill="url(#glow1)"/>
<rect width="{W}" height="{H}" fill="url(#glow2)"/>
{ring()}

<text class="en"   x="106" y="{EN_Y}" font-size="{EN_FS}">MINORU ONDA</text>
<text class="name" x="100" y="{NAME_Y}" font-size="{NAME_FS}">みのるん</text>
<text class="id"   x="545" y="{ID_Y}" font-size="38">@minorun365</text>
<rect x="106" y="{LINE_Y}" width="120" height="{LINE_H}" rx="4" fill="url(#line)"/>
</svg>
'''


def main():
    here = pathlib.Path(__file__).resolve().parent
    # ⚠️ 同じファイル名で中身だけ差し替えると、GitHub や閲覧者のブラウザが
    #    古い画像をキャッシュから返し続ける。見た目を変えたらファイル名も上げる。
    svg_path = here / "banner.svg"
    png_path = here / "banner-v5.png"
    svg_path.write_text(build_svg())
    subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H),
                    "-o", str(png_path), str(svg_path)], check=True)
    print(f"生成: {png_path.name}（{png_path.stat().st_size // 1024}KB）")


if __name__ == "__main__":
    sys.exit(main())
