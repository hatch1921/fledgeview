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
    pg.set_input_files('#fileInput', ['/tmp/vid/Wildlife/2026-09-04/A1208483.jpg', '/mnt/user-data/uploads/A1200001.ARW']); pg.wait_for_timeout(2500)
    for name in ['A1208483.jpg', 'A1200001.ARW']:
        pg.click(f'#strip [aria-label="{name}"]'); pg.wait_for_timeout(2000)
        if not pg.evaluate("document.getElementById('editView').offsetParent"): pg.click('#editTab'); pg.wait_for_timeout(800)
        pg.click('#cropTab'); pg.wait_for_timeout(900)
        full = pg.evaluate("document.getElementById('eCropInfo').textContent")
        pg.select_option('#eCropAr', '4:5'); pg.wait_for_timeout(500)
        four5 = pg.evaluate("document.getElementById('eCropInfo').textContent")
        if name == 'A1200001.ARW': pg.screenshot(path='/tmp/cropsize.png')
        print(name, '| full frame:', full, '| 4:5:', four5)
        pg.click('#eCropReset'); pg.wait_for_timeout(200); pg.click('#eCropBtn'); pg.wait_for_timeout(400)
    print('errors:', errs)
    b.close()
