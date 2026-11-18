from playwright.sync_api import sync_playwright
import glob
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    pg = b.new_page(viewport={'width': 1920, 'height': 1080}, color_scheme='dark'); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(900)
    pg.evaluate("(() => { localStorage.clear(); localStorage.setItem('chimp-settings', JSON.stringify({ tipShown: true, sortAsk: false })); })()"); pg.reload(); pg.wait_for_timeout(900)
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    pg.set_input_files('#fileInput', sorted(glob.glob('/tmp/vid/Wildlife/2026-09-04/*.jpg'))); pg.wait_for_timeout(4000)
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    pg.click('#strip [aria-label="A1206944.jpg"]'); pg.wait_for_timeout(800)
    pg.keyboard.press('c'); pg.wait_for_timeout(1500)
    panes = lambda: pg.evaluate("""(() => { const nm = id => { const c = document.querySelector('#' + id + ' .cap'); return c ? c.textContent.split(/\\s{2,}/)[0].trim() : '?'; };
      return { left: nm('pane0'), right: nm('pane1'), held: document.getElementById('pane1').classList.contains('held') }; })()""")
    print('Compare:        ', panes())
    pg.keyboard.press('h'); pg.wait_for_timeout(1500); print('H (hold):       ', panes())
    pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(1300); print('arrow right:    ', panes())
    pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(1300); print('arrow right:    ', panes())
    pg.click('#pane1'); pg.wait_for_timeout(300); pg.keyboard.press('5'); pg.wait_for_timeout(500)
    held_rating = pg.evaluate("(() => { const c = JSON.parse(localStorage.getItem('chimp-cull') || '{}'); const k = Object.keys(c).find(k => k.startsWith('A1206944.jpg')); return k ? c[k] : null; })()")
    print('5 on the held pane rates the held frame:', held_rating)
    pg.click('#pane0'); pg.wait_for_timeout(300); pg.keyboard.press('h'); pg.wait_for_timeout(1500); print('H on the left (promote):', panes())
    pg.click('#pane1'); pg.wait_for_timeout(300); pg.keyboard.press('h'); pg.wait_for_timeout(1500); print('H on the held (release):', panes())
    pg.keyboard.press('c'); pg.wait_for_timeout(800); print('leaving Compare clears the hold:', not pg.evaluate("document.getElementById('pane1').classList.contains('held')"))
    print('errors:', errs)
    b.close()
