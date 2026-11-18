# Change list item 12: Frame's Save to (a chosen folder, id 'chimp-frame', never replacing a file) and clear download messages.
import sys, os, shutil, threading, http.server, functools
from playwright.sync_api import sync_playwright
MASTER = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/kit/fledgeview-dev-kit/fledgeview.html'
L = '/home/claude/libs/'
LIBS = {'exifr@7.1.3': L + 'exifr-7.1.3/dist/full.umd.js', 'jszip/3.10.1': L + 'jszip-3.10.1/dist/jszip.min.js',
        'pako@1.0.11': L + 'pako-1.0.11/dist/pako_inflate.min.js', 'utif2@4.1.0': L + 'utif2-4.1.0/UTIF.js'}
SERVE = '/home/claude/fsserve'
shutil.rmtree(SERVE, ignore_errors=True); os.makedirs(SERVE); shutil.copy(MASTER, SERVE + '/index.html')
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8796), functools.partial(http.server.SimpleHTTPRequestHandler, directory=SERVE))
threading.Thread(target=srv.serve_forever, daemon=True).start()
def route(r):
    for k, v in LIBS.items():
        if k in r.request.url: return r.fulfill(path=v, content_type='application/javascript')
    return r.abort()
HANDLES = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 't_cardfolder.py')).read().split('HANDLES = """', 1)[1].split('"""', 1)[0]
results = []
def check(name, ok, extra=''):
    results.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + (f'  ({extra})' if extra and not ok else ''))
LIST = "async () => { const d = await (await navigator.storage.getDirectory()).getDirectoryHandle('Prints'); const o = []; for await (const [n] of d.entries()) o.push(n); return o.sort(); }"
with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-proxy-server'])
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000}, accept_downloads=True); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.route(lambda u: not u.startswith('http://127.0.0.1'), route)
    pg.add_init_script(HANDLES)
    pg.add_init_script("localStorage.setItem('chimp-settings', JSON.stringify({ guide: false, tipShown: true, sortAsk: false, seenVersion: '0.9.73 beta' }))")
    pg.goto('http://127.0.0.1:8796/index.html'); pg.wait_for_timeout(900)
    pg.evaluate("""async () => { const r = await navigator.storage.getDirectory(); for await (const [n] of r.entries()) await r.removeEntry(n, { recursive: true });
      const d = await r.getDirectoryHandle('Prints', { create: true }); window.__pickId = null; window.showDirectoryPicker = async (o) => { window.__pickId = o && o.id; return d; }; }""")
    pg.set_input_files('#fileInput', ['/tmp/lrtest/punchy-wide.jpg']); pg.wait_for_timeout(2500)
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    pg.evaluate("document.getElementById('tFrame').click()"); pg.wait_for_timeout(1200)
    check('Save to shows, starting at Downloads', pg.is_visible('#fDest') and pg.input_value('#fDest') == 'dl')
    toast = lambda: pg.inner_text('#toast')
    dls = []; pg.on('download', lambda d: dls.append(d))
    pg.click('#fSave'); pg.wait_for_timeout(2500)
    t = toast(); print('download toast:', t)
    check('download says where it went', len(dls) == 1 and t.startswith('Downloaded punchy-wide_framed_') and 'check your Downloads folder' in t, (len(dls), t))
    pg.select_option('#fDest', 'pick'); pg.wait_for_timeout(600)
    check('folder picker uses its own id chimp-frame', pg.evaluate('window.__pickId') == 'chimp-frame', pg.evaluate('window.__pickId'))
    check('chosen folder shows in Save to', pg.input_value('#fDest') == 'dir' and pg.evaluate("document.getElementById('fDest').selectedOptions[0].textContent") == 'Prints')
    pg.click('#fSave'); pg.wait_for_timeout(2500); t = toast(); print('folder toast:', t)
    check('saved into the folder, named in the message', len(dls) == 1 and t.startswith('Saved punchy-wide_framed_') and t.endswith('to Prints.'), (len(dls), t))
    pg.wait_for_timeout(3500); pg.click('#fSave'); pg.wait_for_timeout(2500)
    lst = pg.evaluate(LIST); print('Prints:', lst)
    check('a second save adds (2), keeps the first', len(lst) == 2 and any('(2).jpg' in n for n in lst), lst)
    pg.select_option('#fDest', 'dl'); pg.wait_for_timeout(300); pg.wait_for_timeout(3500)
    pg.click('#fSave'); pg.wait_for_timeout(2500)
    check('switching back to Downloads downloads again', len(dls) == 2 and toast().startswith('Downloaded'), (len(dls), toast()))
    check('no page errors', not errs, errs)
    ctx.close()
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000}); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.route(lambda u: not u.startswith('http://127.0.0.1'), route)
    pg.add_init_script("delete window.showDirectoryPicker; localStorage.setItem('chimp-settings', JSON.stringify({ guide: false, tipShown: true, sortAsk: false, seenVersion: '0.9.73 beta' }))")
    pg.goto('http://127.0.0.1:8796/index.html'); pg.wait_for_timeout(900)
    pg.set_input_files('#fileInput', ['/tmp/lrtest/punchy-wide.jpg']); pg.wait_for_timeout(2500)
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())"); pg.evaluate("document.getElementById('tFrame').click()"); pg.wait_for_timeout(1000)
    check('no Save to where the browser has no folder access', not pg.is_visible('#fDestL'))
    check('no page errors (no folders)', not errs, errs)
    b.close()
srv.shutdown()
print(f'{sum(results)}/{len(results)} passed')
sys.exit(0 if all(results) else 1)
