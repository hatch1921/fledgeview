from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    pg = b.new_page(viewport={'width': 1920, 'height': 1080}, color_scheme='dark'); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/exifr@7.1.3/dist/full.umd.js', lambda r: r.fulfill(path='/tmp/libs/exifr-7.1.3/dist/full.umd.js', content_type='application/javascript'))
    pg.route('**/jszip.min.js', lambda r: r.fulfill(path='/tmp/libs/jszip-3.10.1/dist/jszip.min.js', content_type='application/javascript'))
    pg.route('https://fonts.**', lambda r: r.abort())
    pg.goto('file:///mnt/user-data/outputs/fledgeview.html'); pg.wait_for_timeout(800)
    pg.evaluate("document.getElementById('guideDlg').close()")
    pg.set_input_files('#fileInput', ['/mnt/user-data/uploads/A1200001.ARW']); pg.wait_for_timeout(3000)
    pg.click('#editTab'); pg.wait_for_timeout(800)
    setv = lambda k, v: pg.evaluate(f"(() => {{ const i = document.getElementById('e_{k}'); i.value = {v}; i.dispatchEvent(new Event('input')); }})()")
    rec = lambda: pg.evaluate("(() => { const e = JSON.parse(localStorage.getItem('chimp-edits') || '{}'); const r = Object.values(e)[0] || {}; return { exp: r.exp || 0, rot: r.rot || 0, crop: r.crop ? Math.round(r.crop.w * 100) + '% wide' : 'none' }; })()")
    info = lambda: pg.evaluate("document.getElementById('eCropInfo').textContent")
    undo_on = lambda: not pg.evaluate("document.getElementById('eCropUndo').disabled")
    setv('exp', 30); pg.wait_for_timeout(500)
    print('Undo before any crop change:', 'enabled' if undo_on() else 'dimmed')
    pg.click('#cropTab'); pg.wait_for_timeout(900)
    print('at 300 ppi:', info().split(' · ')[2]); pg.select_option('#eCropPpi', '240'); pg.wait_for_timeout(300); print('at 240 ppi:', info().split(' · ')[2])
    pg.click('#eReach2'); pg.wait_for_timeout(300); s1 = info().split(' · ')[0]
    # a real corner drag on the crop box
    hits = pg.evaluate("""(() => { const cv = document.getElementById('editCanvas'), r = cv.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()""")
    pg.select_option('#eCropAr', '1:1'); pg.wait_for_timeout(300); s2 = info().split(' · ')[0]
    pg.click('#eReach14'); pg.wait_for_timeout(300); s3 = info().split(' · ')[0]
    print('steps: +2x ->', s1, '| 1:1 ->', s2, '| +1.4x ->', s3)
    for n in range(3):
        pg.click('#eCropUndo'); pg.wait_for_timeout(300); print(f'  undo {n + 1} ->', info().split(' · ')[0])
    print('  Undo now:', 'enabled' if undo_on() else 'dimmed (back to the start)')
    pg.click('#eReach2'); pg.wait_for_timeout(300); pg.click('#eCropBtn'); pg.wait_for_timeout(500)
    print('finished a 2x crop:', rec())
    pg.click('#cropTab'); pg.wait_for_timeout(700); pg.click('#eCropUndo'); pg.wait_for_timeout(300); pg.click('#eCropBtn'); pg.wait_for_timeout(500); print('Undo after finishing the crop (reopened, undone, done):', rec())
    # one Straighten movement = several slider updates = one Undo step
    for v in (10, 25, 40): setv('rot', v); pg.wait_for_timeout(60)
    pg.wait_for_timeout(900); print('straightened:', rec())
    pg.click('#cropTab'); pg.wait_for_timeout(700); pg.click('#eCropUndo'); pg.wait_for_timeout(300); pg.click('#eCropBtn'); pg.wait_for_timeout(500); print('Undo once:', rec(), '| slider shows', pg.evaluate("document.getElementById('ev_rot').textContent"))
    print('errors:', errs)
    b.close()
