from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    ctx = b.new_context(viewport={'width': 1920, 'height': 1080}, color_scheme='dark', accept_downloads=True); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(900)
    pg.evaluate("(() => { const s = JSON.parse(localStorage.getItem('chimp-settings') || '{}'); s.tipShown = true; localStorage.setItem('chimp-settings', JSON.stringify(s)); })()"); pg.reload(); pg.wait_for_timeout(900)
    pg.evaluate("(() => { document.querySelectorAll('dialog[open]').forEach(d => d.close()); window.showDirectoryPicker = undefined; window.showSaveFilePicker = undefined; })()")
    pg.set_input_files('#fileInput', ['/tmp/wbtest/warm-cast-with-card.jpg']); pg.wait_for_timeout(1800)
    # Blinkies: the pure-black patch should flash blue
    pg.click('#tBlink'); pg.wait_for_timeout(600)
    blue = pg.evaluate("""(() => { const c = document.querySelector('#pane0 .blink'), x = c.getContext('2d'), d = x.getImageData(0, 0, c.width, c.height).data; let blue = 0, red = 0;
      for (let i = 0; i < d.length; i += 4) { if (d[i + 3] && d[i + 2] > 200 && d[i] < 80) blue++; if (d[i + 3] && d[i] > 200 && d[i + 2] < 80) red++; } return { blue, red, total: c.width * c.height }; })()""")
    print('Blinkies: crushed-black pixels (blue):', blue['blue'], '| blown pixels (red):', blue['red'], '| of', blue['total'])
    pg.click('#tBlink'); pg.wait_for_timeout(400)
    # Pick neutral on the gray card
    pg.click('#editTab'); pg.wait_for_timeout(900)
    print('Pick neutral button:', pg.evaluate("document.getElementById('eWbPick').textContent.trim()"))
    pg.keyboard.press('w'); pg.wait_for_timeout(300); print('W turns it on:', pg.evaluate("document.getElementById('eWbPick').getAttribute('aria-pressed')"))
    cv = pg.evaluate("(() => { const r = document.getElementById('editCanvas').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
    # the photo is fitted inside the canvas; find the card's screen position from the fitted photo box
    box = pg.evaluate("(() => { const cv = document.getElementById('editCanvas'), r = cv.getBoundingClientRect(), k = cv.width / r.width; return null; })()")
    from PIL import Image as I
    import io
    shot = np.asarray(I.open(io.BytesIO(pg.screenshot(clip={'x': cv[0], 'y': cv[1], 'width': cv[2], 'height': cv[3]}))).convert('L')).astype(int)
    ys, xs = np.where(shot[30:-30, 30:-30] > 20); x0, x1, y0, y1 = xs.min() + 30, xs.max() + 30, ys.min() + 30, ys.max() + 30
    cx = cv[0] + x0 + (x1 - x0) * 0.14; cy = cv[1] + y0 + (y1 - y0) * 0.81
    pg.mouse.click(cx, cy); pg.wait_for_timeout(900)
    print('after picking the card: Temperature', pg.evaluate("document.getElementById('ev_temp').textContent"), '| Tint', pg.evaluate("document.getElementById('ev_tint').textContent"), '| note:', pg.evaluate("document.getElementById('toast').textContent")[:50])
    # export and measure the card
    pg.click('#eDone'); pg.wait_for_timeout(400)
    pg.click('#webBtn'); pg.wait_for_timeout(500); pg.select_option('#wSrc', 'current'); pg.select_option('#wShape', 'orig'); pg.select_option('#wSharp', '0')
    if pg.evaluate("document.getElementById('wBar').checked"): pg.click('#wBar')
    pg.wait_for_timeout(700)
    with pg.expect_download() as d: pg.click('#webGo')
    a = np.asarray(Image.open(d.value.path()).convert('RGB')).astype(float); H, W = a.shape[:2]
    card = a[int(H*.72):int(H*.90), int(W*.08):int(W*.20)].reshape(-1, 3).mean(0)
    print('gray card in the export:', card.round(1), '| spread between channels:', round(float(card.max() - card.min()), 1), '(0 = perfectly neutral; it was about 32 before)')
    # a strongly colored spot is refused
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    pg.click('#editTab'); pg.wait_for_timeout(700); pg.click('#eWbPick'); pg.wait_for_timeout(200)
    pg.mouse.click(cv[0] + x0 + (x1 - x0) * 0.5, cv[1] + y0 + (y1 - y0) * 0.30); pg.wait_for_timeout(500)
    print('clicking the green background:', pg.evaluate("document.getElementById('toast').textContent")[:70])
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200); print('Esc cancels:', pg.evaluate("document.getElementById('eWbPick').getAttribute('aria-pressed')"))
    print('errors:', errs)
    b.close()
