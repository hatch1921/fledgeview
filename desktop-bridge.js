/* FledgeView desktop bridge.
   Small additions that run only inside the desktop program (never on fledgeview.com).
   build_desktop.py places this in the page head, ahead of the app. */
(function () {
  'use strict';
  var T = window.__TAURI__;
  if (!T) return;
  var isWindows = /Windows/i.test(navigator.userAgent);
  var D = window.FV_DESKTOP = { bridge: 2, platform: isWindows ? 'windows' : 'other', nativeFolders: false, lastFolder: null };
  document.documentElement.classList.add('fv-desktop');

  /* ---------- Links: web pages and email open in the person's own browser and mail app ---------- */
  var isExternal = function (u) { return typeof u === 'string' && /^(https?:|mailto:)/i.test(u); };
  var openExternal = function (u) { return T.opener.openUrl(u).catch(function () {}); };
  window.FV_openExternal = openExternal;
  var nativeOpen = window.open.bind(window);
  window.open = function (u) {
    if (isExternal(u)) { openExternal(u); return null; }
    return nativeOpen.apply(window, arguments);
  };
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (!a || a.hasAttribute('download')) return;
    if (isExternal(a.getAttribute('href'))) { e.preventDefault(); openExternal(a.href); }
  }, true);

  /* ---------- Folders: the system folder window, with the real location remembered ---------- */
  // Each folder handle the program hands out is remembered with its path (in memory and in a small
  // database), so desktop features can find a photo's real location: FV_DESKTOP.pathOf(handle).
  var paths = new WeakMap();
  var live = [];   // [path, handle] for folders opened this session, newest first
  var DB = 'fledgeview-desktop', STORE = 'folders', MAX_FOLDERS = 40;
  function db() {
    return new Promise(function (res, rej) {
      var r = indexedDB.open(DB, 1);
      r.onupgradeneeded = function () { r.result.createObjectStore(STORE); };
      r.onsuccess = function () { res(r.result); };
      r.onerror = function () { rej(r.error); };
    });
  }
  function dbAll() {
    return db().then(function (d) {
      return new Promise(function (res) {
        var out = [], tx = d.transaction(STORE, 'readonly'), c = tx.objectStore(STORE).openCursor();
        c.onsuccess = function () { var k = c.result; if (k) { out.push([k.key, k.value]); k.continue(); } else res(out); };
        c.onerror = function () { res(out); };
      });
    }).catch(function () { return []; });
  }
  function remember(handle, path) {
    paths.set(handle, path);
    live = [[path, handle]].concat(live.filter(function (e) { return e[0] !== path; })).slice(0, MAX_FOLDERS);
    D.lastFolder = path;
    db().then(function (d) {
      var st = d.transaction(STORE, 'readwrite').objectStore(STORE);
      st.put({ handle: handle, used: Date.now() }, path);
    }).then(function () {
      return dbAll().then(function (all) {
        if (all.length <= MAX_FOLDERS) return;
        all.sort(function (a, b) { return (b[1].used || 0) - (a[1].used || 0); });
        return db().then(function (d) {
          var st = d.transaction(STORE, 'readwrite').objectStore(STORE);
          all.slice(MAX_FOLDERS).forEach(function (e) { st.delete(e[0]); });
        });
      });
    }).catch(function () {});
  }
  var sep = isWindows ? '\\' : '/';
  function join(base, parts) { return [base.replace(/[\\/]+$/, '')].concat(parts).join(sep); }

  /** The real location of a folder or file handle from a folder the program opened, or null. */
  D.pathOf = function (handle) {
    if (!handle) return Promise.resolve(null);
    if (paths.has(handle)) return Promise.resolve(paths.get(handle));
    return dbAll().then(function (stored) {
      var all = live.map(function (e) { return [e[0], { handle: e[1] }]; }).concat(stored);
      all.sort(function (a, b) { return b[0].length - a[0].length; });   // most specific folder first
      var i = 0;
      function next() {
        if (i >= all.length) return null;
        var p = all[i][0], root = all[i][1].handle; i++;
        return new Promise(function (r) { r(root.isSameEntry(handle)); }).then(function (same) {
          if (same) return p;
          return root.resolve(handle).then(function (rel) { return rel ? join(p, rel) : next(); });
        }).catch(next);
      }
      return next();
    });
  };

  var originalPicker = window.showDirectoryPicker && window.showDirectoryPicker.bind(window);
  var waiting = new Map();
  if (isWindows && originalPicker && window.chrome && chrome.webview) {
    chrome.webview.addEventListener('message', function (e) {
      var d = e.data;
      if (!d || !d.fvHandle || !waiting.has(d.fvHandle)) return;
      var w = waiting.get(d.fvHandle); waiting.delete(d.fvHandle);
      var h = e.additionalObjects && e.additionalObjects[0];
      if (h && h.kind === 'directory') w.resolve(h); else w.reject(new Error('no folder handle arrived'));
    });

    /** A real browser folder handle for a path, created by the program (no folder window). */
    D.handleForPath = function (path) {
      var id = 'fv' + Date.now().toString(36) + Math.random().toString(36).slice(2);
      var arrived = new Promise(function (resolve, reject) {
        waiting.set(id, { resolve: resolve, reject: reject });
        setTimeout(function () { if (waiting.delete(id)) reject(new Error('the folder handle took too long')); }, 12000);
      });
      return T.core.invoke('fv_send_dir_handle', { path: path, id: id })
        .then(function () { return arrived; })
        .then(function (h) { remember(h, path); return h; }, function (err) { waiting.delete(id); throw err; });
    };

    var startFor = function (opts) {
      opts = opts || {};
      var key = 'fvd-start-' + (opts.id || 'default');
      var s = opts.startIn;
      var fromHandle = s && typeof s === 'object' ? D.pathOf(s) : Promise.resolve(null);
      return fromHandle.then(function (p) {
        if (p) return p;
        try { var saved = localStorage.getItem(key); if (saved) return saved; } catch (e) {}
        return typeof s === 'string' ? s : null;
      });
    };

    window.showDirectoryPicker = function (opts) {
      var key = 'fvd-start-' + ((opts && opts.id) || 'default');
      var isMain = !!opts && opts.id === MAIN_ID;
      if (isMain && resumePath) {
        // Reopening the last folder at launch: no folder window, no permission question.
        var p = resumePath; resumePath = null;
        return D.handleForPath(p).then(function (h) { D.nativeFolders = true; return h; }, function () {
          note('Your last folder isn\u2019t available right now: ' + p + '. If it\u2019s on a drive that\u2019s unplugged, plug it in and use Open folder.');
          throw new DOMException('The last folder is not available.', 'AbortError');
        });
      }
      return startFor(opts).then(function (start) {
        return T.core.invoke('fv_pick_folder', { start: start });
      }).then(function (path) {
        if (!path) throw new DOMException('The user aborted a request.', 'AbortError');
        try { localStorage.setItem(key, path); } catch (e) {}
        return D.handleForPath(path).then(function (h) {
          D.nativeFolders = true;
          if (isMain) saveSession({ path: path, file: null });   // a new folder starts at its first photo
          return h;
        }, function (err) {
          // Older WebView2 versions can't create handles: fall back to the standard picker.
          console.warn('FledgeView desktop: using the standard folder picker', err);
          D.nativeFolders = false;
          return originalPicker(opts);
        });
      });
    };
  }

  /* ---------- Where did the camera focus? (all brands, via the bundled ExifTool) ---------- */
  // FV_DESKTOP.focus(fileHandle or path)          -> one answer (see desktop-focus.js), or null
  // FV_DESKTOP.focus([fileHandle or path, ...])   -> a list of answers in the same order
  // Answers are kept, so asking again about the same photo is instant.
  D.features = { focusPoints: true, bursts: true, rawDevelop: true, rawFinish: true, noise: false };
  var focusCache = new Map();
  var keyOf = function (p) { var k = String(p).replace(/\\/g, '/'); return isWindows ? k.toLowerCase() : k; };
  D.focus = function (items) {
    var single = !Array.isArray(items), list = single ? [items] : items;
    return Promise.all(list.map(function (it) { return typeof it === 'string' ? it : D.pathOf(it); })).then(function (paths) {
      var need = [];
      paths.forEach(function (p) { if (p && !focusCache.has(keyOf(p)) && need.indexOf(p) < 0) need.push(p); });
      var chunks = [];
      for (var i = 0; i < need.length; i += 200) chunks.push(need.slice(i, i + 200));
      return chunks.reduce(function (prev, chunk) {
        return prev.then(function () {
          return T.core.invoke('fv_read_tags', { paths: chunk, tags: window.FV_FOCUS.TAGS }).then(function (recs) {
            (recs || []).forEach(function (r) { if (r && r.SourceFile) focusCache.set(keyOf(r.SourceFile), window.FV_FOCUS.normalize(r)); });
            chunk.forEach(function (p) { if (!focusCache.has(keyOf(p))) focusCache.set(keyOf(p), null); });
          });
        });
      }, Promise.resolve()).then(function () {
        var out = paths.map(function (p) { return p ? focusCache.get(keyOf(p)) || null : null; });
        return single ? out[0] : out;
      });
    });
  };

  /* ---------- Developing raw files (LibRaw, matched to the camera's own look) ---------- */
  // FV_DESKTOP.develop(fileHandle or path, { size: 'screen' | 'full' }) -> a JPEG Blob, upright,
  // looking like the camera's rendering but made from the raw data. 'screen' is fast (long edge up to
  // 3000 px) for editing on screen; 'full' is full resolution for export. The last few are kept.
  var developed = new Map(), DEV_KEEP = 6;
  D.develop = function (item, opts) {
    var size = opts && opts.size === 'full' ? 'full' : 'screen';
    return (typeof item === 'string' ? Promise.resolve(item) : D.pathOf(item)).then(function (path) {
      if (!path) throw new Error('This photo wasn\u2019t opened from a folder, so the program can\u2019t find the raw file.');
      var key = keyOf(path) + '|' + size;
      if (developed.has(key)) { var hit = developed.get(key); developed.delete(key); developed.set(key, hit); return hit; }
      return T.core.invoke('fv_develop_raw', { path: path, size: size }).then(function (buf) {
        var blob = new Blob([buf], { type: 'image/jpeg' });
        developed.set(key, blob);
        while (developed.size > DEV_KEEP) developed.delete(developed.keys().next().value);
        return blob;
      });
    });
  };

  /* ---------- Quick finish on raw data (16-bit, in the program) ---------- */
  // FV_DESKTOP.finish(fileHandle or path, edit, { size: 'screen' | 'full' }) -> a JPEG Blob.
  // `edit` is the app's own Quick finish settings object, unchanged (exp, temp, tint, bl, wh, con, hi, sh,
  // cla, vib, sat, shp, vig, bw, bwf, bwt, rot, crop). Same math as the app, applied to the raw file's
  // 16-bit data, so pulling exposure or highlights down can bring back what the camera's JPEG clipped.
  var finished = new Map(), FIN_KEEP = 4;
  D.finish = function (item, edit, opts) {
    var size = opts && opts.size === 'full' ? 'full' : 'screen';
    return (typeof item === 'string' ? Promise.resolve(item) : D.pathOf(item)).then(function (path) {
      if (!path) throw new Error('This photo wasn\u2019t opened from a folder, so the program can\u2019t find the raw file.');
      var e2 = withoutNoise(edit);
      var key = keyOf(path) + '|' + size + '|' + JSON.stringify(e2);
      if (finished.has(key)) return finished.get(key);
      return T.core.invoke('fv_finish_raw', { path: path, edit: e2, size: size }).then(function (buf) {
        var blob = new Blob([buf], { type: 'image/jpeg' });
        finished.set(key, blob);
        while (finished.size > FIN_KEEP) finished.delete(finished.keys().next().value);
        return blob;
      });
    });
  };

  /* ---------- Noise reduction: removed (0.9.76) ---------- */
  // Non-AI results weren't good enough next to Topaz, DxO and Lightroom Denoise. The engine (src-tauri/src/denoise.rs)
  // stays in the program, shelved, but nothing here can reach it: features.noise is false, there is no FV_DESKTOP.noise,
  // and finish() drops any noise settings a test build saved (nr, nrd, nrc, nrt, nrp, nrs) before the program sees them.
  var NOISE_KEYS = ['nr', 'nrd', 'nrc', 'nrt', 'nrp', 'nrs'];
  var withoutNoise = function (edit) {
    var copy = {}; edit = edit || {};
    for (var k in edit) if (NOISE_KEYS.indexOf(k) < 0) copy[k] = edit[k];
    return copy;
  };

  /* ---------- Start where I left off ---------- */
  // The program remembers the folder last opened with Open folder and reopens it at launch.
  // When the shared app supports it, it also returns to the photo and view (see D.remember / D.resume).
  var MAIN_ID = 'chimp';                       // the app's id for its Open folder request
  var SESSION_KEY = 'fvd-session', RESUME_KEY = 'fvd-resume';
  var resumePath = null;
  function session() { try { return JSON.parse(localStorage.getItem(SESSION_KEY) || 'null'); } catch (e) { return null; } }
  function saveSession(patch) {
    try {
      var s = patch.path ? { path: patch.path } : (session() || {});
      for (var k in patch) if (k !== 'path') s[k] = patch[k];
      s.saved = Date.now();
      localStorage.setItem(SESSION_KEY, JSON.stringify(s));
    } catch (e) {}
  }
  D.resumeOn = function () { try { return localStorage.getItem(RESUME_KEY) !== 'off'; } catch (e) { return true; } };
  D.setResume = function (on) { try { localStorage.setItem(RESUME_KEY, on ? 'on' : 'off'); } catch (e) {} };
  /** For the app: remember where the person is (current photo name and any view settings). */
  D.remember = function (state) { if (state && typeof state === 'object') saveSession(state); };
  /** For the app: at launch, the last folder (as a handle) and where the person was, or null. */
  D.resume = function () {
    D.appResumes = true;
    var s = session();
    if (!D.resumeOn() || !s || !s.path || !D.handleForPath) return Promise.resolve(null);
    return D.handleForPath(s.path).then(function (h) {
      var out = { handle: h }; for (var k in s) if (k !== 'path' && k !== 'saved') out[k] = s[k];
      return out;
    }, function () {
      note('Your last folder isn\u2019t available right now: ' + s.path + '. If it\u2019s on a drive that\u2019s unplugged, plug it in and use Open folder.');
      return null;
    });
  };
  // Until the app calls D.resume itself, reopen the folder by pressing Open folder at launch.
  function autoResume() {
    if (D.appResumes || !D.resumeOn() || !D.handleForPath) return;
    var s = session(), btn = document.getElementById('openFolder');
    if (!s || !s.path || !btn) return;
    resumePath = s.path;
    btn.click();
    setTimeout(function () { resumePath = null; }, 8000);   // the app didn't ask: forget it
  }
  window.addEventListener('load', function () { setTimeout(autoResume, 700); });

  // A short, non-blocking message at the bottom of the window.
  function note(text) {
    if (typeof window.toast === 'function') { try { window.toast(text); return; } catch (e) {} }
    var n = document.createElement('div');
    n.textContent = text;
    n.style.cssText = 'position:fixed;left:50%;bottom:28px;transform:translateX(-50%);max-width:640px;padding:12px 18px;' +
      'background:#2b2f33;color:#f2f2f2;border:1px solid #444;border-radius:8px;font:14px/1.4 system-ui,sans-serif;z-index:2147483647;box-shadow:0 6px 24px rgba(0,0,0,.4)';
    (document.body || document.documentElement).appendChild(n);
    setTimeout(function () { n.remove(); }, 9000);
  }

  /* ---------- Saves: say where the file went ---------- */
  // Saves the page makes as downloads (Frame, single exports, galleries) land in the Downloads folder.
  // The program reports each finished save; show a short note with "Show in folder".
  function savedNote(path) {
    var parts = String(path).split(/[\\/]/), name = parts.pop(), folder = parts.pop() || '';
    var n = document.createElement('div');
    n.setAttribute('role', 'status');
    n.className = 'fv-saved-note';
    n.style.cssText = 'position:fixed;left:50%;bottom:28px;transform:translateX(-50%);display:flex;gap:14px;align-items:center;max-width:720px;' +
      'padding:10px 12px 10px 18px;background:#2b2f33;color:#f2f2f2;border:1px solid #444;border-radius:8px;font:14px/1.4 system-ui,sans-serif;z-index:2147483647;box-shadow:0 6px 24px rgba(0,0,0,.4)';
    var t = document.createElement('span');
    t.textContent = 'Saved to ' + folder + ': ' + name;
    var b = document.createElement('button');
    b.textContent = 'Show in folder';
    b.style.cssText = 'font:inherit;padding:6px 12px;border-radius:6px;border:1px solid #5a6270;background:#3a4048;color:#fff;cursor:pointer';
    b.onclick = function () { if (T.opener && T.opener.revealItemInDir) T.opener.revealItemInDir(path).catch(function () {}); n.remove(); };
    n.appendChild(t); n.appendChild(b);
    var old = document.querySelector('.fv-saved-note'); if (old) old.remove();
    (document.body || document.documentElement).appendChild(n);
    setTimeout(function () { n.remove(); }, 12000);
  }
  D.savedNote = savedNote;
  if (T.event && T.event.listen) T.event.listen('fv-saved', function (e) { savedNote(e.payload); });

  /* ---------- Wording that only applies in a browser ---------- */
  function hideBrowserOnly() {
    var re = /may say\s*[\u201c"]Upload[\u201d"]/;
    var els = document.querySelectorAll('p, div, span, small');
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      if (el.textContent.length > 300 || !re.test(el.textContent)) continue;
      var inner = false;
      for (var j = 0; j < el.children.length; j++) if (re.test(el.children[j].textContent)) inner = true;
      if (!inner) el.style.display = 'none';   // the smallest element holding the sentence
    }
  }
  document.addEventListener('DOMContentLoaded', function () { hideBrowserOnly(); setTimeout(hideBrowserOnly, 1500); });

  /* ---------- Browser-version notes that don't belong in the program ---------- */
  // The one-time "Thanks for using FledgeView" tip note: answered "Maybe later" before it shows,
  // which also records it as seen. (The desktop connection in the shared code will replace this.)
  var NOTES = [{ title: 'Thanks for using FledgeView', button: /^\s*maybe later\s*$/i }];
  function noteFor(el) {
    var t = el && el.textContent || '';
    for (var i = 0; i < NOTES.length; i++) if (t.indexOf(NOTES[i].title) >= 0 && t.length < 1500) return NOTES[i];
    return null;
  }
  function dismiss(box, note) {
    var btns = box.querySelectorAll('button, a');
    for (var i = 0; i < btns.length; i++) if (note.button.test(btns[i].textContent)) { btns[i].click(); return true; }
    return false;
  }
  if (window.HTMLDialogElement) {
    ['showModal', 'show'].forEach(function (m) {
      var orig = HTMLDialogElement.prototype[m];
      if (!orig) return;
      HTMLDialogElement.prototype[m] = function () {
        var note = noteFor(this);
        if (note) { var self = this; setTimeout(function () { dismiss(self, note); if (self.open) self.close(); }, 0); return; }
        return orig.apply(this, arguments);
      };
    });
  }
  // Notes built some other way: check only the parts of the page that just changed.
  function boxWithButton(el, note) {
    for (var up = 0; el && up < 6; up++, el = el.parentElement) {
      var btns = el.querySelectorAll ? el.querySelectorAll('button, a') : [];
      for (var i = 0; i < btns.length; i++) if (note.button.test(btns[i].textContent)) return el;
    }
    return null;
  }
  function check(el) {
    if (!el || el.nodeType !== 1) return;
    var t = el.textContent;
    if (!t || t.length > 3000) return;            // notes are short; skip big containers cheaply
    for (var n = 0; n < NOTES.length; n++) {
      if (t.indexOf(NOTES[n].title) < 0) continue;
      var box = boxWithButton(el, NOTES[n]);
      if (box && box.getClientRects().length) { box.style.visibility = 'hidden'; dismiss(box, NOTES[n]); }
    }
  }
  document.addEventListener('DOMContentLoaded', function () {
    new MutationObserver(function (records) {
      for (var i = 0; i < records.length; i++) {
        var r = records[i];
        if (r.type === 'attributes') check(r.target);
        else for (var j = 0; j < r.addedNodes.length; j++) check(r.addedNodes[j]);
      }
    }).observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class', 'style', 'open', 'hidden'] });
  });

  /* ---------- Ctrl+Shift+D: desktop details, for testing ---------- */
  document.addEventListener('keydown', function (e) {
    if (!(e.ctrlKey && e.shiftKey && (e.key === 'D' || e.key === 'd'))) return;
    e.preventDefault();
    var et = T.core.invoke('fv_exiftool_version').then(function (v) { return 'ready (' + v + ')'; }, function (err) { return 'NOT WORKING: ' + err; });
    var lr = T.core.invoke('fv_libraw_version').then(function (v) { return 'ready (' + v + ')'; }, function (err) { return 'NOT WORKING: ' + err; });
    Promise.all([et, lr]).then(function (r) {
    alert('FledgeView desktop\n\nBridge: ' + D.bridge + '\nSystem: ' + D.platform + '\nExifTool: ' + r[0] + '\nLibRaw: ' + r[1] +
      '\nFolder window: ' + (D.nativeFolders ? 'Windows (native)' : originalPicker ? 'standard (not yet used, or fallback)' : 'not available') +
      '\nLast folder: ' + (D.lastFolder || 'none yet') +
      '\nStart where I left off: ' + (D.resumeOn() ? 'on' : 'off'));
    if (confirm('Start where I left off is ' + (D.resumeOn() ? 'ON' : 'OFF') + '. Switch it ' + (D.resumeOn() ? 'off' : 'on') + '?')) D.setResume(!D.resumeOn());
    });
  }, true);
})();
