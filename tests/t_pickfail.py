# 0.9.68: the "No folder was opened" window when Chrome cancels after a folder is chosen.
# Checks: a slow AbortError (Chrome refusing) shows the window with browser-aware names; a quick cancel shows nothing;
# Open read-only instead triggers the fallback folder input; What's new lists 0.9.68.
import sys
from playwright.sync_api import sync_playwright

MASTER = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/kit/fledgeview-dev-kit/fledgeview.html'
L = '/home/claude/libs/'
LIBS = {'exifr@7.1.3': L + 'exifr-7.1.3/dist/full.umd.js', 'jszip/3.10.1': L + 'jszip-3.10.1/dist/jszip.min.js',
        'pako@1.0.11': L + 'pako-1.0.11/dist/pako_inflate.min.js', 'utif2@4.1.0': L + 'utif2-4.1.0/UTIF.js'}
EDGE_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
           'Chrome/157.0.0.0 Safari/537.36 Edg/157.0.0.0')

def route(r):
    for k, v in LIBS.items():
        if k in r.request.url:
            return r.fulfill(path=v, content_type='application/javascript')
    return r.abort()

PICKER = """(delay) => { window.__inputClicks = 0;
  window.showDirectoryPicker = () => new Promise((_, rej) => setTimeout(() =>
    rej(new DOMException('The user aborted a request.', 'AbortError')), delay));
  const inp = document.getElementById('dirInput'); inp.click = () => { window.__inputClicks++; }; }"""

results = []
def check(name, ok):
    results.append(ok); print(('PASS ' if ok else 'FAIL ') + name)

with sync_playwright() as p:
    b = p.chromium.launch(ignore_default_args=['--hide-scrollbars'])
    for ua, bname, alt in [(None, 'Chrome', 'Microsoft Edge'), (EDGE_UA, 'Edge', 'Google Chrome')]:
        ctx = b.new_context(viewport={'width': 1600, 'height': 900}, user_agent=ua) if ua else b.new_context(viewport={'width': 1600, 'height': 900})
        pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.route(lambda u: u.startswith('http'), route)
        pg.add_init_script("localStorage.setItem('chimp-settings', JSON.stringify({guide:false, seenVersion: '0.9.73 beta'}))")
        pg.goto('file://' + MASTER); pg.wait_for_timeout(800)
        # quick cancel: no window
        pg.evaluate(PICKER, 200); pg.click('#openFolder'); pg.wait_for_timeout(700)
        check(f'[{bname}] quick cancel shows no window', not pg.evaluate("document.getElementById('pickFailDlg').open"))
        # slow refusal: window with browser-aware text
        pg.evaluate(PICKER, 2000); pg.click('#openFolder'); pg.wait_for_timeout(2600)
        is_open = pg.evaluate("document.getElementById('pickFailDlg').open")
        check(f'[{bname}] slow refusal shows the window', is_open)
        txt = pg.inner_text('#pickFailDlg')
        check(f'[{bname}] names {bname} and suggests {alt}', f'{bname} didn\u2019t hand it over' in txt and f'try {alt}' in txt)
        check(f'[{bname}] mentions browser update and keeps the site-settings tip', 'after a browser update' in txt and 'File editing' in txt)
        if not ua:
            pg.screenshot(path='/home/claude/pickfail.png')
        pg.click('#pickFailGo'); pg.wait_for_timeout(200)
        check(f'[{bname}] Open read-only instead closes and opens the fallback input',
              not pg.evaluate("document.getElementById('pickFailDlg').open") and pg.evaluate('window.__inputClicks') == 1)
        check(f'[{bname}] no page errors', not errs)
        ctx.close()
    # What's new
    ctx = b.new_context(); pg = ctx.new_page(); pg.route(lambda u: u.startswith('http'), route)
    pg.goto('file://' + MASTER); pg.wait_for_timeout(500)
    v = pg.evaluate("typeof RELEASES !== 'undefined' ? RELEASES[0].v : document.documentElement.innerHTML.includes(\"v: '0.9.68 beta'\")")
    check("What's new has the 0.9.68 entry", v is True or v == '0.9.68 beta')
    b.close()
print(f'{sum(results)}/{len(results)} passed')
sys.exit(0 if all(results) else 1)
