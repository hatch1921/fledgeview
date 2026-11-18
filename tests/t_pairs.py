from playwright.sync_api import sync_playwright
import glob, os
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    pg = b.new_page(viewport={'width': 1920, 'height': 1080}, color_scheme='dark'); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('dialog', lambda d: d.accept())
    pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(900)
    pg.evaluate("(() => { localStorage.clear(); localStorage.setItem('chimp-settings', JSON.stringify({ tipShown: true, sortAsk: false, relinkSeen: true })); })()"); pg.reload(); pg.wait_for_timeout(1000)
    # a real folder with write access (the browser's private file system stands in for the user's folder)
    pg.evaluate("document.body.insertAdjacentHTML('beforeend', '<input type=file multiple id=__tf hidden>')")
    pg.set_input_files('#__tf', sorted(glob.glob('/tmp/pairtest/*')))
    pg.evaluate("""async () => { const root = await navigator.storage.getDirectory(); for await (const [n] of root.entries()) await root.removeEntry(n, { recursive: true });
      const d = await root.getDirectoryHandle('Shoot', { create: true });
      for (const f of document.getElementById('__tf').files) { const w = await (await d.getFileHandle(f.name, { create: true })).createWritable(); await w.write(f); await w.close(); }
      window.__dir = d; window.showDirectoryPicker = async () => d;
      document.querySelectorAll('dialog[open]').forEach(x => x.close()); }""")
    pg.click('#openFolder'); pg.wait_for_timeout(5000); pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    names = pg.evaluate("[...document.querySelectorAll('#strip .th')].map(t => t.getAttribute('aria-label'))")
    print('photos in the grid:', names, '| toast:', pg.evaluate("document.getElementById('toast').textContent")[:70])
    pg.click('#strip [aria-label="DSC0001.JPG"]'); pg.wait_for_timeout(2500)
    print('on screen:', pg.evaluate("document.getElementById('oFormat').textContent"), '| shown at', pg.evaluate("(() => { const c = document.querySelector('#pane0 canvas.img'); return c ? c.width + 'x' + c.height : '?'; })()"))
    pg.evaluate("(() => { const b = document.getElementById('infoToggle'); if (b.getAttribute('aria-expanded') !== 'true') b.click(); })()"); pg.wait_for_timeout(500)
    t = pg.evaluate("document.getElementById('rows').innerText"); i = t.find('Paired raw'); print('Photo info:', t[i:i + 40].replace('\n', ' '))
    print('file type filter choices:', pg.evaluate("[...document.getElementById('fType').options].map(o => o.textContent)"))
    # rate the pairs: pick DSC0001, reject dsc0004
    pg.keyboard.press('p'); pg.wait_for_timeout(400)
    pg.click('#strip [aria-label="dsc0004.jpg"]'); pg.wait_for_timeout(600); pg.keyboard.press('x'); pg.wait_for_timeout(400)
    # write ratings
    pg.evaluate("document.getElementById('writeXmp').click()"); pg.wait_for_timeout(1500)
    print('Write ratings:', pg.evaluate("document.getElementById('toast').textContent"))
    # move picks and rejects
    pg.evaluate("document.getElementById('moveRej').click()"); pg.wait_for_timeout(700); pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => { if (d.id !== 'moveDlg' && !d.querySelector('#mvGo')) d.close(); })")
    pg.click('#mvGo'); pg.wait_for_timeout(1200)
    pg.evaluate("(() => { const d = document.getElementById('moveWarnDlg'); if (d && d.open) { const b = [...d.querySelectorAll('button')].find(x => /move|continue|ok/i.test(x.textContent) && !/cancel/i.test(x.textContent)); b && b.click(); } })()"); pg.wait_for_timeout(3500)
    print('after Move:', pg.evaluate("document.getElementById('toast').textContent"))
    tree = pg.evaluate("""async () => { const out = {}; const walk = async (d, p) => { for await (const [n, h] of d.entries()) { if (h.kind === 'directory') await walk(h, p + n + '/'); else (out[p || './'] = out[p || './'] || []).push(n); } }; await walk(window.__dir, ''); for (const k in out) out[k].sort(); return out; }""")
    print('folder after the move:'); [print('  ', k, v) for k, v in sorted(tree.items())]
    print('errors:', errs)
    b.close()
