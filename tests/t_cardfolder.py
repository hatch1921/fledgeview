# 0.9.72: recipe cards saved to a chosen folder, never replacing a file; Use Downloads; hidden where folders aren't available;
# the Shape list's choices use the dialog's colors. Fixture: /tmp/lrtest/punchy-wide.jpg (see tests/README.md).
import sys, os, shutil, threading, http.server, functools
from playwright.sync_api import sync_playwright

MASTER = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/kit/fledgeview-dev-kit/fledgeview.html'
L = '/home/claude/libs/'
LIBS = {'exifr@7.1.3': L + 'exifr-7.1.3/dist/full.umd.js', 'jszip/3.10.1': L + 'jszip-3.10.1/dist/jszip.min.js',
        'pako@1.0.11': L + 'pako-1.0.11/dist/pako_inflate.min.js', 'utif2@4.1.0': L + 'utif2-4.1.0/UTIF.js'}
SERVE = '/home/claude/cfserve'
shutil.rmtree(SERVE, ignore_errors=True); os.makedirs(SERVE); shutil.copy(MASTER, SERVE + '/index.html')
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8794), functools.partial(http.server.SimpleHTTPRequestHandler, directory=SERVE))
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
results = []
def check(name, ok, extra=''):
    results.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + (f'  ({extra})' if extra and not ok else ''))
LIST = "async () => { const d = await (await navigator.storage.getDirectory()).getDirectoryHandle('Cards'); const o = []; for await (const [n] of d.entries()) o.push(n); return o.sort(); }"

with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-proxy-server'])
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000}, accept_downloads=True, color_scheme='dark'); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route(lambda u: not u.startswith('http://127.0.0.1'), route)
    pg.add_init_script(HANDLES)
    pg.add_init_script("localStorage.setItem('chimp-settings', JSON.stringify({ guide: false, tipShown: true, sortAsk: false, seenVersion: '0.9.73 beta', recipe: { shape: 'p45', preset: false } }))")
    pg.goto('http://127.0.0.1:8794/index.html'); pg.wait_for_timeout(900)
    pg.evaluate("""async () => { const r = await navigator.storage.getDirectory(); for await (const [n] of r.entries()) await r.removeEntry(n, { recursive: true });
      const d = await r.getDirectoryHandle('Cards', { create: true }); window.showDirectoryPicker = async () => d; }""")
    pg.set_input_files('#fileInput', ['/tmp/lrtest/punchy-wide.jpg']); pg.wait_for_timeout(2500)
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    pg.wait_for_function("!document.getElementById('pmCard').disabled", timeout=10000)
    pg.evaluate("document.getElementById('pmCard').click()"); pg.wait_for_timeout(800); pg.fill('#rTitle', 'Punchy')
    # menu colors: options use the dialog's panel and ink colors (dark here)
    oc = pg.evaluate("(() => { const o = getComputedStyle(document.querySelector('#rShape option')); return [o.backgroundColor, o.color]; })()")
    print('option colors:', oc)
    check('Shape list choices use the dark panel color', oc[0] == 'rgb(33, 36, 39)' and oc[1] == 'rgb(227, 228, 224)', oc)
    check('Save to starts as Downloads', pg.inner_text('#rDest') == 'Your Downloads folder' and pg.is_visible('#rDestBtn'))
    pg.click('#rDestBtn'); pg.wait_for_timeout(500)
    check('chosen folder is shown', pg.inner_text('#rDest') == 'Cards' and pg.inner_text('#rDestBtn') == 'Change\u2026' and pg.is_visible('#rDestReset'))
    dls = []; pg.on('download', lambda d: dls.append(d))
    def save():
        pg.evaluate("rStatus.textContent = ''"); pg.click('#rSave'); pg.wait_for_function("rStatus.textContent.startsWith('Saved') || rStatus.textContent.startsWith('Downloaded') || rStatus.textContent.includes('wasn')", timeout=30000); pg.wait_for_timeout(400)
        return pg.inner_text('#rStatus')
    st = save(); print('status:', st)
    check('saved into the folder, no download', pg.evaluate(LIST) == ['Punchy (4x5).jpg'] and not dls, (pg.evaluate(LIST), len(dls)))
    check('status names the folder', st.startswith('Saved Punchy (4x5).jpg in Cards'), st)
    st = save()
    check('saving again adds (2), keeps the first', pg.evaluate(LIST) == ['Punchy (4x5) (2).jpg', 'Punchy (4x5).jpg'], pg.evaluate(LIST))
    pg.check('#rPreset'); st = save(); print('status with preset:', st)
    check('preset saved beside the card', 'Punchy.xmp' in pg.evaluate(LIST) and 'and Punchy.xmp in Cards' in st, (pg.evaluate(LIST), st))
    # remembered across reloads
    pg.evaluate("document.getElementById('recipeDlg').close()"); pg.evaluate("document.getElementById('pmCard').click()"); pg.wait_for_timeout(600); pg.fill('#rTitle', 'Punchy')
    pg.screenshot(path='/home/claude/cardfolder.png')
    check('folder remembered when the window reopens', pg.inner_text('#rDest') == 'Cards')
    pg.click('#rDestReset'); pg.wait_for_timeout(300)
    check('Use Downloads switches back', pg.inner_text('#rDest') == 'Your Downloads folder' and not pg.is_visible('#rDestReset'))
    pg.uncheck('#rPreset'); st = save(); pg.wait_for_timeout(500)
    check('back to downloading', len(dls) == 1 and dls[0].suggested_filename == 'Punchy (4x5).jpg', [d.suggested_filename for d in dls])
    check('no page errors', not errs, errs)
    ctx.close()
    # where folders can't be chosen (Firefox, Safari): the row is hidden and cards download
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000}, accept_downloads=True); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.route(lambda u: not u.startswith('http://127.0.0.1'), route)
    pg.add_init_script("delete window.showDirectoryPicker; localStorage.setItem('chimp-settings', JSON.stringify({ guide: false, tipShown: true, sortAsk: false, seenVersion: '0.9.73 beta' }))")
    pg.goto('http://127.0.0.1:8794/index.html'); pg.wait_for_timeout(900)
    pg.set_input_files('#fileInput', ['/tmp/lrtest/punchy-wide.jpg']); pg.wait_for_timeout(2500)
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    pg.wait_for_function("!document.getElementById('pmCard').disabled", timeout=10000)
    pg.evaluate("document.getElementById('pmCard').click()"); pg.wait_for_timeout(800)
    check('no folder choice where the browser can\u2019t do it', not pg.is_visible('#rDestRow') and not pg.is_visible('#rDestL'))
    check('no page errors (no folders)', not errs, errs)
    b.close()
srv.shutdown()
print(f'{sum(results)}/{len(results)} passed')
sys.exit(0 if all(results) else 1)
