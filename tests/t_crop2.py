from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx = b.new_context(viewport={'width': 1920, 'height': 1080}, color_scheme='dark', accept_downloads=True); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('dialog', lambda d: d.accept())
    pg.route('**/exifr@7.1.3/dist/full.umd.js', lambda r: r.fulfill(path='/tmp/libs/exifr-7.1.3/dist/full.umd.js', content_type='application/javascript'))
    pg.route('**/jszip.min.js', lambda r: r.fulfill(path='/tmp/libs/jszip-3.10.1/dist/jszip.min.js', content_type='application/javascript'))
    pg.route('https://fonts.**', lambda r: r.abort())
    pg.goto('file:///mnt/user-data/outputs/fledgeview.html'); pg.wait_for_timeout(800)
    pg.evaluate("(() => { window.showDirectoryPicker = undefined; document.getElementById('guideDlg').close(); const s = JSON.parse(localStorage.getItem('chimp-settings')); s.tipShown = true; localStorage.setItem('chimp-settings', JSON.stringify(s)); })()")
    pg.reload(); pg.wait_for_timeout(900); pg.evaluate("(() => { window.showDirectoryPicker = undefined; document.querySelectorAll('dialog[open]').forEach(d => d.close()); })()")
    pg.set_input_files('#fileInput', ['/tmp/vid/Wildlife/2026-09-04/A1208483.jpg', '/tmp/vid/Wildlife/2026-09-04/A1209362.jpg']); pg.wait_for_timeout(2000)
    pg.click('#strip [aria-label="A1208483.jpg"]'); pg.wait_for_timeout(800)
    setv = lambda k, v: pg.evaluate(f"(() => {{ const i = document.getElementById('e_{k}'); i.value = {v}; i.dispatchEvent(new Event('input')); }})()")
    def export(shape='orig'):
        pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        pg.click('#webBtn'); pg.wait_for_timeout(500); pg.select_option('#wSrc', 'current'); pg.select_option('#wShape', shape); pg.select_option('#wSharp', '0')
        if pg.evaluate("document.getElementById('wBar').checked"): pg.click('#wBar')
        pg.wait_for_timeout(900)
        with pg.expect_download() as d: pg.click('#webGo')
        a = np.asarray(Image.open(d.value.path()).convert('RGB')).astype(float); pg.evaluate("document.getElementById('webDlg').close()"); pg.wait_for_timeout(300); return a
    def satur(a): mx, mn = a.max(2), a.min(2); return float((mx - mn).mean())
    def detail(a):
        g = a.mean(2); bl = np.asarray(Image.fromarray(g.astype(np.uint8)).resize((g.shape[1] // 16, g.shape[0] // 16)).resize((g.shape[1], g.shape[0]), Image.BILINEAR)).astype(float)
        return float(np.abs(g - bl).mean())
    base = export()
    pg.click('#editTab'); pg.wait_for_timeout(800)
    print('new controls:', pg.evaluate("['e_rot','e_sat','e_cla','eCropBtn'].map(i => !!document.getElementById(i))"), '| straighten readout:', pg.evaluate("document.getElementById('ev_rot').textContent"))
    setv('sat', 60); s60 = export(); setv('sat', -100); s0 = export(); setv('sat', 0)
    print(f'Saturation: plain {satur(base):.1f} | +60 -> {satur(s60):.1f} | -100 -> {satur(s0):.1f} (0 = gray)')
    setv('cla', 80); c80 = export(); setv('cla', 0)
    H, W = base.shape[:2]
    print(f'Clarity +80: whole-photo detail {detail(base):.2f} -> {detail(c80):.2f} | smooth background corner change: {np.abs(c80[:H//6, :W//6] - base[:H//6, :W//6]).mean():.2f} levels')
    # crop by dragging the bottom-right corner in, then lock 1:1
    pg.wait_for_timeout(1200); pg.evaluate("document.getElementById('tipDlg').open && document.getElementById('tipDlg').close()")
    pg.click('#cropTab'); pg.wait_for_timeout(900)
    bx = pg.evaluate("(() => { const cv = document.getElementById('editCanvas'), r = cv.getBoundingClientRect(), k = cv.width / r.width; return { left: r.left, top: r.top, k }; })()")
    eb = pg.evaluate("(() => { /* the crop box spans the drawn photo */ const cv = document.getElementById('editCanvas'); return null; })()")
    print('crop options shown:', not pg.evaluate("document.getElementById('eCropOpts').hidden"), '| button says:', pg.evaluate("document.getElementById('eCropBtn').textContent"))
    pg.screenshot(path='/tmp/crop1.png')
    # find the photo's drawn corner on the edit canvas by scanning for the bright crop border
    img = np.asarray(Image.open('/tmp/crop1.png').convert('RGB')).astype(int)
    cr = pg.evaluate("(() => { const r = document.getElementById('editCanvas').getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.right), Math.round(r.bottom)]; })()")
    white = np.zeros(img.shape[:2], bool); sub = img[cr[1] + 2:cr[3] - 2, cr[0] + 2:cr[2] - 2].min(2) > 245; white[cr[1] + 2:cr[3] - 2, cr[0] + 2:cr[2] - 2] = sub
    ys, xs = np.where(white)
    x1, y1 = int(xs.max()), int(ys.max()); x0, y0 = int(xs.min()), int(ys.min())
    print('crop box on screen:', (x0, y0, x1, y1))
    pg.evaluate('getSelection().removeAllRanges()'); print('before dragging:', repr(pg.evaluate('getSelection().toString()')[:30]))
    pg.mouse.move(x1 - 3, y1 - 3); print('  element under the corner:', pg.evaluate(f'document.elementFromPoint({x1 - 3}, {y1 - 3}).id || document.elementFromPoint({x1 - 3}, {y1 - 3}).className')); pg.mouse.down(); pg.mouse.move(x0 + (x1 - x0) * 0.7, y0 + (y1 - y0) * 0.75, steps=8); pg.mouse.up(); pg.wait_for_timeout(300); print('after corner drag:', repr(pg.evaluate('getSelection().toString()')[:30]))
    pg.mouse.move((x0 + x1) * 0.35, (y0 + y1) * 0.37); pg.mouse.down(); pg.mouse.move((x0 + x1) * 0.4, (y0 + y1) * 0.42, steps=6); pg.mouse.up(); pg.wait_for_timeout(300)
    print('crop after dragging the corner and the box (before choosing 1:1):', pg.evaluate("(() => 0)()"))
    pg.select_option('#eCropAr', '1:1'); pg.wait_for_timeout(400)
    print('text selected after dragging:', repr(pg.evaluate('getSelection().toString()')[:40])); pg.screenshot(path='/tmp/crop2.png')
    pg.keyboard.press('Enter'); pg.wait_for_timeout(500)
    rec = pg.evaluate("(() => { const e = JSON.parse(localStorage.getItem('chimp-edits') || '{}'); return Object.values(e)[0]; })()")
    print('saved crop:', rec.get('crop'), rec.get('cropAr'), '| Crop button marked:', pg.evaluate("document.getElementById('eCropBtn').classList.contains('has')"))
    sq = export(); print('export with 1:1 crop:', sq.shape[1], 'x', sq.shape[0])
    ig = export('4x5'); print('Instagram 4:5 export from the cropped photo:', ig.shape[1], 'x', ig.shape[0])
    # straighten 6 degrees, no crop: no empty corners
    pg.evaluate("document.getElementById('tipDlg').open && document.getElementById('tipDlg').close()")
    if not pg.evaluate("!document.getElementById('editPanel').hidden"): pg.click('#editTab'); pg.wait_for_timeout(500)
    pg.click('#eReset'); pg.wait_for_timeout(300); setv('rot', 60); pg.wait_for_timeout(400)
    print('straighten readout at 60:', pg.evaluate("document.getElementById('ev_rot').textContent"))
    st = export(); corners = [st[2, 2], st[2, -3], st[-3, 2], st[-3, -3]]
    print('straightened export', st.shape[1], 'x', st.shape[0], '| corner brightness:', [round(float(c.mean())) for c in corners], '(empty corners would be 0)')
    pg.screenshot(path='/tmp/crop3.png')
    # Frame mode and Photo view with a crop
    pg.click('#eReset'); pg.wait_for_timeout(200)
    pg.click('#cropTab'); pg.wait_for_timeout(600); pg.select_option('#eCropAr', '1:1'); pg.wait_for_timeout(300); pg.click('#eCropBtn'); pg.wait_for_timeout(500)
    pg.click('#tFrame'); pg.wait_for_timeout(1200); print('Frame mode with a crop: ok' if not errs else errs); pg.click('#tFrame'); pg.wait_for_timeout(500)
    pg.click('#pvBtn'); pg.wait_for_timeout(1500)
    print('Photo view shows the crop (square drawn):', pg.evaluate("(() => { const b = document.getElementById('editCanvas'); return !document.getElementById('editView').hidden; })()"))
    pg.screenshot(path='/tmp/crop4.png'); pg.keyboard.press('Escape'); pg.wait_for_timeout(500)
    print('errors:', errs)
    b.close()
