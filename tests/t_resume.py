# Needs: the built single-file copy served at http://127.0.0.1:8792/new.html and 12 JPEGs /tmp/rs/DSC001-012.JPG (any small JPEGs).
"""0.9.77: Start where I left off (desktop program). A stand-in bridge with real folder handles (the browser's private file system)."""
import sys, glob, base64, json
from playwright.sync_api import sync_playwright
fails = []
def check(ok, what): print(('PASS ' if ok else 'FAIL ') + what); (fails.append(what) if not ok else None)
FAKE = """
window.FV_DESKTOP = {
  features: {}, focus: () => Promise.resolve(null),
  resumeOn: () => localStorage.getItem('fake-resume') !== 'off',
  setResume: on => localStorage.setItem('fake-resume', on ? 'on' : 'off'),
  remember: st => { const s = JSON.parse(localStorage.getItem('fake-session') || '{}'); Object.assign(s, st); localStorage.setItem('fake-session', JSON.stringify(s)); window.__remembered = (window.__remembered || 0) + 1; },
  resume: async () => { window.__resumeCalled = true; const s = JSON.parse(localStorage.getItem('fake-session') || 'null');
    if (localStorage.getItem('fake-resume') === 'off' || !s || !s.path) return null;
    const root = await navigator.storage.getDirectory(); const h = await root.getDirectoryHandle(s.path); const out = { handle: h };
    for (const k in s) if (k !== 'path') out[k] = s[k]; return out; },
};
window.showDirectoryPicker = async () => { const root = await navigator.storage.getDirectory(); localStorage.setItem('fake-session', JSON.stringify({ path: 'shoot', file: null })); return root.getDirectoryHandle('shoot'); };
"""
files = {n.split('/')[-1]: base64.b64encode(open(n, 'rb').read()).decode() for n in sorted(glob.glob('/tmp/rs/DSC*.JPG'))}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1243/chrome-linux64/chrome')
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000}, color_scheme='dark')
    ctx.add_init_script(FAKE)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://127.0.0.1:8792/new.html'); pg.wait_for_timeout(700)
    # the test folder: 9 photos in shoot/, 3 in shoot/sub/
    pg.evaluate("""async files => { const root = await navigator.storage.getDirectory(); try { await root.removeEntry('shoot', { recursive: true }); } catch {}
      const d = await root.getDirectoryHandle('shoot', { create: true }), sub = await d.getDirectoryHandle('sub', { create: true });
      let i = 0; for (const [n, b64] of Object.entries(files)) { const t = i++ < 9 ? d : sub; const w = await (await t.getFileHandle(n, { create: true })).createWritable();
        await w.write(Uint8Array.from(atob(b64), c => c.charCodeAt(0))); await w.close(); }
      localStorage.clear(); localStorage.setItem('chimp-settings', JSON.stringify({ tipShown: true, sortAsk: true })); }""", files)
    pg.reload(); pg.wait_for_timeout(1200)
    check(pg.evaluate("window.__resumeCalled === true"), 'session 1: the app asks the program for the last folder at launch')
    check(pg.evaluate("document.querySelectorAll('#strip .th').length") == 0, 'session 1: nothing to resume, starts empty')
    check(pg.evaluate("!document.getElementById('resumeBtn').hidden && document.getElementById('resumeBtn').getAttribute('aria-pressed') === 'true'"), 'View menu shows Start where I left off, on')
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    pg.click('#openFolder'); pg.wait_for_timeout(1500)
    check(pg.evaluate("document.getElementById('scopeDlg').open"), 'first open asks about subfolders')
    pg.click('#scopeDlg [data-scope="top"]'); pg.wait_for_timeout(1500)
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")   # the "how to sort?" question on a first open
    n1 = pg.evaluate("document.querySelectorAll('#strip .th').length")
    check(n1 == 9, f'this folder only: {n1} photos')
    # picks on DSC002, DSC005, DSC007; filter Picks; go to DSC005; 4-up on
    for name in ['DSC002.JPG', 'DSC005.JPG', 'DSC007.JPG']:
        pg.click(f'#strip [aria-label="{name}"]'); pg.wait_for_timeout(300); pg.keyboard.press('p'); pg.wait_for_timeout(250)
    pg.evaluate("(() => { const s = document.getElementById('filterSel'); s.value = 'picks'; s.dispatchEvent(new Event('change')); })()"); pg.wait_for_timeout(500)
    shown = pg.evaluate("document.querySelectorAll('#strip .th').length")
    check(shown == 3, f'Picks filter shows {shown}')
    pg.click('#strip [aria-label="DSC005.JPG"]'); pg.wait_for_timeout(400)
    pg.click('#tQuad'); pg.wait_for_timeout(2200)
    sess = json.loads(pg.evaluate("localStorage.getItem('fake-session')"))
    print('   remembered:', {k: v for k, v in sess.items()})
    check(sess.get('name') == 'DSC005.JPG' and sess.get('filter') == 'picks' and sess.get('quad') is True and sess.get('scope') == 'top' and sess.get('path') == 'shoot', 'the program is told photo, filter, 4-up and subfolder choice')
    # relaunch
    pg.reload(); pg.wait_for_timeout(3000)
    dlgs = pg.evaluate("[...document.querySelectorAll('dialog[open]')].map(d => d.id)")
    check(not any(d in ('scopeDlg', 'sortDlg') for d in dlgs), f'relaunch: no subfolder or sort question ({dlgs})')
    check(pg.evaluate("document.getElementById('oName').textContent").startswith('DSC005'), 'relaunch: back on DSC005: ' + pg.evaluate("document.getElementById('oName').textContent"))
    check(pg.evaluate("document.getElementById('filterSel').value") == 'picks' and pg.evaluate("document.querySelectorAll('#strip .th').length") == 3, 'relaunch: Picks filter back, 3 shown')
    check(pg.evaluate("document.getElementById('tQuad').getAttribute('aria-pressed')") == 'true', 'relaunch: 4-up back on')
    check('Back where you left off: DSC005.JPG' in pg.evaluate("document.body.innerText"), 'relaunch: says Back where you left off')
    # a pick removed outside: DSC005 un-picked, so the Picks filter would hide it -> All, still on DSC005
    pg.evaluate("""(() => { const c = JSON.parse(localStorage.getItem('chimp-cull')); for (const k in c) if (k.startsWith('DSC005')) c[k].f = 0; localStorage.setItem('chimp-cull', JSON.stringify(c)); })()""")
    pg.evaluate("localStorage.setItem('fake-session', JSON.stringify({ ...JSON.parse(localStorage.getItem('fake-session')), quad: false }))")
    pg.reload(); pg.wait_for_timeout(3000)
    check(pg.evaluate("document.getElementById('oName').textContent").startswith('DSC005') and pg.evaluate("document.getElementById('filterSel').value") == 'all', 'photo no longer a pick: shows all, still on DSC005')
    # Photo view comes back
    pg.keyboard.press('v'); pg.wait_for_timeout(2200)
    check(json.loads(pg.evaluate("localStorage.getItem('fake-session')")).get('pview') is True, 'Photo view is remembered')
    pg.reload(); pg.wait_for_timeout(3200)
    check(pg.evaluate("document.body.classList.contains('pview')") and pg.evaluate("document.getElementById('oName').textContent").startswith('DSC005'), 'relaunch: Photo view back')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(500)
    # a new folder chosen with Open folder starts fresh (the program clears the place); here: first photo, all
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    # turned off in the View menu: next launch starts empty
    pg.evaluate("document.getElementById('resumeBtn').click()"); pg.wait_for_timeout(300)
    check(pg.evaluate("document.getElementById('resumeBtn').getAttribute('aria-pressed')") == 'false', 'View menu turns it off')
    pg.reload(); pg.wait_for_timeout(2500)
    check(pg.evaluate("document.querySelectorAll('#strip .th').length") == 0, 'off: next launch starts empty')
    check(not errs, 'no page errors ' + str(errs[:3]))
    ctx.close()
    # website: no program, no menu item, Open folder still works the old way
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000})
    ctx.add_init_script("window.showDirectoryPicker = async () => (await navigator.storage.getDirectory()).getDirectoryHandle('shoot');")
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://127.0.0.1:8792/new.html'); pg.wait_for_timeout(900)
    pg.evaluate("""async files => { const root = await navigator.storage.getDirectory();
      const d = await root.getDirectoryHandle('shoot', { create: true }), sub = await d.getDirectoryHandle('sub', { create: true });
      let i = 0; for (const [n, b64] of Object.entries(files)) { const t = i++ < 9 ? d : sub; const w = await (await t.getFileHandle(n, { create: true })).createWritable();
        await w.write(Uint8Array.from(atob(b64), c => c.charCodeAt(0))); await w.close(); } }""", files)
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    check(pg.evaluate("document.getElementById('resumeBtn').hidden"), 'website: no Start where I left off item')
    pg.click('#openFolder'); pg.wait_for_timeout(1500); pg.click('#scopeDlg [data-scope="all"]'); pg.wait_for_timeout(1500)
    check(pg.evaluate("document.querySelectorAll('#strip .th').length") == 12 and 'Opened 12 photos with folder access' in pg.evaluate("document.body.innerText"), 'website: Open folder opens all 12 as before')
    check(not errs, 'website: no page errors ' + str(errs[:3]))
    b.close()
print('\n%d failures' % len(fails)); sys.exit(1 if fails else 0)
