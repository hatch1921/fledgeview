from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np, io
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    pg = b.new_page(viewport={'width': 1920, 'height': 1080}, color_scheme='dark'); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(900); pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    pg.set_input_files('#fileInput', ['/tmp/vid/Wildlife/2026-09-04/A1208483.jpg', '/tmp/vid/Wildlife/2026-09-04/A1206951.jpg']); pg.wait_for_timeout(2500)
    pg.click('#strip [aria-label="A1208483.jpg"]'); pg.wait_for_timeout(1200)
    def photo_box():
        sc = pg.locator('#screen').bounding_box(); im = np.asarray(Image.open(io.BytesIO(pg.screenshot(clip=sc))).convert('L')).astype(int)
        mask = im > 30; ys, xs = np.where(mask[40:-40, 40:-40]); w, h = xs.max() - xs.min(), ys.max() - ys.min(); return w, h, round(w / h, 2)
    state = lambda: {'editsShown': pg.evaluate("!document.getElementById('editView').hidden"), 'infoVisible': pg.evaluate("getComputedStyle(document.getElementById('osd')).zIndex")}
    print('before cropping:', photo_box(), state())
    pg.click('#cropTab'); pg.wait_for_timeout(800); pg.select_option('#eCropAr', '1:1'); pg.wait_for_timeout(300); pg.click('#eCropBtn'); pg.wait_for_timeout(1200)
    print('after Done (1:1 crop):', photo_box(), state(), '| camera info text:', pg.evaluate("document.getElementById('osd').innerText.replace(/\\s+/g, ' ')")[:40])
    pg.screenshot(path='/tmp/viewedits.png')
    pg.keyboard.press('z'); pg.wait_for_timeout(1200); print('zoomed in: edits view still on (shows full original region):', state()['editsShown'])
    pg.keyboard.press('z'); pg.wait_for_timeout(800)
    pg.click('#tPeak'); pg.wait_for_timeout(700); print('Peaking on -> original shown:', not state()['editsShown'], photo_box()); pg.click('#tPeak'); pg.wait_for_timeout(700)
    print('Peaking off -> edits again:', state()['editsShown'])
    pg.click('#strip [aria-label="A1206951.jpg"]'); pg.wait_for_timeout(1200); print('unedited photo -> original:', not state()['editsShown'])
    pg.click('#strip [aria-label="A1208483.jpg"]'); pg.wait_for_timeout(1500); print('back to the cropped doe -> edits:', state()['editsShown'], photo_box())
    pg.click('#pvBtn'); pg.wait_for_timeout(1300); print('Photo view:', pg.evaluate("document.body.classList.contains('pview')")); pg.keyboard.press('Escape'); pg.wait_for_timeout(900)
    print('after Photo view -> edits:', state()['editsShown'])
    pg.click('#editTab'); pg.wait_for_timeout(800); print('Adjust opened: edit panel showing:', pg.evaluate("!document.getElementById('editPanel').hidden"))
    pg.click('#editTab'); pg.wait_for_timeout(800); print('Adjust closed -> edits:', state()['editsShown'])
    print('errors:', errs)
    b.close()
