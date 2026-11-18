# 0.9.69: the loading card for large folders.
# Builds a folder in the origin-private file system (600 small JPEGs in lens subfolders), slows file reads so each phase
# can be watched, and checks: Finding photos (count, subfolder, Stop), Reading photo info (bar, count, %, Hide), that it
# goes away when done, that Stop opens nothing, that small folders show no card, and that Open file names it "photos".
import sys
from playwright.sync_api import sync_playwright

MASTER = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/kit/fledgeview-dev-kit/fledgeview.html'
L = '/home/claude/libs/'
LIBS = {'exifr@7.1.3': L + 'exifr-7.1.3/dist/full.umd.js', 'jszip/3.10.1': L + 'jszip-3.10.1/dist/jszip.min.js',
        'pako@1.0.11': L + 'pako-1.0.11/dist/pako_inflate.min.js', 'utif2@4.1.0': L + 'utif2-4.1.0/UTIF.js'}

def route(r):
    for k, v in LIBS.items():
        if k in r.request.url:
            return r.fulfill(path=v, content_type='application/javascript')
    return r.fulfill(body='', status=200)   # page origin requests (none expected)

SERVE = '/home/claude/lcserve'
import os, shutil, threading, http.server, functools
shutil.rmtree(SERVE, ignore_errors=True); os.makedirs(SERVE)
shutil.copy(MASTER, SERVE + '/index.html')
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8791), functools.partial(http.server.SimpleHTTPRequestHandler, directory=SERVE))
threading.Thread(target=srv.serve_forever, daemon=True).start()

BUILD = """async ([name, subs, per]) => {
  const root = await navigator.storage.getDirectory();
  try { await root.removeEntry(name, { recursive: true }); } catch {}
  const top = await root.getDirectoryHandle(name, { create: true });
  const c = document.createElement('canvas'); c.width = 64; c.height = 48;
  const g = c.getContext('2d'); g.fillStyle = '#7a8'; g.fillRect(0, 0, 64, 48);
  const blob = await new Promise(r => c.toBlob(r, 'image/jpeg', 0.8));
  let n = 0;
  for (const s of subs) {
    const d = s ? await top.getDirectoryHandle(s, { create: true }) : top;
    for (let i = 0; i < per; i++) { const f = await d.getFileHandle(`IMG_${String(++n).padStart(5, '0')}.jpg`, { create: true });
      const w = await f.createWritable(); await w.write(blob); await w.close(); }
  }
  window.__dir = top; return n; }"""

SLOW = """([readMs, metaMs]) => {
  const gf = FileSystemFileHandle.prototype.getFile;
  FileSystemFileHandle.prototype.getFile = function () { return new Promise(r => setTimeout(r, readMs)).then(() => gf.call(this)); };
  for (const k of ['parse', 'orientation']) { const f = exifr[k]; exifr[k] = (...a) => new Promise(r => setTimeout(r, metaMs)).then(() => f.apply(exifr, a)); }
  window.showDirectoryPicker = async () => window.__dir; }"""

results = []
def check(name, ok, extra=''):
    results.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + (f'  ({extra})' if extra and not ok else ''))

card = lambda pg: pg.evaluate("(() => { const c = document.getElementById('loadCard'); return { shown: !c.hidden, title: lcTitle.textContent, phase: lcPhase.textContent, detail: lcDetail.textContent, btn: lcBtn.textContent, fill: lcFill.style.width, busy: c.classList.contains('busy') }; })()")

with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-proxy-server'], ignore_default_args=['--hide-scrollbars'])
    def fresh(look='camera'):
        ctx = b.new_context(viewport={'width': 1600, 'height': 900})
        pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.route(lambda u: not u.startswith('http://127.0.0.1'), route)
        pg.add_init_script("localStorage.setItem('chimp-settings', JSON.stringify({guide:false, seenVersion: '0.9.73 beta', sortAsk:false, openScope:'all', look:'%s'}))" % look)
        pg.goto('http://127.0.0.1:8791/index.html'); pg.wait_for_timeout(700)
        return ctx, pg, errs

    # 1. full run: finding, then reading, then gone
    ctx, pg, errs = fresh()
    n = pg.evaluate(BUILD, ['Wildlife 2026', ['600mm', '200-600mm', ''], 200])
    check('built test folder', n == 600, n)
    pg.evaluate(SLOW, [120, 15])
    pg.click('#openFolder')
    pg.wait_for_timeout(1900)
    c = card(pg)
    check('finding: card shows', c['shown'], c)
    check('finding: title names the folder', c['title'] == 'Opening Wildlife 2026', c['title'])
    check('finding: running count', c['phase'].startswith('Finding photos') and 'so far' in c['phase'], c['phase'])
    check('finding: names the subfolder', c['detail'].startswith('In '), c['detail'])
    check('finding: Stop button and moving bar', c['btn'] == 'Stop' and c['busy'], c)
    pg.screenshot(path='/home/claude/lc_find.png')
    pg.wait_for_function("lcBtn.textContent === 'Hide' && !loadCard.hidden", timeout=20000); pg.wait_for_timeout(1200)
    c = card(pg)
    check('reading: card shows with Hide', c['shown'] and c['btn'] == 'Hide' and not c['busy'], c)
    check('reading: count of 600 and percent', ' of 600 ' in c['detail'] and '%' in c['detail'], c['detail'])
    check('reading: bar has width', c['fill'] not in ('', '0%'), c['fill'])
    check('reading: photos are browsable meanwhile', '600 photo' in pg.inner_text('#gridCount'))
    pg.screenshot(path='/home/claude/lc_read.png')
    pg.wait_for_function("document.getElementById('loadCard').hidden", timeout=30000)
    check('done: card goes away by itself', card(pg)['shown'] is False)
    check('no page errors (full run)', not errs, errs)
    ctx.close()

    # 2. Stop during finding opens nothing
    ctx, pg, errs = fresh()
    pg.evaluate(BUILD, ['Whole drive', ['a', 'b', 'c'], 200]); pg.evaluate(SLOW, [150, 0])
    pg.click('#openFolder'); pg.wait_for_timeout(1900)
    check('stop: card is up first', card(pg)['shown'])
    pg.click('#lcBtn'); pg.wait_for_timeout(1500)
    check('stop: card gone, nothing opened', not card(pg)['shown'] and pg.inner_text('#gridCount') == '')
    check('stop: says so', 'Stopped. Nothing was opened from Whole drive' in pg.inner_text('#toast'), pg.inner_text('#toast'))
    check('no page errors (stop)', not errs, errs)
    ctx.close()

    # 3. small folder: no card at all
    ctx, pg, errs = fresh()
    pg.evaluate(BUILD, ['Small', ['400mm'], 40]); pg.evaluate(SLOW, [0, 0])
    pg.evaluate("window.__seen = false; new MutationObserver(() => { if (!loadCard.hidden) window.__seen = true; }).observe(loadCard, { attributes: true })")
    pg.click('#openFolder'); pg.wait_for_timeout(1500)
    check('small folder: opened without a card', '40 photo' in pg.inner_text('#gridCount') and not pg.evaluate('window.__seen'))
    ctx.close()

    # 4. Hide keeps reading; Clean look renders
    ctx, pg, errs = fresh('clean')
    pg.evaluate(BUILD, ['Clean test', ['600mm'], 600]); pg.evaluate(SLOW, [0, 20])
    pg.click('#openFolder'); pg.wait_for_function("lcBtn.textContent === 'Hide' && !loadCard.hidden", timeout=20000); pg.wait_for_timeout(600)
    pg.screenshot(path='/home/claude/lc_clean.png')
    pg.click('#lcBtn'); pg.wait_for_timeout(800)
    check('hide: card hidden while reading continues', not card(pg)['shown'] and pg.inner_text('#status').startswith('Reading photo info'))
    pg.wait_for_timeout(1500)
    check('hide: stays hidden', not card(pg)['shown'])
    check('no page errors (clean, hide)', not errs, errs)
    ctx.close()

    # 5. Open file with many photos after a folder: titled "photos", not the folder's name
    ctx, pg, errs = fresh()
    pg.evaluate(BUILD, ['First', ['x'], 30]); pg.evaluate(SLOW, [0, 15])
    pg.click('#openFolder'); pg.wait_for_timeout(1200)
    import tempfile
    tmp = tempfile.mkdtemp(); src = '/home/claude/lc_tiny.jpg'
    pg.evaluate("""async () => { const c = document.createElement('canvas'); c.width = 32; c.height = 24; c.getContext('2d').fillRect(0, 0, 32, 24);
      return await new Promise(r => c.toBlob(b => { const fr = new FileReader(); fr.onload = () => r(fr.result); fr.readAsDataURL(b); }, 'image/jpeg')); }""")
    data = pg.evaluate("""async () => { const c = document.createElement('canvas'); c.width = 32; c.height = 24; c.getContext('2d').fillRect(0, 0, 32, 24);
      return await new Promise(r => c.toBlob(b => { const fr = new FileReader(); fr.onload = () => r(fr.result.split(',')[1]); fr.readAsDataURL(b); }, 'image/jpeg')); }""")
    import base64
    raw = base64.b64decode(data); paths = []
    for i in range(520):
        fp = f'{tmp}/F{i:04d}.jpg'; open(fp, 'wb').write(raw + bytes([i % 256])); paths.append(fp)
    pg.set_input_files('#fileInput', paths)
    pg.wait_for_function("lcBtn.textContent === 'Hide' && !loadCard.hidden", timeout=20000)
    check('open file: titled Opening photos', card(pg)['title'] == 'Opening photos', card(pg)['title'])
    check('no page errors (open file)', not errs, errs)
    ctx.close()
    b.close()
srv.shutdown()
print(f'{sum(results)}/{len(results)} passed')
sys.exit(0 if all(results) else 1)
