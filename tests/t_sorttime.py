from playwright.sync_api import sync_playwright
import glob
files = sorted(glob.glob('/tmp/vid/Wildlife/2026-09-04/*.jpg'))[:8] + ['/tmp/no_time.png']
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    pg = b.new_page(viewport={'width': 1600, 'height': 900}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/exifr@7.1.3/dist/full.umd.js', lambda r: r.fulfill(path='/tmp/libs/exifr-7.1.3/dist/full.umd.js', content_type='application/javascript'))
    pg.route('**/jszip.min.js', lambda r: r.fulfill(path='/tmp/libs/jszip-3.10.1/dist/jszip.min.js', content_type='application/javascript'))
    pg.route('https://fonts.**', lambda r: r.abort())
    pg.goto('file:///mnt/user-data/outputs/fledgeview.html'); pg.wait_for_timeout(800)
    pg.evaluate("document.getElementById('guideDlg').close()")
    pg.set_input_files('#fileInput', files); pg.wait_for_timeout(3000)
    order = lambda: pg.evaluate("[...document.querySelectorAll('#strip .th')].map(b => b.getAttribute('aria-label'))")
    times = pg.evaluate("Object.fromEntries([...document.querySelectorAll('#strip .th')].map(b => [b.getAttribute('aria-label'), null]))")
    for v in ['time', 'timeNew']:
        pg.select_option('#sortSel', v); pg.wait_for_timeout(600)
        o = order(); print(v, '->', o[:3], '...', o[-2:])
    # check against the photos' recorded capture times
    pg.click('#strip .th'); pg.wait_for_timeout(300)
    print('sort menu choices:', pg.evaluate("[...document.getElementById('sortSel').options].map(o => o.textContent)"))
    print('errors:', errs)
    b.close()
