# FledgeView tests

These are the browser tests used during development (Python + Playwright + Chromium). They were written for the
Claude development environment, so paths near the top of each script point there (sample photos in /tmp/vid,
the A1 II raw in /mnt/user-data/uploads, a local server on port 8790 serving site/). Adjust those paths to rerun.

- qa.py: the main 40-check suite (viewing, culling, ratings, bursts, export, gallery, settings).
- t_split.py / t_crop2.py / t_undo.py / t_undo2.py / t_reach.py / t_cropsize.py: Crop panel, crop and straighten, Undo, Reach, size readout.
- t_edit.py / t_bw.py / t_eexp.py / t_wb.py: Adjust, black and white, the panel's Export, Pick neutral and crushed-black Blinkies.
- t_viewedits.py: the viewer showing edits after Done.
- t_pv.py: Photo view.  t_lensws.py / t_fov.py / t_tele.py: the Lens tools workspace and Field of view.
- t_tiff.py (+ make_test_tiffs.py): TIFF decoding, seven variants, pixel-exact.  t_strip.py: image size for JPEGs without camera data.
- t_soundbyte.py: thumbnails for raw files and TIFFs without a standard thumbnail; Export's Photos list, button label, and Save to.
- t_clearall.py: Clear all clears the screen in six situations (panels open, edited photos), and new photos load after.
- t_burstkeep.py: Shift+P keeps a burst frame and rejects the rest (existing picks stay), Shift+U undoes it, and the session summary.
- t_expo.py: exposure flags (Over, Under, and a lit subject on black that must not be flagged) and their filters. t_hold.py: holding a reference in Compare (H).
- t_pickfail.py: the "No folder was opened" window when Chrome (or Edge) cancels after a folder is chosen; browser-aware wording. Run with a path to test a built copy.
- t_loadcard.py: the loading card for large folders (finding, Stop, reading, Hide, small folders, Open file, both looks); builds a test folder in the origin-private file system and serves the page on port 8791.
- t_inbox.py: 0.9.70 inbox rule for Organize (top level = inbox; moves between lens folders respected; a 0.9.69-recorded top-level photo; New photos only). Needs /tmp/rawlib: 5 Sony JPEGs with lens EXIF (DSC100-102 FE 600mm F4 GM OSS, DSC200-201 FE 100-400mm F4.5-5.6 GM OSS), made with PIL + piexif. Keeps folder handles in memory because the headless test browser crashes when one is saved in IndexedDB.
- t_cardshape.py: 0.9.71 recipe card shapes (Fit, 4:5, square, 9:16) for a wide and a tall photo: exact sizes, photo never cropped, file names, remembered choice. Needs /tmp/lrtest/punchy-wide.jpg and punchy-tall.jpg: JPEGs with a Lightroom crs: XMP packet (PIL save with xmp=). Serves the card font from site/assets/fonts. Cards land in /home/claude/cards for a visual check.
- t_cardfolder.py: 0.9.72 recipe card Save to folder (chosen folder, no overwrite, preset beside it, remembered, Use Downloads, hidden without folder support) and the Shape list colors. Same /tmp/lrtest fixture and in-memory handle workaround as t_inbox.py.
- t_samename.py: change list item 11, same-name photos in Organize (_same name, _already there, plan counts, Undo) and Import (skip copies, _same name). Needs /tmp/rawlib and /tmp/rawlib_b (DSC100 byte copy, DSC101 different content, DSC103 new).
- t_framesave.py: change list item 12, Frame's Save to (folder id chimp-frame, no overwrite, Downloads message, hidden without folder access).
- t_sorttime.py: Capture time – Oldest/Newest.  t_offline.py: the download file with the network blocked.

Lint: tests/lint has the ESLint setup (npm install, then extract the app's <script> into app.js and run npx eslint app.js).


Fixtures: tests/fixtures/ holds copies of /tmp/rawlib, /tmp/rawlib_b and /tmp/lrtest used by t_inbox, t_samename, t_cardshape, t_cardfolder and t_framesave. Copy them to /tmp before running (cp -r tests/fixtures/* /tmp/).
- t_076.py: 0.9.76 noise reduction removed (button, window, saved settings dropped) and print sizes rounding down; runs on site/download/FledgeView.html, needs 8640x5760 and 6000x4000 JPEGs in /tmp/t076.
- t_resume.py: 0.9.77 Start where I left off with a stand-in desktop bridge and real folder handles (private file system): photo, filter, 4-up, Photo view, subfolder choice, no questions at relaunch, a photo no longer matching the filter, the View menu switch, and the website unchanged.
