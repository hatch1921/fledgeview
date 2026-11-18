from playwright.sync_api import sync_playwright
import os, json
FILES = sorted(os.path.relpath(os.path.join(d, f), '/tmp/rawlib') for d, _, fs in os.walk('/tmp/rawlib') for f in fs)
TREE = """async () => { const out = {}; const walk = async (d, p) => { for await (const [n, h] of d.entries()) { if (h.kind === 'directory') await walk(h, p + n + '/'); else (out[p || './'] = out[p || './'] || []).push(n); } }; await walk(window.__raw, ''); for (const k in out) out[k].sort(); return out; }"""
IDX = "async () => { try { const j = JSON.parse(await (await (await window.__raw.getFileHandle('_fledgeview-index.json')).getFile()).text()); const v = Object.values(j.files); return { entries: v.length, settled: v.filter(e => e.s).length, pending: v.filter(e => !e.s).length }; } catch (e) { return 'none'; } }"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    pg = b.new_page(viewport={'width': 1920, 'height': 1080}, color_scheme='dark'); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('dialog', lambda d: d.accept())
    pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(900)
    pg.evaluate("(() => { localStorage.clear(); localStorage.setItem('chimp-settings', JSON.stringify({ tipShown: true, sortAsk: false, moveWarnSeen: true })); })()"); pg.reload(); pg.wait_for_timeout(1000)
    pg.evaluate("document.body.insertAdjacentHTML('beforeend', '<input type=file multiple id=__tf hidden>')")
    pg.set_input_files('#__tf', ['/tmp/rawlib/' + f for f in FILES])
    pg.evaluate("""async (paths) => { const root = await navigator.storage.getDirectory(); for await (const [n] of root.entries()) await root.removeEntry(n, { recursive: true });
      const raw = await root.getDirectoryHandle('RAW', { create: true }); const fl = document.getElementById('__tf').files;
      for (let i = 0; i < fl.length; i++) { const parts = paths[i].split('/'); let d = raw; for (const s of parts.slice(0, -1)) d = await d.getDirectoryHandle(s, { create: true });
        const w = await (await d.getFileHandle(parts.at(-1), { create: true })).createWritable(); await w.write(fl[i]); await w.close(); }
      window.__raw = raw; window.showDirectoryPicker = async () => raw; document.querySelectorAll('dialog[open]').forEach(x => x.close()); }""", FILES)
    show = lambda label: print(f'{label}\n   plan: {pg.evaluate("[...document.querySelectorAll(\'#orgPlan .orgrow\')].map(r => r.innerText.replace(/\\\\s+/g, \' \'))")}\n   note: {pg.evaluate("document.getElementById(\'orgNote\').textContent")}\n   index: {pg.evaluate(IDX)}')
    go = lambda: (pg.click('#orgGo'), pg.wait_for_timeout(300), pg.evaluate("(() => { const d = document.getElementById('moveWarnDlg'); if (d && d.open) document.getElementById('mwGo').click(); })()"), pg.wait_for_timeout(2500))
    # 1. first scan of the RAW folder: nothing loaded in the grid
    pg.evaluate("document.getElementById('orgBtn').click()"); pg.wait_for_timeout(600)
    pg.click('#orgFolderBtn'); pg.wait_for_timeout(3000)
    show('1. FIRST SCAN (no index yet)'); print('   photos loaded in the grid:', pg.evaluate("document.querySelectorAll('#strip .th').length"))
    # 2. organize
    go(); print('2. ORGANIZE:', pg.evaluate("document.getElementById('orgStatus').textContent")); print('   index:', pg.evaluate(IDX))
    # 3. two new photos arrive at the top level, then scan again
    pg.evaluate("""async () => { const src = await (await (await window.__raw.getDirectoryHandle('Sony 600mm F4')).getFileHandle('DSC100.JPG')).getFile(); const src2 = await (await (await window.__raw.getDirectoryHandle('Sony 100-400mm F4.5-5.6')).getFileHandle('DSC200.JPG')).getFile();
      for (const [n, f] of [['DSC400.JPG', src], ['DSC401.JPG', src2]]) { const w = await (await window.__raw.getFileHandle(n, { create: true })).createWritable(); await w.write(await f.arrayBuffer()); await w.write(new Uint8Array([n === 'DSC400.JPG' ? 1 : 2])); await w.close(); } }""")
    pg.click('#orgAgainBtn'); pg.wait_for_timeout(2500); show('3. SCAN AGAIN after 2 new photos')
    go(); print('   organize:', pg.evaluate("document.getElementById('orgStatus').textContent"))
    # 4. move one organized photo by hand into a Keepers folder, then scan again
    pg.evaluate("""async () => { const d = await window.__raw.getDirectoryHandle('Sony 600mm F4'), k = await window.__raw.getDirectoryHandle('Keepers', { create: true }); const f = await (await d.getFileHandle('DSC101.JPG')).getFile();
      const w = await (await k.getFileHandle('DSC101.JPG', { create: true })).createWritable(); await w.write(f); await w.close(); await d.removeEntry('DSC101.JPG'); }""")
    pg.click('#orgAgainBtn'); pg.wait_for_timeout(2500); show('4. SCAN AGAIN after moving DSC101 into Keepers by hand')
    # 5. undo the last organize: those photos are pending again
    pg.click('#orgUndo'); pg.wait_for_timeout(3000); show('5. AFTER UNDO of the last organize')
    print('   folder:', json.dumps(pg.evaluate(TREE)))
    pg.evaluate("document.getElementById('orgDlg').close()")
    pg.evaluate("document.getElementById('orgDlg').close()")
    # organize everything so the top level is empty, then remember "This folder only"
    pg.evaluate("document.getElementById('orgBtn').click()"); pg.wait_for_timeout(500); pg.click('#orgAgainBtn'); pg.wait_for_timeout(2000)
    if pg.evaluate("!document.getElementById('orgGo').disabled"): go()
    pg.evaluate("document.getElementById('orgDlg').close()")
    pg.evaluate("(() => { const s = JSON.parse(localStorage.getItem('chimp-settings')); s.openScope = 'top'; localStorage.setItem('chimp-settings', JSON.stringify(s)); })()")
    pg.reload(); pg.wait_for_timeout(1000); pg.evaluate("(async () => { const root = await navigator.storage.getDirectory(); const raw = await root.getDirectoryHandle('RAW'); window.__raw = raw; window.showDirectoryPicker = async () => raw; document.querySelectorAll('dialog[open]').forEach(x => x.close()); })()"); pg.wait_for_timeout(500)
    pg.click('#openFolder'); pg.wait_for_timeout(2500)
    print('   window says:', pg.evaluate("document.getElementById('scopeSub').textContent")[:120])
    print('   choices:', pg.evaluate("[...document.querySelectorAll('#scopeDlg [data-scope]')].map(b => b.innerText.replace(/\\n/g, ': ') + (b.disabled ? ' [dimmed]' : ''))"))
    pg.click('#scopeDlg [data-scope="all"]'); pg.wait_for_timeout(2500)
    print('   chose Everything -> photos in the grid:', pg.evaluate("document.querySelectorAll('#strip .th').length"))
    print('REMEMBERED "This folder only", top level empty -> photos:', pg.evaluate("document.querySelectorAll('#strip .th').length"), '| dialogs:', pg.evaluate("[...document.querySelectorAll('dialog[open]')].map(d => d.id)"), '| toast:', repr(pg.evaluate("document.getElementById('toast').textContent")))
    print('errors:', errs)
    b.close()
