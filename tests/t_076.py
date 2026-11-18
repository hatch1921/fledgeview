"""0.9.76: noise reduction removed, print sizes round down.
Runs against the built single-file copy (site/download/FledgeView.html, libraries built in).
Needs /tmp/t076/big8640.jpg (8640 x 5760) and /tmp/t076/exact6000.jpg (6000 x 4000), any JPEGs of those sizes."""
import json, sys, os
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = 'file://' + os.path.join(HERE, '..', 'site', 'download', 'FledgeView.html')
fails = []
def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what)
    if not ok: fails.append(what)
OLD = {  # edits saved by a 0.9.75 test build's Noise reduction window
    'noiseonly|1': {'exp': 0, 'nr': 60, 'nrd': 50, 'nrc': 80, 'nrt': 1, 'nrp': 100, 'bw': 0, 'crop': None, 'cropAr': 'orig'},
    'withexp|2': {'exp': 20, 'nr': 40, 'nrc': 30, 'nrt': 0, 'nrs': {'x': .1, 'y': .1, 'w': .2, 'h': .2}, 'bw': 0, 'crop': None, 'cropAr': 'orig'},
    'plain|3': {'exp': -10, 'bw': 0, 'crop': None, 'cropAr': 'orig'},
}
MASTER = open(os.path.join(HERE, '..', 'fledgeview.html'), encoding='utf-8').read()
check("const VERSION = '0.9.76 beta';" in MASTER, 'master version 0.9.76 beta')
import subprocess, re
line = next(l for l in MASTER.split('\n') if l.startswith('const printLen = '))
cases = [(5760, 300, 'in', '19'), (8640, 300, 'in', '28'), (6000, 300, 'in', '20'), (4000, 200, 'in', '20'), (5760, 200, 'in', '28'),
         (8640, 250, 'in', '34'), (8640, 300, 'cm', '73'), (6000, 300, 'cm', '50'), (590, 300, 'in', '1.9'), (600, 300, 'in', '2'),
         (300, 300, 'in', '1.0'), (5760, 150, 'in', '38'), (4000, 240, 'in', '16'), (3000, 360, 'in', '8')]
js = line + '\nconsole.log(JSON.stringify(' + json.dumps([[a, b2, u] for a, b2, u, _ in cases]) + '.map(([a, b, u]) => printLen(a, b, u))));'
got = json.loads(subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True).stdout)
for (px, ppi, u, want), g in zip(cases, got): check(g == want, f'printLen {px} px at {ppi} ppi in {u}: {g} (want {want})')
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1243/chrome-linux64/chrome')
    for desk in (False, True):
        ctx = b.new_context(viewport={'width': 1920, 'height': 1080}, color_scheme='dark', locale='en-US')
        if desk:  # a stand-in for the program's bridge, as an old program build would report it
            ctx.add_init_script("window.FV_DESKTOP = { features: { focusPoints: false, bursts: false, rawDevelop: false, rawFinish: false, noise: true }, focus: () => Promise.resolve(null) };")
        pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        tag = '[program] ' if desk else '[website] '
        pg.goto(PAGE); pg.wait_for_timeout(600)
        pg.evaluate("o => localStorage.setItem('chimp-edits', JSON.stringify(o))", OLD)
        pg.reload(); pg.wait_for_timeout(900)
        pg.evaluate("for (const d of document.querySelectorAll('dialog[open]')) d.close()")
        saved = json.loads(pg.evaluate("localStorage.getItem('chimp-edits')"))
        check('noiseonly|1' not in saved, tag + 'a photo whose only edit was noise reduction is no longer edited')
        check(saved.get('withexp|2', {}).get('exp') == 20 and not any(k in saved.get('withexp|2', {}) for k in ['nr', 'nrd', 'nrc', 'nrt', 'nrp', 'nrs']), tag + 'other edits kept, noise settings dropped')
        check(saved.get('plain|3') == OLD['plain|3'], tag + 'an edit without noise settings is untouched')
        check(pg.evaluate("!document.getElementById('eNr') && !document.getElementById('eNrWeb') && !document.getElementById('nrDlg')"), tag + 'no Noise reduction button, website line, or window')
        check('noise reduction' not in pg.evaluate("document.getElementById('editPanel') ? document.getElementById('editPanel').innerText.toLowerCase() : document.body.innerText.toLowerCase().slice(0,0)"), tag + 'Adjust panel has no noise reduction text')
        helpTxt = pg.evaluate("(() => { const c = document.body.cloneNode(true); c.querySelectorAll('script').forEach(x => x.remove()); return c.innerHTML; })()")
        check('Noise reduction</strong> (desktop program' not in helpTxt and 'Noise reduction window' not in helpTxt, tag + 'Help and What\u2019s new no longer describe the window')
        # the real flow: open the photos, open Crop, read the print line
        pg.set_input_files('#fileInput', ['/tmp/t076/big8640.jpg', '/tmp/t076/exact6000.jpg']); pg.wait_for_timeout(3500)
        for name, want in [('big8640.jpg', 'to 28 \u00d7 19 in (300 ppi)'), ('exact6000.jpg', 'to 20 \u00d7 13 in (300 ppi)')]:
            pg.click(f'#strip [aria-label="{name}"]'); pg.wait_for_timeout(1500)
            if not pg.evaluate("document.getElementById('editView').offsetParent"): pg.click('#editTab'); pg.wait_for_timeout(800)
            pg.click('#cropTab'); pg.wait_for_timeout(1000)
            if pg.evaluate("document.getElementById('ePrIn').getAttribute('aria-pressed')") != 'true': pg.click('#ePrIn'); pg.wait_for_timeout(300)
            line = pg.evaluate("document.getElementById('ePrLine').textContent")
            more = pg.evaluate("[document.getElementById('ePrM1').textContent, document.getElementById('ePrM2').textContent]")
            check(want in line, f'{tag}{name} crop panel: "{line}"')
            if name == 'big8640.jpg':
                check('to 43 \u00d7 28 in (200 ppi)' in more[0] and 'to 57 \u00d7 38 in (150 ppi)' in more[1], f'{tag}{name} more lines: {more}')
                if not desk: pg.screenshot(path='/tmp/t076/crop_8640.png')
            pg.click('#eCropBtn'); pg.wait_for_timeout(400)
        pg.click('#strip [aria-label="big8640.jpg"]'); pg.wait_for_timeout(1000)
        # Adjust still saves edits, and a new edit record carries no noise keys
        if not pg.evaluate("document.getElementById('editView').offsetParent"): pg.click('#editTab'); pg.wait_for_timeout(800)
        pg.evaluate("(() => { const i = document.getElementById('e_exp'); i.value = 25; i.dispatchEvent(new Event('input')); })()"); pg.wait_for_timeout(600)
        recs = [r for r in json.loads(pg.evaluate("localStorage.getItem('chimp-edits')")).values() if r.get('exp') == 25]
        check(len(recs) == 1 and not any(k.startswith('nr') for k in recs[0]), tag + 'Adjust saves an edit with no noise keys: ' + str(recs))
        label = pg.evaluate("""(() => { const e = document.querySelector('#strip [aria-label="big8640.jpg"] .ed'); return e ? e.textContent + ' | ' + e.title : ''; })()""")
        check(label.startswith('Edited') and 'Noise' not in label, tag + 'thumbnail label: ' + label)
        check(not errs, tag + 'no page errors ' + (str(errs) if errs else ''))
        ctx.close()
    b.close()
print('\n%d failures' % len(fails)); sys.exit(1 if fails else 0)
