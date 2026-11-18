# 0.9.71: recipe card shapes for social media. For a wide and a tall Lightroom-edited JPEG (fixture: /tmp/lrtest, made by
# the snippet in tests/README.md), checks each shape's exact size, that the photo isn't cropped, that the settings fit,
# the file names, that Fit still makes the original layout, and saves the cards to /home/claude/cards for a visual check.
import sys, os, shutil, threading, http.server, functools
from playwright.sync_api import sync_playwright
from PIL import Image

MASTER = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/kit/fledgeview-dev-kit/fledgeview.html'
L = '/home/claude/libs/'
LIBS = {'exifr@7.1.3': L + 'exifr-7.1.3/dist/full.umd.js', 'jszip/3.10.1': L + 'jszip-3.10.1/dist/jszip.min.js',
        'pako@1.0.11': L + 'pako-1.0.11/dist/pako_inflate.min.js', 'utif2@4.1.0': L + 'utif2-4.1.0/UTIF.js'}
FONTS = '/home/claude/kit/fledgeview-dev-kit/site/assets'
SERVE = '/home/claude/cardserve'; OUT = '/home/claude/cards'
shutil.rmtree(SERVE, ignore_errors=True); os.makedirs(SERVE); shutil.copy(MASTER, SERVE + '/index.html')
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
shutil.copytree(FONTS + '/fonts', SERVE + '/fonts')   # the card's Barlow Condensed, served locally instead of Google Fonts
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8793), functools.partial(http.server.SimpleHTTPRequestHandler, directory=SERVE))
threading.Thread(target=srv.serve_forever, daemon=True).start()

def route(r):
    u = r.request.url
    for k, v in LIBS.items():
        if k in u: return r.fulfill(path=v, content_type='application/javascript')
    if 'fonts.googleapis.com' in u:
        css = open(SERVE + '/fonts/fonts.css').read().replace('url(', 'url(http://127.0.0.1:8793/fonts/').replace('url(http://127.0.0.1:8793/fonts/"', 'url("http://127.0.0.1:8793/fonts/').replace("url(http://127.0.0.1:8793/fonts/'", "url('http://127.0.0.1:8793/fonts/")
        return r.fulfill(body=css, content_type='text/css')
    return r.abort()

results = []
def check(name, ok, extra=''):
    results.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + (f'  ({extra})' if extra and not ok else ''))

SIZES = {'p45': (1080, 1350), 'sq': (1080, 1080), 'story': (1080, 1920)}
SUFFIX = {'fit': '', 'p45': ' (4x5)', 'sq': ' (square)', 'story': ' (story)'}

with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-proxy-server'])
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000}, accept_downloads=True); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route(lambda u: not u.startswith('http://127.0.0.1'), route)
    pg.add_init_script("localStorage.setItem('chimp-settings', JSON.stringify({ guide: false, tipShown: true, sortAsk: false, seenVersion: '0.9.73 beta' }))")
    pg.goto('http://127.0.0.1:8793/index.html'); pg.wait_for_timeout(900)
    pg.evaluate("window.showSaveFilePicker = undefined; document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    for photo in ['punchy-wide.jpg', 'punchy-tall.jpg']:
        pg.set_input_files('#fileInput', ['/tmp/lrtest/' + photo]); pg.wait_for_timeout(2500)
        pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        pg.wait_for_function("!document.getElementById('pmCard').disabled", timeout=10000)
        pg.evaluate("document.getElementById('pmCard').click()"); pg.wait_for_timeout(800)
        pg.fill('#rTitle', 'B&W - Punchy'); pg.fill('#rBy', 'www.fledgeview.com')
        pg.select_option('#rTheme', 'dark')
        for shape in ['fit', 'p45', 'sq', 'story']:
            pg.select_option('#rShape', shape); pg.wait_for_timeout(900)
            dl = []
            pg.on('download', lambda d: dl.append(d))
            pg.uncheck('#rPreset') if shape != 'fit' else pg.check('#rPreset')
            pg.evaluate("rStatus.textContent = ''")
            pg.click('#rSave'); pg.wait_for_function("(rStatus.textContent.startsWith('Saved') || rStatus.textContent.startsWith('Downloaded'))", timeout=30000); pg.wait_for_timeout(500)
            dl = [d for d in dl if d.suggested_filename.endswith('.jpg')]
            if not dl: check(f'[{photo} {shape}] saved', False, 'no download'); continue
            d = dl[0]; name = d.suggested_filename; path = f'{OUT}/{photo[:-4]}-{shape}.jpg'; d.save_as(path)
            check(f'[{photo} {shape}] file name', name == 'B&W - Punchy' + SUFFIX[shape] + '.jpg', name)
            im = Image.open(path); w, h = im.size
            if shape == 'fit':
                check(f'[{photo} fit] original layout unchanged', (w > h) if 'wide' in photo else (h > w), (w, h))
            else:
                check(f'[{photo} {shape}] exact size {SIZES[shape]}', (w, h) == SIZES[shape], (w, h))
                # photo not cropped: its area keeps the photo's 3:2 or 2:3 shape (bright rows/cols of the gradient sky region)
                g = im.convert('L'); px = g.load()
                photo_h = next((y for y in range(h) if max(px[x, y] for x in range(0, w, 4)) < 45), 0)   # first all-panel row below the photo
                cols = [x for x in range(w) if px[x, 5] > 60]; photo_w = (max(cols) - min(cols) + 1) if cols else 0
                ratio = photo_w / photo_h if photo_h else 0
                want = 1.5 if 'wide' in photo else 2 / 3
                check(f'[{photo} {shape}] photo shown whole (ratio {ratio:.2f} vs {want:.2f})', abs(ratio - want) < 0.06, (photo_w, photo_h))
        st = pg.evaluate("document.getElementById('rStatus').textContent")
        check(f'[{photo}] status names the social file', '(story).jpg' in st, st)
        pg.evaluate("document.getElementById('recipeDlg').close()")
    # remembered
    pg.evaluate("document.getElementById('pmCard').click()"); pg.wait_for_timeout(600)
    check('shape choice is remembered', pg.input_value('#rShape') == 'story', pg.input_value('#rShape'))
    check('no page errors', not errs, errs)
    b.close()
srv.shutdown()
print(f'{sum(results)}/{len(results)} passed')
sys.exit(0 if all(results) else 1)
