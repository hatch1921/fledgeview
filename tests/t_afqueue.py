from playwright.sync_api import sync_playwright
import glob, sys
url = sys.argv[1]
FILES = sorted(glob.glob('/tmp/raw20/*.ARW'))
HOOK = """(() => { window.__big = { now: 0, max: 0, total: 0 }; const orig = Blob.prototype.slice;
  Blob.prototype.slice = function (a, b, c) { const part = orig.call(this, a, b, c); if ((b - (a || 0)) >= 8 * 1024 * 1024 - 1) { const ab = part.arrayBuffer.bind(part);
    part.arrayBuffer = async () => { const B = window.__big; B.now++; B.total++; B.max = Math.max(B.max, B.now); try { return await ab(); } finally { B.now--; } }; } return part; }; })()"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    pg = b.new_page(viewport={'width': 1920, 'height': 1080}, color_scheme='dark'); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(url); pg.wait_for_timeout(900)
    pg.evaluate("(() => { localStorage.clear(); localStorage.setItem('chimp-settings', JSON.stringify({ tipShown: true, sortAsk: false, sort: 'burst' })); })()"); pg.reload(); pg.wait_for_timeout(1000)
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(x => x.close())")
    pg.set_input_files('#fileInput', FILES); pg.wait_for_function("!document.getElementById('status').textContent && document.querySelectorAll('#strip .th .sp').length > 0", timeout=90000); pg.wait_for_timeout(1500)
    print('session 1: burst scored, labels shown =', pg.evaluate("document.querySelectorAll('#strip .th .sp').length"))
    # session 2: scores come from storage, focus points unknown
    pg.reload(); pg.wait_for_timeout(1000); pg.evaluate(HOOK); pg.evaluate("document.querySelectorAll('dialog[open]').forEach(x => x.close())")
    pg.set_input_files('#fileInput', FILES); pg.wait_for_timeout(6000)
    big = pg.evaluate("window.__big")
    print('session 2: 8 MB reads at the same time, at most =', big['max'], '| total =', big['total'], '| photo on screen:', pg.evaluate("(() => { const c = document.querySelector('#pane0 canvas.img'); return c ? c.width + 'x' + c.height : 'none'; })()"), '| labels:', pg.evaluate("[...new Set([...document.querySelectorAll('#strip .th .sp')].map(s => s.textContent))]"))
    print('errors:', errs)
    b.close()
