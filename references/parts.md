# The parts catalogue (sketch theme)

Every circuit part and matter drawing in a sketch short comes from the kit in `assets/gfx/sketch.js`, so a battery, a
resistor or an atom looks the same in every short of a series (the user, 2026-11-21: PN part 3 had two different
batteries). The full API is the header comment of sketch.js; this page is the rules and how to use them. The plan and
its decisions: `docs/plans/2026-11-21-parts-library.md`.

## The rules
- **Kit only.** No home-made `drawBattery`, no meter assembled from `S.circle` + `S.line`. A part the kit lacks is
  added to sketch.js and to the catalogue sheet first, and the user approves the sheet before it is used.
  `scripts/check_parts.py` (run by `build_gfx.py`) warns about parts drawn by hand; mark intended free drawing
  (waveforms, lattice bond stubs, arrows of an argument) with `// parts-ok`.
- **The same shape everywhere.** Each part is drawn once in its own 120 px frame with fixed seeds and placed by a
  transform, so it has the same wobble at any position, angle (`rot` 0/90/180/270, any angle works) and size
  (`size: 'S' | 'M' | 'L'` = ⅔ / 1 / ⁴⁄₃, and `'XL' | 'XXL'` = 2 / 3 for a real object as the hero; strokes keep their on-screen width). Letters and polarity marks stay upright.
- **Polarity:** + red, − blue (battery, electrolytic cap, DC source, op-amp inputs, dial terminals).
- **Pins on the 20 px grid.** Place parts at multiples of 20 and the wires line up; the paper grid is 60 px.
- **Labels** with `S.label(part, 'R1', '10kΩ', {side})`: name 48 px, value 44 px (never under 44 in this theme); it moves
  to the other side if it would cross the button column (x > 960) or the top margin (y < 140).

## Using a part
```js
const b = S.battery(200, 700, { rot: 90 });            // centre, options (P on top)
const r = S.res(540, 400, { size: 'L' });
const d = S.led(540, 1000, { rot: 180 });              // anode on the right
const w1 = S.route(b.pins.P, r.pins.A);                 // wires from the returned pins: 20 px grid, right angles,
const w2 = S.route(r.pins.B, d.pins.A, { via: [[880, 1000]] });   // and each returns its points
const w3 = S.route(d.pins.K, b.pins.N);
S.label(r, 'R1', '220Ω');
d.at(6.2, { on: true });                                // states are keyframes: seek-safe
const MAIN = [...w1, ...r.path, ...w2, ...d.path, ...w3];   // the loop: wires and parts in the order the current flows
S.energize(6.0, MAIN); S.stream(6.2, MAIN, { n: 11 });
```
- Every part returns `{ pins, path, paths, box, at(t, state) }` in world coordinates. A current path is the wires'
  points and the parts' `path`s joined in the order the current flows (a part's `path` alone skips the wires). Pin names: `A`/`B` (no
  polarity), `P`/`N` (polarity), `A`/`K` (diodes), `B`/`C`/`E` (BJT), `G`/`D`/`S` (MOSFET), `INP`/`INN`/`OUT` (op-amp),
  `P1 P2 S1 S2` (transformer), `COM`/`NO`/`NC` (SPDT), `C1 C2 COM NO` (relay).
- States: `S.sw` open/closed (`spdt`: `pos` 0/1), `S.relay` closed, `S.led` / `S.ledReal` / `S.lamp` on, `S.dial` value. The change
  is animated (0.25–0.4 s, `sine.inOut`).
- Old two-point calls (`S.res(x1, y1, x2, y2, {s})`, `S.battery(x, y, dir, s)`, `S.npn(cx, cy, s)` …) still work and
  draw the same catalogue shape between the points.

## Parts list (by category)
- **Passive:** `S.res`, `S.pot`, `S.ldr`, `S.thermistor`, `S.cap` (`{polar}`), `S.vcap` (variable cap), `S.ecap`, `S.ind` (`{core}`), `S.xfmr`, `S.fuse`, `S.xtal`.
- **Sources & reference:** `S.battery` (`{cells}`), `S.vdc`, `S.vac`, `S.isrc`, `S.gnd`, `S.vcc`, `S.port`.
- **Semiconductors:** `S.diode` (`kind: 'std'|'led'|'zener'|'photo'|'schottky'`; alias `S.led`), `S.npn`, `S.pnp`, `S.nmos`, `S.pmos`, `S.opamp` (`{power}`), `S.chip`, `S.gate` (`'and'|'or'|'not'|'nand'|'nor'|'xor'`).
- **Switches & outputs:** `S.sw` (`kind: 'spst'|'spdt'|'push'`), `S.relay`, `S.lamp`, `S.motor`, `S.speaker`, `S.buzzer`.
- **Instruments, wiring & layout:** `S.meter` (`label: 'A'|'V'|'Ω'`; aliases `S.ammeter`, `S.voltmeter`), `S.dial`, `S.scope`, `S.wire`, `S.route`, `S.dot`, `S.hop`, `S.term`, `S.curArrow`, `S.block`, `S.label`.
- **Matter:** `S.atom`, `S.electron`, `S.hole`, `S.ion`, `S.lattice`, `S.band`, `S.hill`, `S.glow`, `S.chair`, `S.person`.
- **Real-world illustrations (for "what it actually looks like" and breadboard scenes):**
  - `S.cellReal(cx, cy, {kind: 'AA'|'9V', rot, size, flip})` → pins `{P, N}` (+ red, − blue)
  - `S.resReal(cx, cy, {value: '220', tol: 'gold', rot, size, flip})` → pins `{A, B}` (4-band color code computed from `value`, drawn in hachure as the one pen-colour exception)
  - `S.ledReal(cx, cy, {on, color, rot, size, flip})` → pins `{A, K}` (long anode leg, short cathode leg + flat cathode rim; `.at(t, {on})`)
  - `S.ecapReal(cx, cy, {rot, size, flip})` → pins `{P, N}` (top cross vent, blue − side stripe, long P leg)
  - `S.to92(cx, cy, {pins: 'EBC', label, rot, size, flip})` → 3 legs on 20 px grid (`-20, 0, +20`); pin keys follow `pins` order
  - `S.breadboard(x, y, cols, rows, opts)` (or `(cx, cy, opts)`) → 20 px hole grid, centre trench, top/bottom `+` red / `−` blue rails; returns `hole(c, r)` (supports row index `0..rows-1` or `'top+'`/`'top-'`/`'bot+'`/`'bot-'`)

## The catalogue sheet
```bash
python3 scripts/parts_sheet.py --out chk/parts --sheet catalog     # every part (incl. real-world & real↔symbol), labelled
python3 scripts/parts_sheet.py --out chk/parts --sheet identity    # proof: same path at every angle, size and order
python3 scripts/parts_sheet.py --out chk/parts --sheet circuits    # four example circuits (incl. breadboard) and a 1.5x push
```
Run it from the skill folder (it needs no project). `identity` exits non-zero if any part differs between variants.
Attach the catalogue PNGs when briefing a graphics agent (GFX_BRIEF.md), so the drawings are matched by eye too.
