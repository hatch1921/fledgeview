# FledgeView dev kit (0.9.77 beta)

Everything needed to rebuild FledgeView and fledgeview.com from scratch.

- fledgeview.html: the master app. All changes go here. It loads its libraries from CDNs, so it runs as-is in a browser
  (and is the published Claude test copy).
- site/: fledgeview.com exactly as deployed. The GitHub repo (hatch1921/fledgeview) root = this folder's contents.
  - site/index.html: the home page.  site/app/: the app (index.html, sw.js offline cache, manifest).
  - site/download/FledgeView.html: the single-file offline copy (all libraries and fonts built in).
  - site/assets/: libraries, fonts, icons, screenshots, and assets/licenses (open-source license texts).
- build_site.py: after changing the master, run `python3 build_site.py` (from any folder). It rewrites
  site/app/index.html and site/download/FledgeView.html from fledgeview.html, bumps the offline cache name in
  site/app/sw.js to match the version, and checks that every file the offline cache lists exists.
- tests/: the development test scripts and lint setup (see tests/README.md).

Libraries (all MIT, except the fonts under the SIL Open Font License; license texts in site/assets/licenses
and in the app under Help > About and licenses):
- exifr 7.1.3 (camera data), JSZip 3.10.1 (zip files), utif2 4.1.0 = UTIF.js (TIFF decoding), pako 1.0.11 (ZIP-compressed TIFFs),
  Barlow and Barlow Condensed fonts.
- CDN URLs used by the master: cdn.jsdelivr.net/npm/exifr@7.1.3, cdnjs jszip/3.10.1, cdn.jsdelivr.net/npm/pako@1.0.11,
  cdn.jsdelivr.net/npm/utif2@4.1.0. Note: the older npm package "utif" 3.1.0 decodes LZW TIFFs as black; don't use it.

To publish an update: run build_site.py, then upload site/app, site/download, and any changed site/assets files to the repo.

Not included: the Google Search Console verification file (google....html). It lives only in the GitHub repo; never delete it there.

Handoff doc: https://claude.ai/artifact/N6v1Ujh3B4GygEZPStJrAu
Published test copy: https://claude.ai/artifact/ACmTyWy5tALFCEh5rmqbvn
