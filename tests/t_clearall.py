from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    def run(case):
        pg = b.new_page(viewport={'width': 1920, 'height': 1080}, color_scheme='dark'); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(900)
        pg.evaluate("(() => { localStorage.clear(); document.querySelectorAll('dialog[open]').forEach(d => d.close()); })()"); pg.reload(); pg.wait_for_timeout(900)
        pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        pg.set_input_files('#fileInput', ['/tmp/vid/Wildlife/2026-09-04/A1208483.jpg', '/tmp/tifftest/8bit-lzw-predictor.tif']); pg.wait_for_timeout(2500)
        pg.click('#strip [aria-label="A1208483.jpg"]'); pg.wait_for_timeout(1000)
        setv = lambda k, v: pg.evaluate(f"(() => {{ const i = document.getElementById('e_{k}'); i.value = {v}; i.dispatchEvent(new Event('input')); }})()")
        if case == 'Adjust open, with edits': pg.click('#editTab'); pg.wait_for_timeout(700); setv('exp', 30); pg.wait_for_timeout(400)
        elif case == 'edited photo, panel closed': pg.click('#editTab'); pg.wait_for_timeout(700); setv('exp', 30); pg.wait_for_timeout(300); pg.click('#editTab'); pg.wait_for_timeout(700)
        elif case == 'Crop panel open': pg.click('#cropTab'); pg.wait_for_timeout(800)
        elif case == 'Lens tools open': pg.click('#dofBtn'); pg.wait_for_timeout(900)
        elif case == 'Adjust open, no edits': pg.click('#editTab'); pg.wait_for_timeout(700)
        pg.click('#clearAll'); pg.wait_for_timeout(800); pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        st = pg.evaluate("""(() => { const vis = id => { const e = document.getElementById(id); return !!e && !e.hidden && getComputedStyle(e).display !== 'none'; };
          const emptyOnTop = (() => { const e = document.getElementById('empty'), r = e.getBoundingClientRect(), t = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return !!t && (t === e || e.contains(t)); })();
          return { editLayer: vis('editView'), lensLayer: vis('lensView'), panel: vis('editPanel'), startMessageVisible: emptyOnTop }; })()""")
        ok = not st['editLayer'] and not st['lensLayer'] and not st['panel'] and st['startMessageVisible']
        pg.set_input_files('#fileInput', ['/tmp/vid/Wildlife/2026-09-04/A1206951.jpg']); pg.wait_for_timeout(1500)
        again = pg.evaluate("(() => { const c = document.querySelector('#pane0 canvas.img'); return !!c && c.width > 1000 && document.getElementById('empty').hidden; })()")
        print(f'{case:28s}', 'OK ' if ok else 'BUG', '| start message shown:', st['startMessageVisible'], '| layers left:', [k for k in ('editLayer', 'lensLayer', 'panel') if st[k]] or 'none', '| new photos load after:', again, errs or '')
        pg.close()
    for c in ['no edits, nothing open', 'Adjust open, no edits', 'Adjust open, with edits', 'edited photo, panel closed', 'Crop panel open', 'Lens tools open']: run(c)
    b.close()
