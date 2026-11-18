from playwright.sync_api import sync_playwright
import glob, sys
folder = sys.argv[1] if len(sys.argv) > 1 else '/tmp/rawonly'
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    pg = b.new_page(viewport={'width': 1920, 'height': 1080}, color_scheme='dark'); errs = []; logs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: logs.append(m.type + ': ' + m.text) if m.type in ('error', 'warning') else None)
    pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(900)
    pg.evaluate("(() => { localStorage.clear(); localStorage.setItem('chimp-settings', JSON.stringify({ tipShown: true, sortAsk: false })); })()"); pg.reload(); pg.wait_for_timeout(1000)
    pg.evaluate("document.body.insertAdjacentHTML('beforeend', '<input type=file multiple id=__tf hidden>')")
    pg.set_input_files('#__tf', sorted(glob.glob(folder + '/*')))
    pg.evaluate("""async () => { const root = await navigator.storage.getDirectory(); for await (const [n] of root.entries()) await root.removeEntry(n, { recursive: true });
      const d = await root.getDirectoryHandle('Shoot', { create: true });
      for (const f of document.getElementById('__tf').files) { const w = await (await d.getFileHandle(f.name, { create: true })).createWritable(); await w.write(f); await w.close(); }
      window.showDirectoryPicker = async () => d; document.querySelectorAll('dialog[open]').forEach(x => x.close()); }""")
    pg.click('#openFolder'); pg.wait_for_timeout(5000)
    print('photos in the grid:', pg.evaluate("document.querySelectorAll('#strip .th').length"), '| open dialogs:', pg.evaluate("[...document.querySelectorAll('dialog[open]')].map(d => d.id)"), '| status:', pg.evaluate("document.getElementById('status').textContent"), '| toast:', pg.evaluate("document.getElementById('toast').textContent")[:80])
    print('errors:', errs); print('console:', logs[:6])
    b.close()
