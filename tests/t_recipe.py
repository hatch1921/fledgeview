from playwright.sync_api import sync_playwright
import sys
theme = sys.argv[1] if len(sys.argv) > 1 else 'light'
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    ctx = b.new_context(viewport={'width': 1920, 'height': 1080}, color_scheme='dark', accept_downloads=True); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(900)
    pg.evaluate("(() => { localStorage.clear(); localStorage.setItem('chimp-settings', JSON.stringify({ tipShown: true, sortAsk: false })); })()"); pg.reload(); pg.wait_for_timeout(1200)
    pg.evaluate("(() => { document.querySelectorAll('dialog[open]').forEach(d => d.close()); window.showSaveFilePicker = undefined; })()")
    pg.set_input_files('#fileInput', ['/tmp/lrtest/retro-22322.jpg']); pg.wait_for_timeout(2500)
    pg.evaluate("(() => { const b = document.getElementById('infoToggle'); if (b.getAttribute('aria-expanded') !== 'true') b.click(); })()"); pg.wait_for_timeout(1500)
    pg.click('#rows .lrbar button:has-text("Make recipe card")'); pg.wait_for_timeout(800)
    pg.fill('#rTitle', 'Retro #22322'); pg.fill('#rBy', 'Frank Hatcher \u00b7 frankhatcher.com'); pg.fill('#rOther', 'Topaz Photo AI: denoise, low')
    pg.select_option('#rTheme', theme); pg.wait_for_timeout(1500)
    downloads = []
    pg.on('download', lambda d: downloads.append(d))
    pg.click('#rSave'); pg.wait_for_timeout(4000)
    for d in downloads: d.save_as('/tmp/' + d.suggested_filename.replace(' ', '_').replace('#', ''))
    print('saved:', [d.suggested_filename for d in downloads], '|', pg.evaluate("document.getElementById('rStatus').textContent"))
    print('errors:', errs)
    b.close()
