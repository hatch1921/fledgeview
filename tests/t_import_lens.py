from playwright.sync_api import sync_playwright
import os, json
CARD = sorted(os.path.relpath(os.path.join(d, f), '/tmp/cardtest') for d, _, fs in os.walk('/tmp/cardtest') for f in fs)
RAWF = sorted(os.path.relpath(os.path.join(d, f), '/tmp/rawlib') for d, _, fs in os.walk('/tmp/rawlib') for f in fs)
TREE = """async () => { const out = {}; const walk = async (d, p) => { for await (const [n, h] of d.entries()) { if (h.kind === 'directory') await walk(h, p + n + '/'); else (out[p || './'] = out[p || './'] || []).push(n); } }; await walk(window.__raw, ''); for (const k in out) out[k].sort(); return out; }"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    pg = b.new_page(viewport={'width': 1920, 'height': 1080}, color_scheme='dark'); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('dialog', lambda d: d.accept())
    pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(900)
    pg.evaluate("(() => { localStorage.clear(); localStorage.setItem('chimp-settings', JSON.stringify({ tipShown: true, sortAsk: false, moveWarnSeen: true })); })()"); pg.reload(); pg.wait_for_timeout(1000)
    pg.evaluate("document.body.insertAdjacentHTML('beforeend', '<input type=file multiple id=__c hidden><input type=file multiple id=__r hidden>')")
    pg.set_input_files('#__c', ['/tmp/cardtest/' + f for f in CARD]); pg.set_input_files('#__r', ['/tmp/rawlib/' + f for f in RAWF])
    pg.evaluate("""async ([cp, rp]) => { const root = await navigator.storage.getDirectory(); for await (const [n] of root.entries()) await root.removeEntry(n, { recursive: true });
      const put = async (top, paths, inp) => { const base = await root.getDirectoryHandle(top, { create: true }); const fl = document.getElementById(inp).files;
        for (let i = 0; i < fl.length; i++) { const parts = paths[i].split('/'); let d = base; for (const s of parts.slice(0, -1)) d = await d.getDirectoryHandle(s, { create: true });
          const w = await (await d.getFileHandle(parts.at(-1), { create: true })).createWritable(); await w.write(fl[i]); await w.close(); } return base; };
      const card = await put('CARD', cp, '__c'), raw = await put('RAW', rp, '__r');
      // the RAW folder starts already organized, with its index, as after an earlier Organize
      const q = [card, raw]; window.showDirectoryPicker = async () => q.shift() || raw; window.__raw = raw; window.__card = card;
      document.querySelectorAll('dialog[open]').forEach(x => x.close()); }""", [CARD, RAWF])
    # first organize the RAW folder once, so it has an index (4 new top-level photos get placed)
    pg.evaluate("window.showDirectoryPicker = async () => window.__raw")
    pg.evaluate("document.getElementById('orgBtn').click()"); pg.wait_for_timeout(500); pg.click('#orgFolderBtn'); pg.wait_for_timeout(2500)
    pg.click('#orgGo'); pg.wait_for_timeout(2500); pg.evaluate("document.getElementById('orgDlg').close()")
    print('RAW organized first:', pg.evaluate("Object.keys(document) && 1") and 'ok')
    # import the card into RAW with Lens only
    pg.evaluate("(() => { const q = [window.__card, window.__raw]; window.showDirectoryPicker = async () => q.shift() || window.__raw; })()")
    pg.evaluate("document.getElementById('impBtn').click()"); pg.wait_for_timeout(800)
    pg.click('#impSrcBtn'); pg.wait_for_timeout(2500); pg.click('#impDstBtn'); pg.wait_for_timeout(1500)
    pg.select_option('#impPreset', '{lens}'); pg.wait_for_timeout(1500)
    print('import plan:', pg.evaluate("[...document.querySelectorAll('#impPlan .orgrow')].map(r => r.innerText.replace(/\\s+/g, ' '))"))
    pg.evaluate("document.getElementById('impOpen').checked = false"); pg.click('#impGo'); pg.wait_for_timeout(4000)
    print('import:', pg.evaluate("document.getElementById('impProgTxt').textContent")[:110])
    pg.evaluate("document.getElementById('impDlg').close()")
    print('RAW folder after import:'); [print('  ', k, v) for k, v in sorted(pg.evaluate(TREE).items())]
    # organize scan afterwards: the imported photos should need no reading and no moving
    pg.evaluate("window.showDirectoryPicker = async () => window.__raw")
    pg.evaluate("document.getElementById('orgBtn').click()"); pg.wait_for_timeout(500); pg.click('#orgFolderBtn'); pg.wait_for_timeout(2500)
    print('organize scan after import:', pg.evaluate("[...document.querySelectorAll('#orgPlan .orgrow')].map(r => r.innerText.replace(/\\s+/g, ' '))"), '|', pg.evaluate("document.getElementById('orgNote').textContent"))
    print('errors:', errs)
    b.close()
