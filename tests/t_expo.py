from playwright.sync_api import sync_playwright
import glob
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    pg = b.new_page(viewport={'width': 1920, 'height': 1080}, color_scheme='dark'); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(900)
    pg.evaluate("(() => { localStorage.clear(); localStorage.setItem('chimp-settings', JSON.stringify({ tipShown: true, sortAsk: false })); })()"); pg.reload(); pg.wait_for_timeout(900)
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    pg.set_input_files('#fileInput', sorted(glob.glob('/tmp/expotest/*.jpg'))); pg.wait_for_timeout(2500)
    pg.evaluate("(() => { const s = document.getElementById('filterSel'); s.value = 'over'; s.dispatchEvent(new Event('change')); })()"); pg.wait_for_timeout(3500)
    names = lambda: pg.evaluate("[...document.querySelectorAll('#strip .th')].map(t => t.getAttribute('aria-label'))")
    print('filter Possibly overexposed  ->', names())
    pg.evaluate("(() => { const s = document.getElementById('filterSel'); s.value = 'under'; s.dispatchEvent(new Event('change')); })()"); pg.wait_for_timeout(1200); print('filter Possibly underexposed ->', names())
    pg.evaluate("(() => { const s = document.getElementById('filterSel'); s.value = 'all'; s.dispatchEvent(new Event('change')); })()"); pg.wait_for_timeout(1200)
    print('thumbnail badges:', pg.evaluate("[...document.querySelectorAll('#strip .th')].map(t => t.getAttribute('aria-label') + ': ' + ((t.querySelector('.xp') || {}).textContent || 'none'))"))
    pg.evaluate("(() => { const b = document.getElementById('infoToggle'); if (b.getAttribute('aria-expanded') !== 'true') b.click(); })()")
    for n in ['2-overexposed.jpg', '4-lit-subject-on-black.jpg']:
        pg.click(f'#strip [aria-label="{n}"]'); pg.wait_for_timeout(900)
        print(f'Photo info for {n}:', pg.evaluate("[...document.querySelectorAll('#rows tr')].map(r => r.innerText.replace(/\\s+/g, ' ')).find(t => /Exposure check/.test(t))"))
    print('measurements:', pg.evaluate("JSON.parse(localStorage.getItem('chimp-expo') || '{}')"))
    print('errors:', errs)
    b.close()
