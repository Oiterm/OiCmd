"""OiCmd 아이콘 (OiNMS·OiLog 아이콘과 같은 디자인, 점 색과 글자만 다름)

작은 크기(16~48px)는 단순화한 "Oi" + 점, 64px 이상은 아래에 "CMD" 글자.
만드는 것: oicmd.ico, icon-*.png, icon.svg, icon-small.svg, ../installer/welcome.bmp
필요: python3, playwright(chromium), pillow, Inter 글꼴
"""
import io, os
from playwright.sync_api import sync_playwright
from PIL import Image

OUT = os.path.dirname(os.path.abspath(__file__))
SIZES = [16, 20, 24, 32, 40, 48, 64, 96, 128, 256]

BG_TOP, BG_BOT, EDGE = "#1f2731", "#0e1318", "#334050"
INK, ACCENT = "#e9eef3", "#46c08a"


def svg_full(px):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{px}" height="{px}" viewBox="0 0 256 256">
<defs>
 <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG_BOT}"/></linearGradient>
 <filter id="glow" x="-1" y="-1" width="3" height="3"><feGaussianBlur stdDeviation="7"/></filter>
</defs>
<rect x="8" y="8" width="240" height="240" rx="58" fill="url(#bg)"/>
<rect x="9" y="9" width="238" height="238" rx="57" fill="none" stroke="{EDGE}" stroke-width="2"/>
<circle cx="98" cy="106" r="41" fill="none" stroke="{INK}" stroke-width="22"/>
<rect x="158" y="86" width="23" height="61" rx="4" fill="{INK}"/>
<circle cx="169.5" cy="58" r="16" fill="{ACCENT}" opacity=".55" filter="url(#glow)"/>
<circle cx="169.5" cy="58" r="13" fill="{ACCENT}"/>
<text x="128" y="213" text-anchor="middle" font-family="Inter" font-weight="800" font-size="46" letter-spacing="7" fill="{ACCENT}">CMD</text>
</svg>'''


def svg_small(px):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{px}" height="{px}" viewBox="0 0 32 32" shape-rendering="geometricPrecision">
<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG_BOT}"/></linearGradient></defs>
<rect x="0.5" y="0.5" width="31" height="31" rx="7" fill="url(#bg)" stroke="{EDGE}" stroke-width="1"/>
<circle cx="12" cy="17.5" r="6.2" fill="none" stroke="{INK}" stroke-width="3.6"/>
<rect x="20.5" y="13" width="3.8" height="11" rx="0.8" fill="{INK}"/>
<circle cx="22.4" cy="8.4" r="2.6" fill="{ACCENT}"/>
</svg>'''


def welcome_html():
    # NSIS 환영 화면 왼쪽 그림 164x314
    return f'''<html><body style="margin:0;width:164px;height:314px;background:linear-gradient({BG_TOP},{BG_BOT});
font-family:Inter,sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;color:{INK}">
{svg_full(112)}
<div style="margin-top:14px;font-weight:800;font-size:22px;letter-spacing:1px"><span style="color:{ACCENT}">Oi</span>Cmd</div>
<div style="margin-top:6px;font-size:11px;opacity:.7">Command Dictionary</div>
</body></html>'''


def render(pg, html, w, h):
    pg.set_viewport_size({"width": w, "height": h})
    pg.set_content(html)
    return Image.open(io.BytesIO(pg.screenshot(omit_background=True, clip={"x": 0, "y": 0, "width": w, "height": h}))).convert("RGBA")


def wrap(svg):
    return f'<html><body style="margin:0;background:transparent">{svg}</body></html>'


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]) if os.path.exists("/usr/bin/google-chrome") else p.chromium.launch()
    pg = b.new_page(device_scale_factor=1)
    imgs = {}
    for s in SIZES:
        imgs[s] = render(pg, wrap(svg_small(s) if s < 64 else svg_full(s)), s, s)
        imgs[s].save(os.path.join(OUT, f"icon-{s}.png"))
    render(pg, wrap(svg_full(512)), 512, 512).save(os.path.join(OUT, "icon-512.png"))
    wb = render(pg, welcome_html(), 164, 314)
    b.close()

open(os.path.join(OUT, "icon.svg"), "w").write(svg_full(256))
open(os.path.join(OUT, "icon-small.svg"), "w").write(svg_small(32))
base = imgs[256]
others = [imgs[s] for s in SIZES if s != 256]
base.save(os.path.join(OUT, "oicmd.ico"), format="ICO", sizes=[(s, s) for s in SIZES],
          append_images=others, bitmap_format="bmp")
inst = os.path.join(OUT, "..", "installer")
os.makedirs(inst, exist_ok=True)
wb.convert("RGB").save(os.path.join(inst, "welcome.bmp"))
print("ok", os.path.getsize(os.path.join(OUT, "oicmd.ico")))
