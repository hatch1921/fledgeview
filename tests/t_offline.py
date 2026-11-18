from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx = b.new_context(viewport={'width': 1600, 'height': 900}, offline=True); pg = ctx.new_page(); errs = []; net = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('request', lambda r: net.append(r.url) if not r.url.startswith(('file:', 'data:', 'blob:')) else None)
    pg.goto('file:///tmp/usbstick/FledgeView/FledgeView.html'); pg.wait_for_timeout(1200)
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    print('version:', pg.evaluate("document.title"), '| camera-data reader built in:', pg.evaluate("typeof exifr"), '| zip library built in:', pg.evaluate("typeof JSZip"))
    print('fonts built in:', pg.evaluate("document.fonts.check('600 16px Barlow')"), '| folder access available:', pg.evaluate("typeof window.showDirectoryPicker === 'function'"))
    pg.set_input_files('#fileInput', ['/mnt/user-data/uploads/A1200001.ARW', '/tmp/vid/Wildlife/2026-09-04/A1208483.jpg']); pg.wait_for_timeout(3500)
    print('raw and JPEG shown with camera data:', pg.evaluate("document.getElementById('osd').innerText.replace(/\\s+/g, ' ').slice(0, 70)"))
    pg.click('#strip .th'); pg.keyboard.press('4'); pg.wait_for_timeout(300)
    pg.click('#editTab'); pg.wait_for_timeout(700); pg.click('#eCropBtn'); pg.wait_for_timeout(500)
    print('crop tool:', pg.evaluate("document.getElementById('eCropInfo').textContent")[:60])
    print('internet requests attempted:', net or 'none', '| errors:', errs)
    b.close()
