from playwright.sync_api import sync_playwright
from PIL import Image
import io
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    ctx = b.new_context(viewport={'width': 1920, 'height': 1080}, color_scheme='dark', accept_downloads=True); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(900)
    pg.evaluate("(() => { localStorage.clear(); localStorage.setItem('chimp-settings', JSON.stringify({ tipShown: true, sortAsk: false })); })()"); pg.reload(); pg.wait_for_timeout(900)
    pg.evaluate("(() => { document.querySelectorAll('dialog[open]').forEach(d => d.close()); window.showSaveFilePicker = undefined; window.showDirectoryPicker = undefined; })()")
    pg.set_input_files('#fileInput', ['/tmp/vid/Wildlife/2026-09-04/A1208483.jpg']); pg.wait_for_timeout(1500)
    pg.click('#tFrame'); pg.wait_for_timeout(1500)
    info = lambda: pg.evaluate("document.getElementById('frameInfo').textContent")
    open_ = lambda: pg.evaluate("(() => { const r = document.getElementById('frameView').getBoundingClientRect(), c = document.getElementById('frameCanvas'), k = c.width / r.width; return null; })()")
    def drag_test(label):
        before = pg.evaluate("document.getElementById('frameCanvas').toDataURL().length")
        r = pg.locator('#frameView').bounding_box(); cx, cy = r['x'] + r['width'] / 2, r['y'] + r['height'] / 2
        pg.mouse.move(cx, cy); pg.mouse.down(); pg.mouse.move(cx + 160, cy, steps=8); pg.mouse.up(); pg.wait_for_timeout(500)
        after = pg.evaluate("document.getElementById('frameCanvas').toDataURL().length")
        print(f'{label}: dragging at fit changed the picture: {before != after}')
    print('Fit  |', info()[:120]); drag_test('Fit ')
    pg.select_option('#fFit', 'fill'); pg.wait_for_timeout(900)
    print('Fill |', info()[:160]); drag_test('Fill')
    # save the framed image twice, with the photo dragged to each side, and compare
    def save(name):
        with pg.expect_download() as d: pg.click('#fSave')
        p2 = f'/tmp/{name}.jpg'; d.value.save_as(p2); return Image.open(p2)
    r = pg.locator('#frameView').bounding_box(); cx, cy = r['x'] + r['width'] / 2, r['y'] + r['height'] / 2
    pg.mouse.move(cx, cy); pg.mouse.down(); pg.mouse.move(cx + 600, cy, steps=10); pg.mouse.up(); pg.wait_for_timeout(500); a = save('fill_left')
    pg.mouse.move(cx, cy); pg.mouse.down(); pg.mouse.move(cx - 1200, cy, steps=12); pg.mouse.up(); pg.wait_for_timeout(500); c = save('fill_right')
    import numpy as np
    da, dc = np.asarray(a.convert('L')).astype(int), np.asarray(c.convert('L')).astype(int)
    print('saved images differ with the positioning:', a.size == c.size and float(np.abs(da - dc).mean()) > 3, '| size', a.size)
    pg.screenshot(path='/tmp/fill.png', clip=pg.locator('#frameView').bounding_box())
    print('errors:', errs)
    b.close()
