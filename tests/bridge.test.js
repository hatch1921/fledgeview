// Tests the desktop bridge folder logic with stand-ins for Windows and WebView2. Run: node tests/bridge.test.js
require('fake-indexeddb/auto');
const fs = require('fs'), assert = require('assert');
const src = fs.readFileSync(require('path').join(__dirname, '..', 'desktop-bridge.js'), 'utf8');

class FDir { constructor(p) { this.kind = 'directory'; this.path = p; this.name = p.split('\\').pop(); }
  async isSameEntry(o) { return !!o && o.path === this.path; }
  async resolve(h) { return h.path.startsWith(this.path + '\\') ? h.path.slice(this.path.length + 1).split('\\') : null; } }
class FFile { constructor(p) { this.kind = 'file'; this.path = p; } }

function setup({ pick, handleOk = true, delay = 0, ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edg/141', store = {}, missing = [] }) {
  const listeners = [], calls = [], winEvents = {}, notes = [];
  const win = {
    navigator: { userAgent: ua },
    __TAURI__: {
      opener: { openUrl: async () => {} },
      event: { listen: async (name, f) => { (win.__events = win.__events || {})[name] = f; return () => { delete win.__events[name]; }; } },
      core: { invoke: async (cmd, args) => {
        calls.push([cmd, args]);
        if (cmd === 'fv_pick_folder') return pick;
        if (cmd === 'fv_read_tags') return args.paths.map(p => ({ SourceFile: p.replace(/\\\\/g, '/'), Make: 'SONY', FocusLocation: '6000 4000 1500 1000' }));
        if (cmd === 'fv_finish_raw') return new Uint8Array([0xFF, 0xD8, 0xFF, (args.edit && args.edit.exp) || 0]).buffer;
        if (cmd === 'fv_develop_raw') { if (/missing/.test(args.path)) throw 'couldn\'t develop this raw file: Input/output error'; return new Uint8Array([0xFF, 0xD8, 0xFF, args.size === 'full' ? 2 : 1]).buffer; }
        if (cmd === 'fv_send_dir_handle') {
          if (!handleOk) throw 'ICoreWebView2Environment14 not supported';
          if (missing.includes(args.path)) throw 'not a folder: ' + args.path;
          setTimeout(() => listeners.forEach(f => f({ data: { fvHandle: args.id, path: args.path }, additionalObjects: [new FDir(args.path)] })), delay);
        }
      } } },
    chrome: { webview: { addEventListener: (t, f) => t === 'message' && listeners.push(f) } },
    showDirectoryPicker: async () => 'ORIGINAL',
    open: () => {}, alert: () => {}, toast: t => notes.push(t),
    addEventListener: (t, f) => { (winEvents[t] = winEvents[t] || []).push(f); },
    localStorage: { getItem: k => store[k] ?? null, setItem: (k, v) => { store[k] = String(v); } },
    indexedDB, DOMException, Blob, FV_FOCUS: require('../desktop-focus.js'),
  };
  const btn = { click: () => { const p = win.showDirectoryPicker({ mode: 'read', id: 'chimp' }); p.catch(() => {}); win.lastAppPick = p; } };
  const doc = { documentElement: { classList: { add() {} } }, addEventListener() {}, querySelectorAll: () => [], getElementById: id => id === 'openFolder' ? btn : null };
  new Function('window', 'document', 'navigator', 'chrome', 'indexedDB', 'localStorage', 'alert', 'console', 'confirm', 'Blob', src)
    (win, doc, win.navigator, win.chrome, indexedDB, win.localStorage, win.alert, { warn() {} }, () => false, Blob);
  const fireLoad = () => (winEvents.load || []).forEach(f => f());
  return { win, calls, store, notes, fireLoad };
}

(async () => {
  // 1. Choose a folder: Windows window, real handle, path remembered.
  let t = setup({ pick: 'D:\\Photos\\2026' });
  assert(String(t.win.showDirectoryPicker).includes('fv_pick_folder'), 'picker replaced on Windows');
  const h = await t.win.showDirectoryPicker({ id: 'main', mode: 'readwrite' });
  assert.equal(h.kind, 'directory'); assert.equal(h.path, 'D:\\Photos\\2026');
  assert.equal(t.win.FV_DESKTOP.nativeFolders, true);
  assert.equal(await t.win.FV_DESKTOP.pathOf(h), 'D:\\Photos\\2026');
  // 2. A photo inside, and inside a subfolder.
  assert.equal(await t.win.FV_DESKTOP.pathOf(new FFile('D:\\Photos\\2026\\heron.ARW')), 'D:\\Photos\\2026\\heron.ARW');
  assert.equal(await t.win.FV_DESKTOP.pathOf(new FFile('D:\\Photos\\2026\\Picks\\a.jpg')), 'D:\\Photos\\2026\\Picks\\a.jpg');
  assert.equal(await t.win.FV_DESKTOP.pathOf(new FFile('E:\\Other\\x.jpg')), null);
  // 3. The folder window starts where it was last used for that purpose.
  t.calls.length = 0; await t.win.showDirectoryPicker({ id: 'main' });
  assert.equal(t.calls[0][1].start, 'D:\\Photos\\2026');
  // 4. startIn given as a known handle starts there.
  t.calls.length = 0; await t.win.showDirectoryPicker({ id: 'other', startIn: h });
  assert.equal(t.calls[0][1].start, 'D:\\Photos\\2026');
  // 5. Cancel gives the same error a browser gives.
  t = setup({ pick: null });
  await assert.rejects(t.win.showDirectoryPicker(), e => e.name === 'AbortError');
  // 6. Old WebView2 without handle support: falls back to the standard picker.
  t = setup({ pick: 'D:\\Photos', handleOk: false });
  assert.equal(await t.win.showDirectoryPicker(), 'ORIGINAL'); assert.equal(t.win.FV_DESKTOP.nativeFolders, false);
  // 7. Not Windows: the picker is left alone.
  const mac = setup({ pick: '/x', ua: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0)' });
  assert.equal(await mac.win.showDirectoryPicker(), 'ORIGINAL', 'picker untouched off Windows');
  assert.equal(mac.calls.length, 0);
  // 8. Nested folders: the most specific one wins.
  t = setup({ pick: 'D:\\Photos' }); await t.win.showDirectoryPicker({ id: 'a' });
  t.win.__TAURI__.core.invoke = (orig => async (c, a) => c === 'fv_pick_folder' ? 'D:\\Photos\\Birds' : orig(c, a))(t.win.__TAURI__.core.invoke);
  await t.win.showDirectoryPicker({ id: 'b' });
  assert.equal(await t.win.FV_DESKTOP.pathOf(new FFile('D:\\Photos\\Birds\\owl.NEF')), 'D:\\Photos\\Birds\\owl.NEF');

  // 9. Open folder (the app's 'chimp' request) is remembered; export and import folders are not.
  t = setup({ pick: 'D:\\Shoots\\Cranes' });
  await t.win.showDirectoryPicker({ mode: 'read', id: 'chimp' });
  assert.equal(JSON.parse(t.store['fvd-session']).path, 'D:\\Shoots\\Cranes');
  t.win.__TAURI__.core.invoke = (orig => async (c, a) => c === 'fv_pick_folder' ? 'E:\\Exports' : orig(c, a))(t.win.__TAURI__.core.invoke);
  await t.win.showDirectoryPicker({ mode: 'readwrite', id: 'chimp-web' });
  assert.equal(JSON.parse(t.store['fvd-session']).path, 'D:\\Shoots\\Cranes', 'export folder not remembered as the photo folder');
  // 10. At launch the last folder reopens with no folder window.
  const saved = { ...t.store };
  let r = setup({ pick: 'SHOULD NOT BE ASKED', store: { ...saved } });
  r.fireLoad(); await new Promise(z => setTimeout(z, 800));
  const h2 = await r.win.lastAppPick;
  assert.equal(h2.path, 'D:\\Shoots\\Cranes');
  assert(!r.calls.some(c => c[0] === 'fv_pick_folder'), 'no folder window at launch');
  // 11. After that, Open folder shows the window again as normal.
  r.calls.length = 0; await r.win.showDirectoryPicker({ id: 'chimp' });
  assert(r.calls.some(c => c[0] === 'fv_pick_folder'));
  // 12. Turned off: nothing reopens.
  r = setup({ pick: 'x', store: { ...saved, 'fvd-resume': 'off' } });
  r.fireLoad(); await new Promise(z => setTimeout(z, 800));
  assert.equal(r.win.lastAppPick, undefined);
  // 13. Folder gone (drive unplugged): a friendly note, and the app sees a quiet cancel.
  r = setup({ pick: 'x', store: { ...saved }, missing: ['D:\\Shoots\\Cranes'] });
  r.fireLoad(); await new Promise(z => setTimeout(z, 800));
  await assert.rejects(r.win.lastAppPick, e => e.name === 'AbortError');
  assert(r.notes[0] && r.notes[0].includes('D:\\Shoots\\Cranes'));
  // 14. When the app supports it: remember the photo, and resume returns folder + photo.
  r = setup({ pick: 'x', store: { ...saved } });
  r.win.FV_DESKTOP.remember({ file: 'A1_05978.ARW', view: '4-up' });
  const res = await r.win.FV_DESKTOP.resume();
  assert.equal(res.handle.path, 'D:\\Shoots\\Cranes'); assert.equal(res.file, 'A1_05978.ARW'); assert.equal(res.view, '4-up');
  r.fireLoad(); await new Promise(z => setTimeout(z, 800));
  assert.equal(r.win.lastAppPick, undefined, 'no button press when the app resumes by itself');
  // 15. Picking a new photo folder starts it at its first photo.
  await r.win.showDirectoryPicker({ id: 'chimp' });
  assert.equal(JSON.parse(r.store['fvd-session']).file, null);
  // 16. Developing a raw: by path or by handle, screen or full, kept for reuse, clear errors.
  r = setup({ pick: 'D:\\Shoots' }); await r.win.showDirectoryPicker({ id: 'chimp' });
  const b1 = await r.win.FV_DESKTOP.develop(new FFile('D:\\Shoots\\owl.CR2'));
  assert.equal(b1.type, 'image/jpeg'); assert.equal(new Uint8Array(await b1.arrayBuffer())[3], 1);
  const b2 = await r.win.FV_DESKTOP.develop('D:\\Shoots\\owl.CR2', { size: 'full' });
  assert.equal(new Uint8Array(await b2.arrayBuffer())[3], 2);
  const calls = r.calls.filter(c => c[0] === 'fv_develop_raw').length;
  await r.win.FV_DESKTOP.develop(new FFile('D:\\Shoots\\owl.CR2'));
  assert.equal(r.calls.filter(c => c[0] === 'fv_develop_raw').length, calls, 'second ask is kept, not developed again');
  await assert.rejects(r.win.FV_DESKTOP.develop(new FFile('E:\\Elsewhere\\x.CR2')), /wasn.t opened from a folder/);
  await assert.rejects(r.win.FV_DESKTOP.develop('D:\\Shoots\\missing.CR2'), /couldn't develop/);
  // 17. Quick finish on a raw: settings passed through unchanged; same settings kept, new ones asked again.
  const f1 = await r.win.FV_DESKTOP.finish(new FFile('D:\\Shoots\\owl.CR2'), { exp: 7, hi: -40 });
  assert.equal(new Uint8Array(await f1.arrayBuffer())[3], 7);
  const sent = r.calls.filter(c => c[0] === 'fv_finish_raw').pop()[1];
  assert.deepEqual(sent.edit, { exp: 7, hi: -40 }); assert.equal(sent.size, 'screen'); assert.equal(sent.path, 'D:\\Shoots\\owl.CR2');
  const nFin = r.calls.filter(c => c[0] === 'fv_finish_raw').length;
  await r.win.FV_DESKTOP.finish('D:\\Shoots\\owl.CR2', { exp: 7, hi: -40 });
  assert.equal(r.calls.filter(c => c[0] === 'fv_finish_raw').length, nFin, 'same settings kept');
  await r.win.FV_DESKTOP.finish('D:\\Shoots\\owl.CR2', { exp: 9 });
  assert.equal(r.calls.filter(c => c[0] === 'fv_finish_raw').length, nFin + 1, 'new settings asked again');
  assert.equal(r.win.FV_DESKTOP.features.rawFinish, true);
  // 18. Noise reduction is removed (0.9.76): switched off, no API, and saved noise settings never reach the program.
  assert.equal(r.win.FV_DESKTOP.features.noise, false);
  assert.equal(r.win.FV_DESKTOP.noise, undefined);
  assert.equal(r.win.FV_DESKTOP.withSubject, undefined);
  const nFocus = r.calls.filter(c => c[0] === 'fv_read_tags').length;
  await r.win.FV_DESKTOP.finish('D:\\Shoots\\heron.CR2', { exp: 7, nr: 50, nrd: 40, nrc: 80, nrt: 1, nrp: 90, nrs: { x: 0.1, y: 0.1, w: 0.2, h: 0.2 } });
  let sentEdit = r.calls.filter(c => c[0] === 'fv_finish_raw').pop()[1].edit;
  assert.deepEqual(sentEdit, { exp: 7 }, 'noise settings dropped: ' + JSON.stringify(sentEdit));
  assert.equal(r.calls.filter(c => c[0] === 'fv_read_tags').length, nFocus, 'no focus lookup for a subject box');
  // 19. A photo edited in a test build with noise reduction matches the same edit without it (same cached result).
  const nFin2 = r.calls.filter(c => c[0] === 'fv_finish_raw').length;
  await r.win.FV_DESKTOP.finish('D:\\Shoots\\heron.CR2', { exp: 7 });
  assert.equal(r.calls.filter(c => c[0] === 'fv_finish_raw').length, nFin2, 'same settings once noise is dropped');
  // 20. The original settings object is left as the app gave it.
  const given = { exp: 3, nr: 20 };
  await r.win.FV_DESKTOP.finish('D:\\Shoots\\heron.CR2', given);
  assert.deepEqual(given, { exp: 3, nr: 20 });
  assert.equal(r.win.FV_DESKTOP.features.rawDevelop, true); assert.equal(r.win.FV_DESKTOP.features.bursts, true);
  console.log('all bridge tests passed');
})().catch(e => { console.error('FAILED', e); process.exit(1); });
