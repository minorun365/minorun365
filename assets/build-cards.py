#!/usr/bin/env python3
"""README に並べるリポジトリカードを作る（ライト/ダークの2枚ずつ）。

  python3 assets/build-cards.py

GitHub の README は CSS が使えず、style 属性もサニタイズで剥がされる。
角丸・影・余白を持つカードを出すには、カードそのものを画像にするしかない。
背景を透明にした PNG を <picture> でライト/ダーク切り替えして貼る。

カードに載せるのはタイトル・スター数・言語だけにする。画像は縮尺が固定なので、
スマホの2列表示（1枚180px相当）まで縮むと細かい文字が読めなくなるため、
説明文は README 側にテキストで置く（テキストならブラウザが可読サイズを保つ）。

スター数は生成時点の値で焼き込まれる。増えたら再実行すれば更新される。
"""
import pathlib
import subprocess
import sys

OUT_DIR = pathlib.Path(__file__).resolve().parent / "cards"

W, H = 500, 180
RADIUS = 18

# GitHub のライト/ダーク両テーマの実際の色に合わせる。カードだけ浮かないようにするため。
THEMES = {
    "light": dict(bg="#ffffff", border="#d0d7de", title="#0a4695",
                  body="#57606a", meta="#6e7781", shadow="#0e0d6a"),
    "dark":  dict(bg="#161b22", border="#30363d", title="#58a6ff",
                  body="#8b949e", meta="#6e7681", shadow="#000000"),
}

LANG_COLOR = {
    "TypeScript": "#3178c6", "Python": "#3572a5", "Swift": "#f05138",
    "HTML": "#e34c26", "Shell": "#89e051",
}

# (画像ファイル名, タイトル, スター数, 言語)
CARDS = [
    ("marp-agent", "パワポ作るマン", 114, "TypeScript"),
    ("html-share", "HTML共有くん", 24, "HTML"),
    ("jirei-share-bot", "事例共有くん", 1, "Python"),
    ("live-dictation", "文字起こしちゃん", 6, "Swift"),
    ("my-claude-code-settings", "Claude Code設定", 97, "Shell"),
    ("agentcore-push", "agentcore-push", 5, "Python"),
    ("agent-book", "AIエージェント開発/運用入門", 157, "Python"),
    # カード上は「Amazon」を落として字を大きく保つ。正式書名は README の alt に書く。
    ("bedrock-book", "Bedrock 生成AIアプリ開発入門", 133, "Python"),
    ("agentcore-book", "Bedrock AgentCore実践入門", 42, "Python"),
]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


INNER = W - 76          # 左右の余白を引いた、文字を置ける幅


def text_em(text):
    """1em を単位にした概算の文字幅。日本語は全角、英数字と記号は約0.56倍で数える。"""
    return sum(1.0 if ord(c) > 0x2E80 else 0.56 for c in text)


def title_size(text):
    """枠内に必ず収まる最大サイズを選ぶ。書籍名のような長いタイトルは自動で小さくなる。"""
    for size in (44, 40, 36, 32, 29, 26, 24):
        if text_em(text) * size <= INNER:
            return size
    return 22


def build_svg(title, stars, lang, theme):
    t = THEMES[theme]
    lc = LANG_COLOR.get(lang, "#8b949e")
    ts = title_size(title)
    star_x = 34 + len(str(stars)) * 12   # 言語ドットをスター数の桁数ぶん右へずらす
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#0e0d6a"/><stop offset="55%" stop-color="#0a4695"/><stop offset="100%" stop-color="#01b6ec"/>
  </linearGradient>
  <clipPath id="card"><rect x="2" y="2" width="{W-4}" height="{H-4}" rx="{RADIUS}"/></clipPath>
</defs>
<style>
  .ti {{ font-family: "Hiragino Sans","Hiragino Kaku Gothic ProN",sans-serif; font-weight: 800; fill: {t['title']}; }}
  .mt {{ font-family: "Helvetica Neue",Arial,sans-serif; font-weight: 700; fill: {t['meta']}; }}
  .ml {{ font-family: "Hiragino Sans","Helvetica Neue",Arial,sans-serif; font-weight: 600; fill: {t['meta']}; }}
</style>
<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="{RADIUS}" fill="{t['bg']}" stroke="{t['border']}" stroke-width="2"/>
<g clip-path="url(#card)">
  <rect x="0" y="0" width="{W}" height="7" fill="url(#accent)"/>
</g>

<text class="ti" x="38" y="95" font-size="{ts}">{esc(title)}</text>

<g transform="translate(38, 128)">
  <path d="M12 0.7 L15.2 7.5 L22.6 8.5 L17.3 13.7 L18.6 21.1 L12 17.6 L5.4 21.1 L6.7 13.7 L1.4 8.5 L8.8 7.5 Z"
        fill="#e3b341"/>
  <text class="mt" x="32" y="17" font-size="22">{stars}</text>
  <circle cx="{star_x + 44}" cy="11" r="8" fill="{lc}"/>
  <text class="ml" x="{star_x + 60}" y="17" font-size="21">{esc(lang)}</text>
</g>
</svg>
'''


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    made = 0
    for name, title, stars, lang in CARDS:
        for theme in THEMES:
            svg = OUT_DIR / f"{name}-{theme}.svg"
            png = OUT_DIR / f"{name}-{theme}.png"
            svg.write_text(build_svg(title, stars, lang, theme))
            subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H),
                            "-o", str(png), str(svg)], check=True)
            svg.unlink()
            made += 1
    total = sum(p.stat().st_size for p in OUT_DIR.glob("*.png"))
    print(f"カード {made}枚を生成（合計 {total // 1024}KB）")
    for name, title, _, _ in CARDS:
        print(f"  {title_size(title):>2}px  {title}")


if __name__ == "__main__":
    sys.exit(main())
