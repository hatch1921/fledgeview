from playwright.sync_api import sync_playwright
from PIL import Image
import io
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    pg = b.new_page(viewport={'width': 1920, 'height': 1080}, color_scheme='dark'); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(900)
    pg.evaluate("(() => { localStorage.clear(); localStorage.setItem('chimp-settings', JSON.stringify({ tipShown: true, sortAsk: false })); })()"); pg.reload(); pg.wait_for_timeout(1000)
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    pg.set_input_files('#fileInput', ['/tmp/lrtest/retro-22322.jpg', '/tmp/lrtest/lightroom-defaults.jpg', '/mnt/user-data/uploads/A1200001.ARW']); pg.wait_for_timeout(3000)
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    for n in ['retro-22322.jpg', 'lightroom-defaults.jpg', 'A1200001.ARW']:
        pg.click(f'#strip [aria-label="{n}"]'); pg.wait_for_timeout(1500)
        st = pg.evaluate("({ dot: !document.getElementById('lrDot').hidden, card: !document.getElementById('pmCard').disabled, note: document.getElementById('pmNote').hidden ? '' : document.getElementById('pmNote').textContent })")
        print(f'{n:24s}', st)
    pg.click('#strip [aria-label="retro-22322.jpg"]'); pg.wait_for_timeout(1200)
    pg.click('#presetMenuBtn'); pg.wait_for_timeout(300)
    r = pg.locator('#presetMenuBtn').bounding_box(); shot = Image.open(io.BytesIO(pg.screenshot(clip={'x': r['x'] - 300, 'y': 0, 'width': 700, 'height': 230})))
    shot.save('/tmp/pmenu.png')
    pg.click('#pmCard'); pg.wait_for_timeout(800); print('Make recipe card opens the card window:', pg.evaluate("document.getElementById('recipeDlg').open"))
    pg.evaluate("document.getElementById('recipeDlg').close()")
    pg.click('#presetMenuBtn'); pg.wait_for_timeout(300); pg.click('#pmShow'); pg.wait_for_timeout(900)
    print('Show Lightroom settings opens Photo info:', pg.evaluate("document.getElementById('infoToggle').getAttribute('aria-expanded')"))
    print('errors:', errs); pg.close()
    for w, h in [(1366, 768), (1440, 900), (1920, 1080)]:
        for look in ('Camera', 'Clean'):
            pg = b.new_page(viewport={'width': w, 'height': h}, color_scheme='dark')
            pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(800)
            pg.evaluate(f"(() => {{ document.querySelectorAll('dialog[open]').forEach(d => d.close()); document.getElementById('look{look}').click(); }})()"); pg.wait_for_timeout(300)
            fit = pg.evaluate("""(() => { const bar = document.querySelector('header, .top, .toolbar') || document.getElementById('presetMenuBtn').closest('header,nav,div'); const rows = new Set([...document.querySelectorAll('header .btn, .toolbar .btn')].filter(b => b.offsetParent).map(b => Math.round(b.getBoundingClientRect().top))); return { oneRow: rows.size <= 1, noSideScroll: document.documentElement.scrollWidth <= innerWidth }; })()""")
            print(f'{w}x{h} {look}:', fit)
            pg.close()
    b.close()
