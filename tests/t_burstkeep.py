from playwright.sync_api import sync_playwright
import glob
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    pg = b.new_page(viewport={'width': 1920, 'height': 1080}, color_scheme='dark'); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(900)
    pg.evaluate("(() => { localStorage.clear(); const s = { tipShown: true, sortAsk: false }; localStorage.setItem('chimp-settings', JSON.stringify(s)); })()"); pg.reload(); pg.wait_for_timeout(900)
    pg.evaluate("(() => { document.querySelectorAll('dialog[open]').forEach(d => d.close()); window.showDirectoryPicker = undefined; })()")
    pg.set_input_files('#fileInput', sorted(glob.glob('/tmp/vid/Wildlife/2026-09-04/*.jpg'))); pg.wait_for_timeout(4000)
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    # find a burst with at least 4 frames
    info = pg.evaluate("""(() => { const th = [...document.querySelectorAll('#strip .th')]; const names = th.map(t => t.getAttribute('aria-label'));
      return names; })()""")
    flags = lambda: pg.evaluate("(() => { const c = JSON.parse(localStorage.getItem('chimp-cull') || '{}'); return c; })()")
    # open each photo's Burst line until we find one of size >= 4
    target = None
    for n in info:
        pg.click(f'#strip [aria-label="{n}"]'); pg.wait_for_timeout(250)
        bt = pg.evaluate("document.getElementById('oBurst').textContent")
        if bt and int(bt.split('/')[1]) >= 4: target = (n, bt); break
    print('burst found at:', target)
    size = int(target[1].split('/')[1])
    # the burst's frames are consecutive in the grid: pick the NEXT frame first (it should stay picked)
    i = info.index(target[0]); other = info[i + 1]
    pg.click(f'#strip [aria-label="{other}"]'); pg.wait_for_timeout(300); pg.keyboard.press('p'); pg.wait_for_timeout(400)
    pg.click(f'#strip [aria-label="{target[0]}"]'); pg.wait_for_timeout(400)
    pg.keyboard.press('Shift+P'); pg.wait_for_timeout(900)
    burst = info[i: i + size] if target[1].startswith('Burst 1/') else None
    c = flags(); key = lambda n: [k for k in c if k.split('|')[0] == n]
    get = lambda n: (c.get(key(n)[0], {}) if key(n) else {}).get('f', 0)
    names_in_burst = pg.evaluate(f"""(() => {{ const it = [...document.querySelectorAll('#strip .th')]; return null; }})()""")
    print('toast:', pg.evaluate("document.getElementById('toast').textContent"))
    print('now showing:', pg.evaluate("document.getElementById('oName') ? document.getElementById('oName').textContent : ''") or pg.evaluate("document.querySelector('.osd .fname, #oFile') && document.querySelector('.osd .fname, #oFile').textContent"))
    print('flags in the burst (1 pick, -1 reject):', {n: get(n) for n in info[max(0, i - 1): i + size + 1]})
    pg.keyboard.press('Shift+U'); pg.wait_for_timeout(600); c = flags()
    print('after Shift+U:', {n: get(n) for n in info[max(0, i - 1): i + size + 1]}, '|', pg.evaluate("document.getElementById('toast').textContent"))
    # session summary, then walk to the end of the folder
    pg.click('#cullMenuBtn') if pg.locator('#cullMenuBtn').count() else None
    pg.evaluate("document.getElementById('sessBtn').click()"); pg.wait_for_timeout(500)
    print('summary:', pg.evaluate("[...document.querySelectorAll('#sessTab tr')].map(r => r.innerText.replace(/\\s+/g, ' '))"))
    pg.evaluate("document.getElementById('sessDlg').close()")
    for _ in range(len(info)): pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(60)
    pg.wait_for_timeout(1600)
    print('at the last photo, summary opened by itself:', pg.evaluate("document.getElementById('sessDlg').open"), '| reviewed:', pg.evaluate("[...document.querySelectorAll('#sessTab tr')][0].innerText.replace(/\\s+/g, ' ')"))
    print('errors:', errs)
    b.close()
