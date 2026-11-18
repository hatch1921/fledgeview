from playwright.sync_api import sync_playwright
import glob
STORED = "(() => { const c = JSON.parse(localStorage.getItem('chimp-cull') || '{}'); const k = Object.keys(c).find(k => k.startsWith('DSC0001.JPG')); return k ? c[k] : null; })()"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    pg = b.new_page(viewport={'width': 1920, 'height': 1080}, color_scheme='dark'); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(900)
    files = sorted(glob.glob('/tmp/pairtest/*'))
    pg.evaluate("(() => { localStorage.clear(); localStorage.setItem('chimp-settings', JSON.stringify({ tipShown: true, sortAsk: false, pairs: false })); })()"); pg.reload(); pg.wait_for_timeout(900)
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    pg.set_input_files('#fileInput', files); pg.wait_for_timeout(3000); pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    print('pairing off -> photos in the grid:', pg.evaluate("document.querySelectorAll('#strip .th').length"), '(from 6 files)')
    pg.click('#strip [aria-label="DSC0001.ARW"]'); pg.wait_for_timeout(800); pg.keyboard.press('4'); pg.wait_for_timeout(500)
    pg.evaluate("document.getElementById('pairBtn').click()"); pg.wait_for_timeout(300)
    print('setting turned back on:', pg.evaluate("document.getElementById('pairBtn').getAttribute('aria-pressed')"))
    pg.evaluate("document.getElementById('clearAll').click()"); pg.wait_for_timeout(600); pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    pg.set_input_files('#fileInput', files); pg.wait_for_timeout(3000); pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    print('pairing on  -> photos in the grid:', pg.evaluate("document.querySelectorAll('#strip .th').length"))
    print("the pair's stored rating (carried from the raw):", pg.evaluate(STORED))
    print('errors:', errs)
    b.close()
