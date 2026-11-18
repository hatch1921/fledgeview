from playwright.sync_api import sync_playwright
import glob
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    pg = b.new_page(viewport={'width': 1920, 'height': 1080}, color_scheme='dark'); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(900)
    pg.evaluate("(() => { const s = JSON.parse(localStorage.getItem('chimp-settings') || '{}'); s.tipShown = true; localStorage.setItem('chimp-settings', JSON.stringify(s)); })()"); pg.reload(); pg.wait_for_timeout(900)
    # simulate raw files whose standard thumbnail slot is empty
    pg.evaluate("(() => { document.querySelectorAll('dialog[open]').forEach(d => d.close()); exifr.thumbnail = async () => undefined; })()")
    files = ['/mnt/user-data/uploads/A1200001.ARW', '/tmp/tifftest/8bit-uncompressed.tif', '/tmp/tifftest/16bit-zip-predictor.tif', '/tmp/tifftest/16bit-lzw-tiled.tif', '/tmp/vid/Wildlife/2026-09-04/A1208483.jpg']
    pg.set_input_files('#fileInput', files); pg.wait_for_timeout(9000)
    print('thumbnails (never viewed):')
    for n in [f.split('/')[-1] for f in files]:
        print(f'  {n:24s}', pg.evaluate(f"""(() => {{ const t = document.querySelector('#strip [aria-label="{n}"]'); const im = t && t.querySelector('img'); return im && im.src && im.naturalWidth ? 'image ' + im.naturalWidth + 'x' + im.naturalHeight : 'file type only'; }})()"""))
    # export: Photos list, button label, Save to
    pg.evaluate("""async () => { const root = await navigator.storage.getDirectory(); for await (const [n] of root.entries()) await root.removeEntry(n, { recursive: true });
      window.__exp = await root.getDirectoryHandle('My exports', { create: true }); window.__asked = 0;
      window.showDirectoryPicker = async o => { window.__asked++; return window.__exp; }; }""")
    pg.click('#strip [aria-label="A1208483.jpg"]'); pg.wait_for_timeout(1000)
    pg.click('#webBtn'); pg.wait_for_timeout(700)
    print('Photos list:', pg.evaluate("[...document.getElementById('wSrc').options].map(o => o.textContent)"))
    print('selected:', pg.evaluate("document.getElementById('wSrc').value"), '| button:', pg.evaluate("document.getElementById('webGo').textContent"))
    pg.select_option('#wSrc', 'view'); pg.wait_for_timeout(200); print('Photos shown -> button:', pg.evaluate("document.getElementById('webGo').textContent"))
    pg.select_option('#wSrc', 'current'); pg.wait_for_timeout(200)
    print('Save to row shown:', pg.evaluate("!document.getElementById('wOutRow').hidden"), '| choices:', pg.evaluate("[...document.getElementById('wOut').options].map(o => o.textContent)"))
    pg.click('#wOutPick'); pg.wait_for_timeout(500)
    print('after Choose folder:', pg.evaluate("document.getElementById('wOut').selectedOptions[0].textContent"), '|', pg.evaluate("document.getElementById('wDest').textContent"))
    asked0 = pg.evaluate("window.__asked")
    pg.click('#webGo'); pg.wait_for_timeout(4000)
    print('export: folder prompts during export:', pg.evaluate("window.__asked") - asked0, '| status:', pg.evaluate("document.getElementById('webStatus').textContent")[:60])
    print('files in My exports:', pg.evaluate("(async () => { const out = []; for await (const [n] of window.__exp.entries()) out.push(n); return out; })()"))
    pg.evaluate("document.getElementById('webDlg').close()"); pg.reload(); pg.wait_for_timeout(1200)
    pg.evaluate("(() => { document.querySelectorAll('dialog[open]').forEach(d => d.close()); })()")
    pg.set_input_files('#fileInput', ['/tmp/vid/Wildlife/2026-09-04/A1208483.jpg']); pg.wait_for_timeout(1500)
    pg.click('#webBtn'); pg.wait_for_timeout(900)
    print('after reload, Save to remembers:', pg.evaluate("document.getElementById('wOut').selectedOptions[0].textContent"))
    print('errors:', errs)
    b.close()
