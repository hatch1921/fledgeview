from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    ctx = b.new_context(viewport={'width': 1920, 'height': 1080}, color_scheme='dark', accept_downloads=True); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(900)
    pg.evaluate("(() => { localStorage.clear(); localStorage.setItem('chimp-settings', JSON.stringify({ tipShown: true, sortAsk: false })); })()"); pg.reload(); pg.wait_for_timeout(900)
    pg.evaluate("(() => { document.querySelectorAll('dialog[open]').forEach(d => d.close()); window.showSaveFilePicker = undefined; })()")
    pg.set_input_files('#fileInput', ['/tmp/lrtest/lightroom-edited.jpg', '/tmp/lrtest/lightroom-defaults.jpg']); pg.wait_for_timeout(2500)
    pg.evaluate("(() => { const b = document.getElementById('infoToggle'); if (b && b.getAttribute('aria-expanded') !== 'true') b.click(); })()")
    for n in ['lightroom-edited.jpg', 'lightroom-defaults.jpg']:
        pg.click(f'#strip [aria-label="{n}"]'); pg.wait_for_timeout(1500)
        txt = pg.evaluate("document.getElementById('rows').innerText")
        i = txt.find('Lightroom'); print(f'== {n}\n' + (txt[i:i + 900] if i >= 0 else 'no Lightroom section'))
        print('   preset button:', pg.evaluate("!!document.querySelector('#rows .lrbar button')"))
    pg.click('#strip [aria-label="lightroom-edited.jpg"]'); pg.wait_for_timeout(1200)
    with pg.expect_download() as d: pg.click('#rows .lrbar button')
    d.value.save_as('/tmp/lr_preset.xmp'); print('saved as:', d.value.suggested_filename, '| toast:', pg.evaluate("document.getElementById('toast').textContent"))
    print('errors:', errs)
    b.close()
