// Tests the focus translator with real ExifTool output from sample files of each brand
// (tests/fixtures/exiftool-samples.json, made with ExifTool 13.61 from its own test images)
// plus records shaped like current cameras. Run: node tests/focus.test.js
const assert = require('assert');
const F = require('../desktop-focus.js');
const near = (a, b, msg) => assert(Math.abs(a - b) < 0.005, `${msg}: ${a} vs ${b}`);
const center = b => [b.x + b.w / 2, b.y + b.h / 2];
const byName = Object.fromEntries(require('./fixtures/exiftool-samples.json').map(r => [r.SourceFile.split('/').pop(), F.normalize(r)]));

// Canon 350D (CR2): center point in focus.
let r = byName['CanonRaw.cr2']; assert(r.found); assert.equal(r.boxes.length, 1); assert.equal(r.boxes[0].point, 3);
near(center(r.boxes[0])[0], 0.5, 'CR2 x'); near(center(r.boxes[0])[1], 0.5, 'CR2 y');
// Canon EOS M50 (CR3): one area right of center and low (EOS: Y measured upward, so -327 is below center).
r = byName['CanonRaw.cr3']; assert(r.found);
near(center(r.boxes[0])[0], (3000 + 392) / 6000, 'CR3 x'); near(center(r.boxes[0])[1], (2000 + 327) / 4000, 'CR3 y');
near(r.boxes[0].w, 337 / 6000, 'CR3 width');
// Canon 1D Mark III: point 13 of 45.
r = byName['Canon1DmkIII.jpg']; assert.equal(r.boxes[0].point, 13);
near(center(r.boxes[0])[0], (1944 + 311) / 3888, '1D x'); near(center(r.boxes[0])[1], (1296 + 277) / 2592, '1D y');
// Canon Rebel, manual focus: nothing in focus, and says so.
r = byName['Canon.jpg']; assert(!r.found); assert(/manual focus/i.test(r.note));
// Panasonic LX3: center point.
r = byName['Panasonic.rw2']; assert(r.found); near(center(r.boxes[0])[0], 0.5, 'Pana x'); near(center(r.boxes[0])[1], 0.5, 'Pana y');
// Nikon D70: point name only, explained.
r = byName['Nikon.nef']; assert(!r.found); assert(/name of the AF point/.test(r.note));
// Olympus compact and Pentax: nothing usable, no error.
assert(!byName['Olympus2.jpg'].found); assert(!byName['Pentax.jpg'].found);

// Current cameras (record shapes from ExifTool's tag documentation).
r = F.normalize({ Make: 'NIKON CORPORATION', Model: 'NIKON Z 8', AFImageWidth: 8256, AFImageHeight: 5504, AFAreaXPosition: 6192, AFAreaYPosition: 1376, AFAreaWidth: 412, AFAreaHeight: 412, Orientation: 1 });
assert(r.found); near(center(r.boxes[0])[0], 0.75, 'Z8 x'); near(center(r.boxes[0])[1], 0.25, 'Z8 y'); near(r.boxes[0].w, 412 / 8256, 'Z8 w');
r = F.normalize({ Make: 'FUJIFILM', Model: 'X-T5', FocusPixel: '3120 1040', ExifImageWidth: 6240, ExifImageHeight: 4160 });
assert(r.found); near(center(r.boxes[0])[0], 0.5, 'Fuji x'); near(center(r.boxes[0])[1], 0.25, 'Fuji y');
r = F.normalize({ Make: 'OM Digital Solutions', Model: 'OM-1', AFFrameSize: '1200 900', AFFocusArea: '840 180 120 90' });
assert(r.found); near(center(r.boxes[0])[0], 0.75, 'OM x'); near(center(r.boxes[0])[1], 0.25, 'OM y'); near(r.boxes[0].w, 0.1, 'OM w');
r = F.normalize({ Make: 'OLYMPUS CORPORATION', Model: 'E-M1MarkIII', AFPointSelected: '0.4 0.45 0.5 0.55' });
assert(r.found); near(center(r.boxes[0])[0], 0.45, 'EM1 x');
r = F.normalize({ Make: 'SONY', Model: 'ILCE-1', FocusLocation: '8640 5760 2160 4320' });
assert(r.found); near(center(r.boxes[0])[0], 0.25, 'Sony x'); near(center(r.boxes[0])[1], 0.75, 'Sony y');
r = F.normalize({ Make: 'Canon', Model: 'Canon EOS R5', AFImageWidth: 8192, AFImageHeight: 5464, AFAreaWidths: '400 0', AFAreaHeights: '400 0', AFAreaXPositions: '-2048 0', AFAreaYPositions: '1366 0', AFPointsInFocus: '1 0', ValidAFPoints: 1 });
near(center(r.boxes[0])[0], 0.25, 'R5 x'); near(center(r.boxes[0])[1], 0.25, 'R5 y (upward is positive on EOS)');
r = F.normalize({ Make: 'Canon', Model: 'Canon PowerShot G7 X', AFImageWidth: 1000, AFImageHeight: 1000, AFAreaWidth: 100, AFAreaHeight: 100, AFAreaXPositions: '0', AFAreaYPositions: '250', AFPointsInFocus: '1' });
near(center(r.boxes[0])[1], 0.75, 'PowerShot y (downward is positive)');
// Canon: nothing in focus but a point selected -> shows the selected point.
r = F.normalize({ Make: 'Canon', Model: 'Canon EOS 90D', AFImageWidth: 1000, AFImageHeight: 1000, AFAreaWidth: 100, AFAreaHeight: 100, AFAreaXPositions: '0 200', AFAreaYPositions: '0 0', AFPointsInFocus: '0', AFPointsSelected: '2' });
assert.equal(r.boxes[0].point, 1); assert.equal(r.boxes[0].how, 'selected');

// Rotation: a box in the top-left of the sensor, shown after each rotation.
const b = { x: 0.1, y: 0.2, w: 0.1, h: 0.05 };
assert.deepEqual(F.rotate(b, 1), { x: 0.1, y: 0.2, w: 0.1, h: 0.05 });
let d = F.rotate(b, 6); near(d.x, 0.75, 'rot6 x'); near(d.y, 0.1, 'rot6 y'); near(d.w, 0.05, 'rot6 w'); near(d.h, 0.1, 'rot6 h');
d = F.rotate(b, 8); near(d.x, 0.2, 'rot8 x'); near(d.y, 0.8, 'rot8 y');
d = F.rotate(b, 3); near(d.x, 0.8, 'rot3 x'); near(d.y, 0.75, 'rot3 y');
r = F.normalize({ Make: 'SONY', FocusLocation: '6000 4000 1500 1000', Orientation: 6 });
near(center(r.boxes[0].display)[0], 0.75, 'rotated display x'); near(center(r.boxes[0].display)[1], 0.25, 'rotated display y');

// Unknown brand or empty record: no error.
assert(!F.normalize({ Make: 'Hasselblad' }).found); assert(!F.normalize(null).found);
console.log('all focus tests passed');
