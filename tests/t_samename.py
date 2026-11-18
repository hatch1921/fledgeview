# Change list item 11: same-name photos in Organize and Import. Fixtures: /tmp/rawlib (5 Sony JPEGs) and /tmp/rawlib_b
# (DSC100 = byte-identical copy, DSC101 = a different photo with the same name, DSC103 = new). See tests/README.md.
import sys, os, shutil, threading, http.server, functools
from playwright.sync_api import sync_playwright

MASTER = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/kit/fledgeview-dev-kit/fledgeview.html'
L = '/home/claude/libs/'
LIBS = {'exifr@7.1.3': L + 'exifr-7.1.3/dist/full.umd.js', 'jszip/3.10.1': L + 'jszip-3.10.1/dist/jszip.min.js',
        'pako@1.0.11': L + 'pako-1.0.11/dist/pako_inflate.min.js', 'utif2@4.1.0': L + 'utif2-4.1.0/UTIF.js'}
SERVE = '/home/claude/snserve'
shutil.rmtree(SERVE, ignore_errors=True); os.makedirs(SERVE); shutil.copy(MASTER, SERVE + '/index.html')
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8795), functools.partial(http.server.SimpleHTTPRequestHandler, directory=SERVE))
threading.Thread(target=srv.serve_forever, daemon=True).start()
def route(r):
    for k, v in LIBS.items():
        if k in r.request.url: return r.fulfill(path=v, content_type='application/javascript')
    return r.abort()
HANDLES = """(() => { /* the headless test browser crashes when a folder handle is saved in IndexedDB; keep handles in memory instead */
  const P = IDBObjectStore.prototype.put, G = IDBObjectStore.prototype.get, R = Object.getOwnPropertyDescriptor(IDBRequest.prototype, 'result').get; window.__h = {};
  IDBObjectStore.prototype.put = function (v, k) { if (v instanceof FileSystemHandle) { window.__h[k] = v; v = '__h:' + k; } return P.call(this, v, k); };
  IDBObjectStore.prototype.get = function (k) { const r = G.call(this, k); Object.defineProperty(r, 'result', { get() { const v = R.call(r); return typeof v === 'string' && v.startsWith('__h:') ? window.__h[v.slice(4)] : v; } }); return r; };
  FileSystemHandle.prototype.queryPermission = async () => 'granted'; FileSystemHandle.prototype.requestPermission = async () => 'granted';
})()"""
TREE = """async (name) => { const out = {}; const top = await (await navigator.storage.getDirectory()).getDirectoryHandle(name);
  const walk = async (d, p) => { for await (const [n, h] of d.entries()) { if (h.kind === 'directory') await walk(h, p + n + '/');
    else if (!n.startsWith('_fledgeview')) (out[p || '.'] = out[p || '.'] || []).push(n + ':' + (await h.getFile()).size); } };
  await walk(top, ''); for (const k in out) out[k].sort(); return out; }"""
PUT = """async ([folder, sub, ids]) => { const root = await navigator.storage.getDirectory(); let d = await root.getDirectoryHandle(folder, { create: true });
  for (const s of sub ? sub.split('/') : []) d = await d.getDirectoryHandle(s, { create: true });
  for (const f of document.getElementById(ids).files) { const w = await (await d.getFileHandle(f.name, { create: true })).createWritable(); await w.write(f); await w.close(); } }"""
results = []
def check(name, ok, extra=''):
    results.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + (f'  ({extra})' if extra and not ok else ''))
A = sorted('/tmp/rawlib/' + f for f in os.listdir('/tmp/rawlib'))
B = sorted('/tmp/rawlib_b/' + f for f in os.listdir('/tmp/rawlib_b'))
sz = lambda f: os.path.getsize(f)

with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-proxy-server'])
    pg = b.new_page(viewport={'width': 1600, 'height': 1000}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('dialog', lambda d: d.accept())
    pg.route(lambda u: not u.startswith('http://127.0.0.1'), route)
    pg.add_init_script(HANDLES)
    pg.add_init_script("localStorage.setItem('chimp-settings', JSON.stringify({ guide: false, tipShown: true, sortAsk: false, moveWarnSeen: true, seenVersion: '0.9.73 beta' }))")
    pg.goto('http://127.0.0.1:8795/index.html'); pg.wait_for_timeout(900)
    pg.evaluate("document.body.insertAdjacentHTML('beforeend', '<input type=file multiple id=__a hidden><input type=file multiple id=__b hidden>')")
    pg.set_input_files('#__a', A); pg.set_input_files('#__b', B)
    pg.evaluate("async () => { const r = await navigator.storage.getDirectory(); for await (const [n] of r.entries()) await r.removeEntry(n, { recursive: true }); document.querySelectorAll('dialog[open]').forEach(x => x.close()); }")

    # ---------- Organize: lens folder already holds DSC100 (same photo) and DSC101 (a different photo) ----------
    pg.evaluate(PUT, ['RAW', '', '__b'])                         # top level: DSC100 (copy), DSC101 (different), DSC103 (new)
    pg.evaluate(PUT, ['RAW', 'Sony 600mm F4', '__a'])            # lens folder: the original A set (all five, by name)
    pg.evaluate("""async () => { const raw = await (await navigator.storage.getDirectory()).getDirectoryHandle('RAW');
      const lens = await raw.getDirectoryHandle('Sony 600mm F4'); for (const n of ['DSC102.JPG', 'DSC200.JPG', 'DSC201.JPG']) await lens.removeEntry(n);
      window.__raw = raw; window.showDirectoryPicker = async () => raw; }""")
    pg.evaluate("document.getElementById('orgBtn').click()"); pg.wait_for_timeout(600)
    pg.click('#orgFolderBtn'); pg.wait_for_timeout(3500)
    note = pg.inner_text('#orgNote'); print('plan note:', note)
    check('plan counts the different photo with the same name', '1 has the same name as a different photo' in note, note)
    check('plan counts the likely copy', '1 looks like a copy of a photo already there' in note and '_already there' in note, note)
    pg.click('#orgGo'); pg.wait_for_timeout(300)
    pg.evaluate("(() => { const d = document.getElementById('moveWarnDlg'); if (d && d.open) document.getElementById('mwGo').click(); })()"); pg.wait_for_timeout(3000)
    st = pg.inner_text('#orgStatus'); print('organize done:', st)
    tree = pg.evaluate(TREE, 'RAW'); print('tree:', tree)
    L6 = 'Sony 600mm F4/'
    check('nothing left at the top level', '.' not in tree, tree.get('.'))
    check('new photo goes into the lens folder', any(x.startswith('DSC103.JPG') for x in tree.get(L6, [])), tree.get(L6))
    check('different photo with the same name goes into _same name, original untouched',
          tree.get(L6 + '_same name/') == [f'DSC101.JPG:{sz("/tmp/rawlib_b/DSC101.JPG")}'] and f'DSC101.JPG:{sz("/tmp/rawlib/DSC101.JPG")}' in tree.get(L6, []), tree)
    check('true copy goes into _already there', tree.get(L6 + '_already there/') == [f'DSC100.JPG:{sz("/tmp/rawlib/DSC100.JPG")}'], tree)
    check('finished message reports both', '3 photos sorted' in st and '1 had the same name as a different photo' in st and '1 was a copy' in st, st)
    pg.click('#orgUndo'); pg.wait_for_timeout(2500)
    tree = pg.evaluate(TREE, 'RAW'); print('after undo:', tree)
    check('Undo moves all three back to the top level', sorted(x.split(':')[0] for x in tree.get('.', [])) == ['DSC100.JPG', 'DSC101.JPG', 'DSC103.JPG'], tree.get('.'))
    check('Undo leaves the originals in the lens folder', sorted(x.split(':')[0] for x in tree.get(L6, [])) == ['DSC100.JPG', 'DSC101.JPG'], tree.get(L6))
    pg.evaluate("document.getElementById('orgDlg').close()")

    # ---------- Import: card A, then card B (DSC100 same photo, DSC101 different photo, DSC103 new) ----------
    def run_import(card):
        pg.evaluate(PUT, [card, '', '__a' if card == 'CARDA' else '__b'])
        pg.evaluate("""async (card) => { const r = await navigator.storage.getDirectory(); const c = await r.getDirectoryHandle(card); const m = await r.getDirectoryHandle('MAIN', { create: true });
          window.__seq = [c, m]; window.showDirectoryPicker = async () => window.__seq.shift() || m; }""", card)
        pg.evaluate("document.getElementById('impBtn').click()"); pg.wait_for_timeout(800)
        pg.click('#impSrcBtn'); pg.wait_for_timeout(2500)
        if pg.is_enabled('#impDstBtn'): pg.click('#impDstBtn'); pg.wait_for_timeout(1500)
        pg.evaluate("document.getElementById('impOpen') && (document.getElementById('impOpen').checked = false)")
        pg.wait_for_timeout(1500)
        plan = pg.inner_text('#impNote')
        pg.evaluate("document.getElementById('impProgTxt').textContent = ''")
        pg.click('#impGo'); pg.wait_for_function("document.getElementById('impProgTxt').textContent.startsWith('Done')", timeout=20000)
        done = pg.inner_text('#impProgTxt'); pg.evaluate("document.getElementById('impDlg').close()")
        return plan, done
    plan, done = run_import('CARDA'); print('import A:', done)
    plan, done = run_import('CARDB'); print('import B plan:', plan); print('import B done:', done)
    check('Import plan: already imported counted', '1 looks already imported' in plan, plan)
    check('Import plan: same name, different photo counted', '1 has the same name as a different photo' in plan, plan)
    check('Import done: copied two, skipped one, one into _same name', 'Copied 2 photos' in done and '1 had the same name as a different photo' in done and '1 was already imported: skipped' in done, done)
    tree = pg.evaluate(TREE, 'MAIN'); print('main:', tree)
    same = [k for k in tree if k.endswith('_same name/')]
    check('different photo copied into a _same name folder beside the original', len(same) == 1 and tree[same[0]] == [f'DSC101.JPG:{sz("/tmp/rawlib_b/DSC101.JPG")}'], tree)
    check('no problems reported', 'problem' not in done, done)
    check('no page errors', not errs, errs)
    b.close()
srv.shutdown()
print(f'{sum(results)}/{len(results)} passed')
sys.exit(0 if all(results) else 1)
