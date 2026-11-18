from playwright.sync_api import sync_playwright
from PIL import Image
import glob, io
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    shots = []
    for size in (300, 150):
        pg = b.new_page(viewport={'width': 1920, 'height': 1080}, color_scheme='dark'); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(900)
        pg.evaluate("(() => { localStorage.clear(); localStorage.setItem('chimp-settings', JSON.stringify({ tipShown: true, sortAsk: false, look: 'clean' })); })()"); pg.reload(); pg.wait_for_timeout(900)
        pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        files = sorted(glob.glob('/tmp/vid/Wildlife/2026-09-04/A12068*.jpg')) + ['/tmp/vid/Wildlife/2026-09-04/A1208483.jpg', '/tmp/vid/Wildlife/2026-09-04/A1209362.jpg']
        pg.set_input_files('#fileInput', files); pg.wait_for_timeout(2500); pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        pg.evaluate("(() => { const s = document.getElementById('sortSel'); s.value = 'burst'; s.dispatchEvent(new Event('change')); })()"); pg.wait_for_timeout(3500)
        pg.evaluate(f"(() => {{ const t = document.getElementById('tSize'); t.value = {size}; t.dispatchEvent(new Event('input')); }})()"); pg.wait_for_timeout(600)
        names = pg.evaluate("[...document.querySelectorAll('#strip .th')].map(t => t.getAttribute('aria-label'))")
        setv = lambda k, v: pg.evaluate(f"(() => {{ const i = document.getElementById('e_{k}'); i.value = {v}; i.dispatchEvent(new Event('input')); }})()")
        pg.click(f'#strip [aria-label="{names[0]}"]'); pg.wait_for_timeout(500); pg.click('#cropTab'); pg.wait_for_timeout(600); pg.select_option('#eCropAr', '1:1'); pg.wait_for_timeout(300); pg.click('#eCropBtn'); pg.wait_for_timeout(500)
        pg.click(f'#strip [aria-label="{names[1]}"]'); pg.wait_for_timeout(500); pg.click('#editTab'); pg.wait_for_timeout(600); setv('exp', 20); setv('vib', 15); pg.wait_for_timeout(300); pg.click('#editTab'); pg.wait_for_timeout(500)
        pg.click(f'#strip [aria-label="{names[2]}"]'); pg.wait_for_timeout(500); pg.click('#cropTab'); pg.wait_for_timeout(600); pg.select_option('#eCropAr', '4:5'); setv('rot', 20); pg.wait_for_timeout(300); pg.click('#eCropBtn'); pg.wait_for_timeout(500)
        pg.click('#editTab'); pg.wait_for_timeout(600); setv('exp', 20); pg.wait_for_timeout(300); pg.click('#editTab'); pg.wait_for_timeout(700)
        for n in names[:3]: print(size, n, '|', pg.evaluate(f"""(() => {{ const e = document.querySelector('#strip [aria-label="{n}"] .ed'); return e ? e.textContent + '  [tip: ' + e.title + ']' : 'no label'; }})()"""))
        r = pg.locator('#strip').bounding_box(); shots.append(Image.open(io.BytesIO(pg.screenshot(clip={'x': r['x'], 'y': r['y'], 'width': r['width'], 'height': min(r['height'], 480)}))))
        print('errors:', errs); pg.close()
    s = Image.new('RGB', (sum(i.width for i in shots) + 10, max(i.height for i in shots)), 'white'); x = 0
    for i in shots: s.paste(i, (x, 0)); x += i.width + 10
    s.save('/tmp/edkind.png')
    b.close()
