from playwright.sync_api import sync_playwright
import glob
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    pg = b.new_page(viewport={'width': 1920, 'height': 1080}, color_scheme='dark'); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(900)
    pg.evaluate("(() => { localStorage.clear(); localStorage.setItem('chimp-settings', JSON.stringify({ tipShown: true, sortAsk: false })); })()"); pg.reload(); pg.wait_for_timeout(900)
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    pg.set_input_files('#fileInput', sorted(glob.glob('/tmp/vid/Wildlife/2026-09-04/*.jpg'))); pg.wait_for_timeout(3500)
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    pg.evaluate("(() => { const s = document.getElementById('sortSel'); s.value = 'burst'; s.dispatchEvent(new Event('change')); })()")
    pg.wait_for_function("!document.getElementById('status').textContent", timeout=90000); pg.wait_for_timeout(2500)
    labels = pg.evaluate("[...document.querySelectorAll('#strip .th .sp')].map(s => [s.closest('.th').getAttribute('aria-label'), s.textContent, s.className.replace('sp ', ''), s.title.slice(0, 70)])")
    for l in labels: print('  ', l)
    print('any Soft or Sharp words left:', any(w in (l[1]) for l in labels for w in ('Soft', 'Sharp')))
    pg.click('#strip [aria-label="%s"]' % labels[-1][0]); pg.wait_for_timeout(900)
    print('info line:', pg.evaluate("document.getElementById('oSharp').textContent"))
    print('filter name:', pg.evaluate("[...document.getElementById('filterSel').options].find(o => o.value === 'soft').textContent"))
    pg.screenshot(path='/tmp/sharplabels.png', clip=pg.locator('#strip').bounding_box())
    print('errors:', errs)
    b.close()
