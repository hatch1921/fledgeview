# 0.9.70: the top level of an organized folder is the inbox.
# A settled photo moved back to the top level by hand is offered again by Scan again; a photo moved between lens folders
# stays where it was put; a photo that has always been at the top level (no lens data) is not offered again and again.
# Fixture: /tmp/rawlib (5 Sony JPEGs with lens data, made by the snippet in tests/README.md) plus one photo with no lens data.
import sys, os, shutil, threading, http.server, functools
from playwright.sync_api import sync_playwright

MASTER = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/kit/fledgeview-dev-kit/fledgeview.html'
L = '/home/claude/libs/'
LIBS = {'exifr@7.1.3': L + 'exifr-7.1.3/dist/full.umd.js', 'jszip/3.10.1': L + 'jszip-3.10.1/dist/jszip.min.js',
        'pako@1.0.11': L + 'pako-1.0.11/dist/pako_inflate.min.js', 'utif2@4.1.0': L + 'utif2-4.1.0/UTIF.js'}
SERVE = '/home/claude/inboxserve'
shutil.rmtree(SERVE, ignore_errors=True); os.makedirs(SERVE); shutil.copy(MASTER, SERVE + '/index.html')
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8792), functools.partial(http.server.SimpleHTTPRequestHandler, directory=SERVE))
threading.Thread(target=srv.serve_forever, daemon=True).start()
FILES = sorted(f for f in os.listdir('/tmp/rawlib') if f.upper().endswith('.JPG'))

def route(r):
    for k, v in LIBS.items():
        if k in r.request.url: return r.fulfill(path=v, content_type='application/javascript')
    return r.abort()

HANDLES = """(() => { /* the headless test browser crashes when a folder handle is saved in IndexedDB; keep handles in memory instead */
  const P = IDBObjectStore.prototype.put, G = IDBObjectStore.prototype.get, R = Object.getOwnPropertyDescriptor(IDBRequest.prototype, 'result').get; window.__h = {};
  IDBObjectStore.prototype.put = function (v, k) { if (v instanceof FileSystemHandle) { window.__h[k] = v; v = '__h:' + k; } return P.call(this, v, k); };
  IDBObjectStore.prototype.get = function (k) { const r = G.call(this, k); Object.defineProperty(r, 'result', { get() { const v = R.call(r); return typeof v === 'string' && v.startsWith('__h:') ? window.__h[v.slice(4)] : v; } }); return r; };
})()"""
results = []
def check(name, ok, extra=''):
    results.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + (f'  ({extra})' if extra and not ok else ''))

TREE = """async () => { const out = {}; const walk = async (d, p) => { for await (const [n, h] of d.entries()) {
  if (h.kind === 'directory') await walk(h, p + n + '/'); else if (!n.startsWith('_fledgeview')) (out[p || '.'] = out[p || '.'] || []).push(n); } };
  await walk(window.__raw, ''); for (const k in out) out[k].sort(); return out; }"""
PLAN = "[...document.querySelectorAll('#orgPlan .orgrow')].map(r => r.innerText.replace(/\\s+/g, ' ').trim())"
MOVE = """async ([from, to, name]) => { const get = async p => { let d = window.__raw; for (const s of p ? p.split('/') : []) d = await d.getDirectoryHandle(s, { create: true }); return d; };
  const a = await get(from), b = await get(to), f = await (await a.getFileHandle(name)).getFile();
  const w = await (await b.getFileHandle(name, { create: true })).createWritable(); await w.write(f); await w.close(); await a.removeEntry(name); }"""

with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-proxy-server'])
    pg = b.new_page(viewport={'width': 1600, 'height': 900}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('dialog', lambda d: d.accept())
    pg.route(lambda u: not u.startswith('http://127.0.0.1'), route)
    pg.add_init_script("localStorage.setItem('chimp-settings', JSON.stringify({ guide: false, tipShown: true, sortAsk: false, moveWarnSeen: true, seenVersion: '0.9.73 beta' }))")
    pg.add_init_script(HANDLES)
    pg.goto('http://127.0.0.1:8792/index.html'); pg.wait_for_timeout(900)
    pg.evaluate("document.body.insertAdjacentHTML('beforeend', '<input type=file multiple id=__tf hidden>')")
    pg.set_input_files('#__tf', ['/tmp/rawlib/' + f for f in FILES])
    pg.evaluate("""async () => { const root = await navigator.storage.getDirectory(); for await (const [n] of root.entries()) await root.removeEntry(n, { recursive: true });
      const raw = await root.getDirectoryHandle('RAW', { create: true }); for (const f of document.getElementById('__tf').files) {
        const w = await (await raw.getFileHandle(f.name, { create: true })).createWritable(); await w.write(f); await w.close(); }
      const c = document.createElement('canvas'); c.width = 64; c.height = 48; c.getContext('2d').fillRect(0, 0, 64, 48);
      const nolens = await new Promise(r => c.toBlob(r, 'image/jpeg'));
      const w = await (await raw.getFileHandle('SCAN001.JPG', { create: true })).createWritable(); await w.write(nolens); await w.close();
      window.__raw = raw; window.showDirectoryPicker = async () => raw;
      FileSystemHandle.prototype.queryPermission = async () => 'granted'; FileSystemHandle.prototype.requestPermission = async () => 'granted'; document.querySelectorAll('dialog[open]').forEach(x => x.close()); }""")
    go = lambda: (pg.click('#orgGo'), pg.wait_for_timeout(300), pg.evaluate("(() => { const d = document.getElementById('moveWarnDlg'); if (d && d.open) document.getElementById('mwGo').click(); })()"), pg.wait_for_timeout(2500))

    pg.evaluate("document.getElementById('orgBtn').click()"); pg.wait_for_timeout(600)
    pg.click('#orgFolderBtn'); pg.wait_for_timeout(3000)
    plan1 = pg.evaluate(PLAN); print('first plan:', plan1)
    go(); tree = pg.evaluate(TREE); print('after first organize:', tree)
    lens = [k for k in tree if k != '.']
    check('first organize made lens folders', len(lens) >= 2, tree)
    check('the photo with no lens data goes to Unknown lens; top level empty', '.' not in tree and any('SCAN001.JPG' in v for k, v in tree.items() if 'nknown' in k), tree)

    pg.click('#orgAgainBtn'); pg.wait_for_timeout(2500)
    check('scan again: nothing to move (no-lens photo is not offered again)', pg.evaluate(PLAN) in ([], plan1[:0]) or not any('DSC' in r for r in pg.evaluate(PLAN)), pg.evaluate(PLAN))
    note_quiet = pg.evaluate("document.getElementById('orgNote').textContent"); print('note:', note_quiet)

    f600 = next(k for k in lens if '600' in k); f400 = next(k for k in lens if '400' in k and '600' not in k)
    # a. back to the inbox
    pg.evaluate(MOVE, [f600.rstrip('/'), '', 'DSC101.JPG'])
    # b. between lens folders (deliberate)
    pg.evaluate(MOVE, [f600.rstrip('/'), f400.rstrip('/'), 'DSC102.JPG'])
    pg.click('#orgAgainBtn'); pg.wait_for_timeout(2500)
    plan = pg.evaluate(PLAN); print('plan after moves:', plan)
    check('photo moved back to the top level is offered again', any('DSC101' in r for r in plan) or '1 photo' in ' '.join(plan), plan)
    check('photo moved between lens folders is not offered', not any('DSC102' in r for r in plan), plan)
    go(); tree = pg.evaluate(TREE); print('after second organize:', tree)
    check('DSC101 is back in its lens folder', 'DSC101.JPG' in tree.get(f600, []), tree)
    check('DSC102 stays where it was put', 'DSC102.JPG' in tree.get(f400, []), tree)
    check('top level is empty again', '.' not in tree, tree.get('.'))
    pg.click('#orgAgainBtn'); pg.wait_for_timeout(2500)
    check('scan again afterwards: nothing to move', not any('DSC' in r for r in pg.evaluate(PLAN)), pg.evaluate(PLAN))
    # c. a photo 0.9.69 had already recorded as "moved by hand to the top level" (settled, d = '') is sorted too
    pg.evaluate(MOVE, [f400.rstrip('/'), '', 'DSC201.JPG'])
    pg.evaluate("""async () => { const h = await window.__raw.getFileHandle('_fledgeview-index.json'); const j = JSON.parse(await (await h.getFile()).text());
      for (const [id, e] of Object.entries(j.files)) if (id.startsWith('DSC201.JPG|')) { e.d = ''; e.s = 1; }
      const w = await h.createWritable(); await w.write(JSON.stringify(j)); await w.close(); }""")
    pg.click('#orgAgainBtn'); pg.wait_for_timeout(2500)
    plan = pg.evaluate(PLAN); print('plan for a 0.9.69-recorded top-level photo:', plan)
    check('a photo already recorded at the top level by 0.9.69 is offered', any('100-400' in r for r in plan), plan)
    # d. Open folder, New photos only: top-level photos count as new
    pg.evaluate("document.getElementById('orgDlg').close()"); pg.wait_for_timeout(300)
    pg.click('#openFolder'); pg.wait_for_timeout(1500)
    if pg.evaluate("document.getElementById('scopeDlg').open"):
        pg.click('#scopeDlg [data-scope="new"]'); pg.wait_for_timeout(2500)
    shown = pg.evaluate("[...document.querySelectorAll('#strip .th')].map(t => t.getAttribute('aria-label') || t.title || '')")
    print('New photos only opened:', shown)
    check('New photos only opens the top-level photo', len(shown) == 1 and 'DSC201' in ' '.join(shown), shown)
    check('no page errors', not errs, errs)
    b.close()
srv.shutdown()
print(f'{sum(results)}/{len(results)} passed')
sys.exit(0 if all(results) else 1)
