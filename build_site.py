"""Builds fledgeview.com's app/ and download/ files from the master fledgeview.html, and bumps the offline cache.

Run from anywhere:  python3 build_site.py
It uses fledgeview.html and site/ next to this script. To point elsewhere, set FV_MASTER and FV_SITE.
"""
import base64, re, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.environ.get('FV_SITE') or os.path.join(HERE, 'site')
MASTER = os.environ.get('FV_MASTER') or os.path.join(HERE, 'fledgeview.html')
for need in (MASTER, f'{SITE}/app/sw.js', f'{SITE}/assets'):
    if not os.path.exists(need): sys.exit(f'build_site.py: missing {need}')
src = open(MASTER, encoding='utf-8').read()
head_cdn = '''<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Condensed:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/exifr@7.1.3/dist/full.umd.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/pako@1.0.11/dist/pako_inflate.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/utif2@4.1.0/UTIF.js"></script>'''
assert src.count(head_cdn) == 1
ver = re.search(r"const VERSION = '([^']+)'", src).group(1)
site_head = '''<link rel="stylesheet" href="/assets/fonts/fonts.css">
<script src="/assets/exifr.umd.js"></script>
<script src="/assets/jszip.min.js"></script>
<script src="/assets/pako_inflate.min.js"></script>
<script src="/assets/utif.js"></script>
<link rel="manifest" href="/app/manifest.webmanifest">
<meta name="theme-color" content="#16171a">
<meta name="description" content="FledgeView: free photo culling for burst shooters. Find the sharp frame, sort by lens, finish, and share, right in your browser. Nothing uploaded.">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/icons/favicon-32.png">
<link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png">'''
app = src.replace(head_cdn, site_head)
i = app.rindex('</body>')
app = app[:i] + '''<script>
if ('serviceWorker' in navigator && (location.protocol === 'https:' || ['localhost', '127.0.0.1'].includes(location.hostname))) { window.addEventListener('load', () => navigator.serviceWorker.register('/app/sw.js', { scope: '/app/' }).catch(() => {})); }
</script>
''' + app[i:]
open(f'{SITE}/app/index.html', 'w', encoding='utf-8').write(app)
cache = 'fledgeview-' + re.sub(r'[^0-9a-z.]+', '-', ver.lower())
sw = open(f'{SITE}/app/sw.js').read()
sw = re.sub(r"const CACHE = '[^']+';", f"const CACHE = '{cache}';", sw)
open(f'{SITE}/app/sw.js', 'w').write(sw)
ff = ''
for fam, slug in (('Barlow', 'barlow'), ('Barlow Condensed', 'barlow-condensed')):
    for w in (400, 500, 600):
        b64 = base64.b64encode(open(f'{SITE}/assets/fonts/{slug}-latin-{w}-normal.woff2', 'rb').read()).decode()
        ff += f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{w};font-display:swap;src:url(data:font/woff2;base64,{b64}) format('woff2')}}\n"
ex = open(f'{SITE}/assets/exifr.umd.js', encoding='utf-8').read(); jz = open(f'{SITE}/assets/jszip.min.js', encoding='utf-8').read()
pk = open(f'{SITE}/assets/pako_inflate.min.js', encoding='utf-8').read(); ut = open(f'{SITE}/assets/utif.js', encoding='utf-8').read()
fav = base64.b64encode(open(f'{SITE}/assets/icons/favicon-32.png', 'rb').read()).decode()
dl = src.replace(head_cdn, f'<style>\n{ff}</style>\n<script>\n{ex}\n</script>\n<script>\n{jz}\n</script>\n<script>\n{pk}\n</script>\n<script>\n{ut}\n</script>\n<link rel="icon" type="image/png" href="data:image/png;base64,{fav}">')
open(f'{SITE}/download/FledgeView.html', 'w', encoding='utf-8').write(dl)
# every file the offline cache lists must exist, or the app won't install for offline use
listed = re.findall(r'"(/(?:assets|app)/[^"]*)"', sw)
missing = [u for u in listed if not u.endswith('/') and not os.path.exists(SITE + u)]
if missing: sys.exit('build_site.py: the offline cache lists files that do not exist: ' + ', '.join(missing))
print('built', ver, '| offline cache', cache, '|', len(listed), 'cached files checked')
