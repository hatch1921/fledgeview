from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-proxy-server'])
    pg = b.new_page(viewport={'width': 1920, 'height': 1080}, color_scheme='dark'); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://127.0.0.1:8790/app/'); pg.wait_for_timeout(900)
    pg.evaluate("(() => { document.querySelectorAll('dialog[open]').forEach(d => d.close()); window.showDirectoryPicker = undefined; })()")
    pg.set_input_files('#dirInput', '/tmp/stripped2'); pg.wait_for_timeout(3000)
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    if pg.evaluate("document.querySelector('#infoPanel, .sidepanel, #rows') && document.getElementById('rows').offsetParent === null"):
        pg.evaluate("(() => { const b = [...document.querySelectorAll('button, summary')].find(x => /Photo info/.test(x.textContent)); b && b.click(); })()")
    for name in ['doe-with-exif.jpg', 'doe-no-exif.jpg', 'small-web-copy.jpg', 'A1200001.ARW']:
        pg.click(f'#strip [aria-label="{name}"]'); pg.wait_for_timeout(1500)
        print('==', name)
        print('  on-screen info:', pg.evaluate("document.getElementById('osd').innerText.replace(/\\s+/g, ' ')")[:120])
        print('  Photo info rows:', pg.evaluate("[...document.querySelectorAll('#rows tr, #rows .row')].map(r => r.innerText.replace(/\\s+/g, ' ')).filter(t => /size|dimension|pixel|MP|file|preview/i.test(t))"))
    print('errors:', errs)
    b.close()
