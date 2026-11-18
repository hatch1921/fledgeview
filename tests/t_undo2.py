from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    pg = b.new_page(viewport={'width': 1920, 'height': 1080}, color_scheme='dark'); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/exifr@7.1.3/dist/full.umd.js', lambda r: r.fulfill(path='/tmp/libs/exifr-7.1.3/dist/full.umd.js', content_type='application/javascript'))
    pg.route('**/jszip.min.js', lambda r: r.fulfill(path='/tmp/libs/jszip-3.10.1/dist/jszip.min.js', content_type='application/javascript'))
    pg.route('https://fonts.**', lambda r: r.abort())
    pg.goto('file:///mnt/user-data/outputs/fledgeview.html'); pg.wait_for_timeout(800)
    pg.evaluate("document.getElementById('guideDlg').close()")
    pg.set_input_files('#fileInput', ['/tmp/vid/Wildlife/2026-09-04/A1208483.jpg']); pg.wait_for_timeout(2000)
    pg.click('#cropTab'); pg.wait_for_timeout(1000)
    info = lambda: pg.evaluate("document.getElementById('eCropInfo').textContent").split(' · ')[0]
    pg.screenshot(path='/tmp/u.png'); img = np.asarray(Image.open('/tmp/u.png').convert('RGB')).astype(int)
    cr = pg.evaluate("(() => { const r = document.getElementById('editCanvas').getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.right), Math.round(r.bottom)]; })()")
    white = np.zeros(img.shape[:2], bool); white[cr[1] + 2:cr[3] - 2, cr[0] + 2:cr[2] - 2] = img[cr[1] + 2:cr[3] - 2, cr[0] + 2:cr[2] - 2].min(2) > 245
    ys, xs = np.where(white); x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
    print('start:', info())
    pg.mouse.move(x1 - 3, y1 - 3); pg.mouse.down(); pg.mouse.move(x0 + (x1 - x0) * 0.6, y0 + (y1 - y0) * 0.6, steps=8); pg.mouse.up(); pg.wait_for_timeout(300)
    print('after dragging the corner:', info(), '| Undo enabled:', not pg.evaluate("document.getElementById('eCropUndo').disabled"))
    pg.mouse.click((x0 + x1) // 3, (y0 + y1) // 3); pg.wait_for_timeout(300)
    print('a click inside without dragging adds no step; Undo once ->', end=' '); pg.click('#eCropUndo'); pg.wait_for_timeout(300); print(info())
    print('errors:', errs)
    b.close()
