from playwright.sync_api import sync_playwright
import glob, time, sys
from PIL import Image
import numpy as np
url = sys.argv[1]
ref = np.asarray(Image.open('/tmp/vid/Wildlife/2026-09-04/A1206951.jpg').convert('RGB')).astype(int)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    pg = b.new_page(viewport={'width': 1920, 'height': 1080}, color_scheme='dark'); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(url); pg.wait_for_timeout(1200); pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    print('UTIF loaded:', pg.evaluate("typeof UTIF"), '| pako loaded:', pg.evaluate("typeof pako"))
    files = sorted(glob.glob('/tmp/tifftest/*.tif'))
    pg.set_input_files('#fileInput', files); pg.wait_for_timeout(3000)
    for f in files:
        name = f.split('/')[-1]; t0 = time.time()
        pg.click(f'#strip [aria-label="{name}"]')
        pg.wait_for_function("(() => { const c = document.querySelector('#pane0 canvas.img'); return c && c.width > 1000; })()", timeout=30000)
        dt = time.time() - t0; pg.wait_for_timeout(900)
        pg.wait_for_function("(() => { const c = document.querySelector('#pane0 canvas.img'); return c && c.width > 1000; })()", timeout=30000)
        info = pg.evaluate("""(() => { const c = document.querySelector('#pane0 canvas.img'), x = c.getContext('2d'), d = x.getImageData(0, 0, c.width, c.height).data;
          const s = []; for (const [fx, fy] of [[0.3, 0.3], [0.5, 0.5], [0.62, 0.4], [0.8, 0.7]]) { const px = Math.floor(fx * c.width), py = Math.floor(fy * c.height), i = (py * c.width + px) * 4; s.push([px, py, d[i], d[i + 1], d[i + 2]]); }
          return { w: c.width, h: c.height, samples: s, beyond: !document.querySelector('.beyond') || document.querySelector('.beyond').hidden }; })()""")
        diff = max(abs(int(ref[py, px][k]) - v) for px, py, *rgb in info['samples'] for k, v in enumerate(rgb))
        print(f'{name:26s} shown at {info["w"]}x{info["h"]} | {dt:4.1f} s | pixels vs original: max difference {diff} | no "beyond preview" note: {info["beyond"]}')
    print('errors:', errs)
    b.close()
