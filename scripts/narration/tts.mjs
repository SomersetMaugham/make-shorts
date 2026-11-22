#!/usr/bin/env node
/**
 * tts.mjs — narration and timeline for a script-to-motion project.
 *
 *   node tts.mjs <projectDir> [--approved] [--only c03,c07] [--force] [--placeholder]
 *
 * Reads <project>/script.json, synthesizes each cue with the TTS provider — by default Google Cloud Text-to-Speech, Chirp 3 HD
 * voice ko-KR-Chirp3-HD-Enceladus (script.json "tts"; "provider": "fish" or "edge" picks the others) — cached by content
 * hash, keeps every take exactly as the provider returned it, applies the cuts the agent wrote, lays the cues end to end with gaps, and writes:
 *   audio/cues/<id>.wav        one file per cue
 *   audio/narration.wav        the full narration, t=0 aligned with the video's t=0
 *   audio/narration.mp3        same, compressed (if ffmpeg is available) — used by the player
 *   js/cues.js                 window.VIDEO_DATA: cue timings the scenes are anchored to
 *   script.txt                 the script as plain text: every cue's text, one per line, no ids or times
 *
 *   --approved     the user decided to record, after reviewing the finished video (or asked for these takes): only
 *                  then are new takes recorded. Without it, cues that have no take yet get placeholder audio (silent,
 *                  estimated timing, flagged `placeholder: true` per cue in js/cues.js) and nothing is sent to Fish
 *                  Audio — the whole video is finished on them first, and the voice is recorded only when the user says so.
 *   --only ids     re-synthesize just these cues (new take), keep the rest from cache (needs --approved)
 *   --force        re-synthesize every cue
 *   --placeholder  no API calls: silent audio with estimated durations (for building visuals
 *                  before a key is available). Real takes already in the cache are still used.
 *   --drop-takes   let recorded cues become placeholders when the settings changed (see below) — only when meant
 *
 * A recorded cue never turns silent unnoticed: when js/cues.js names a take for a cue whose "say" is unchanged, the take
 * is still in .tts-cache, and this run would still make the cue a placeholder (the voice id, model, temperature or top_p
 * differ from what it was recorded with, so its cache key differs), nothing is written and the run says why.
 *
 * No code here decides where silence is — not at a take's edges, not inside it. What comes out of a take is the agent's
 * call, read from the numbers wave.mjs prints (node wave.mjs <dir> --cue <id>, or --unreviewed), written as the cue's
 * "cut" in script.json —
 *   "cut": { "take": "<the take's id, js/cues.js>", "ranges": [[from, to], …] }   seconds in the take as recorded
 * — and applied exactly: an inner stretch with a 10 ms crossfade over its join, a stretch from 0 or up to the take's end
 * (its length as wave.mjs prints it) with nothing of it kept. "ranges": [] says the take was read and nothing goes.
 * A cut made on another take is not applied and is reported. A take kept as recorded that has no cut for it yet is
 * marked `unreviewed: true` in js/cues.js (check.mjs refuses the hand-off until each has its cut), references/sound.md §1.
 * Takes cached before 2026-11-09 had their edges cut by tts.mjs itself (at −38 dBFS) before they were stored: they are
 * still used as they are (re-recording costs credits); what was cut from them is gone.
 *   --record-cache record in generated.json the cached takes of this script's cues that have no record (takes cached
 *                  before the tools kept generated.json) — said once by the user's decision, never as a routine
 *
 * Every file written here that isn't text — the takes in .tts-cache, audio/cues/*.wav, audio/narration.wav|mp3 — is
 * recorded in the project's generated.json with its sha256 (lib/generated.mjs); check.mjs accepts nothing else unlisted.
 *
 * Narration is optional. "narration": false in script.json makes a video WITHOUT narration: no API call, silent
 * audio, each cue timed by its estimated reading time (the cues still drive the scenes).
 * Real narration needs BOTH, provided by the user — nothing is guessed or defaulted:
 *   voice  the user's Fish Audio voice model id: "voice" in script.json, else FISH_VOICE (environment or .env)
 *   key    FISH_API_KEY (or FISH_AUDIO_API_KEY) from the environment, else from a `.env` file in the
 *          project folder or any parent folder, else from the skill's own `.env` (git-ignored, where the user keeps
 *          their keys). The key is never copied into the project.
 * Model: drama-3 by default (directed in plain language: [directions], [sounds/pauses], <emphasis>…</emphasis>) —
 * https://docs.fish.audio/features/text-to-speech · …/text-to-speech/drama-3
 * Without them only "narration": false or --placeholder (temporary, flagged until replaced) runs.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import vm from 'node:vm';
import { spawnSync } from 'node:child_process';
import { scriptSignature } from './lib/scriptsig.mjs';
import { recordGenerated, readRecord, projectOf } from './lib/generated.mjs';
import { SKILL_ENV, fromEnvFile } from './lib/env.mjs';

const API = 'https://api.fish.audio/v1/tts';
const SR = 44100;
const DEFAULTS = {
  voice: '',            // the user's own Fish Audio voice model id — script.json "voice" or FISH_VOICE; never a default
  model: 'drama-3',     // the user's model; a missing/misspelt model header silently falls back to s2.1-pro
  temperature: 0.7,
  top_p: 0.7,
  leadIn: 0.3,
  gap: 0.25,
  tail: 1.5,
};

// ---------- args ----------
const argv = process.argv.slice(2);
const opt = { _: [] };
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a.startsWith('--')) {
    const k = a.slice(2);
    opt[k] = argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[++i] : true;
  } else opt._.push(a);
}
const dir = path.resolve(opt._[0] || '.');
const only = typeof opt.only === 'string' ? new Set(opt.only.split(',').map((s) => s.trim())) : null;

function die(msg, code = 1) {
  console.error('✖ ' + msg);
  process.exit(code);
}

// ---------- script ----------
const scriptPath = path.join(dir, 'script.json');
if (!fs.existsSync(scriptPath)) die(`no script.json in ${dir}`);
let script;
try {
  script = JSON.parse(fs.readFileSync(scriptPath, 'utf8'));
} catch (e) {
  die(`script.json is not valid JSON: ${e.message}`);
}
const cfg = { ...DEFAULTS };
for (const k of Object.keys(DEFAULTS)) if (script[k] != null) cfg[k] = script[k];
const cues = script.cues || [];
if (!cues.length) die('script.json has no cues');

const seen = new Set();
for (const [i, c] of cues.entries()) {
  if (!c.id || !/^[A-Za-z][A-Za-z0-9]*$/.test(c.id)) die(`cue #${i + 1}: id must be alphanumeric starting with a letter (got ${JSON.stringify(c.id)})`);
  if (seen.has(c.id)) die(`duplicate cue id ${c.id}`);
  seen.add(c.id);
  if (!c.say || !String(c.say).trim()) die(`cue ${c.id}: "say" is empty`);
}
if (only) for (const id of only) if (!seen.has(id)) die(`--only: unknown cue id ${id}`);
// the voice is never slowed down or sped up (the user's rule): no speed but 1, for the whole script or for a cue
const sped = [...((script.speed ?? 1) !== 1 ? [`script ×${script.speed}`] : []), ...cues.filter((c) => c.speed != null && c.speed !== 1).map((c) => `${c.id} ×${c.speed}`)];
if (sped.length) die(`speed must stay 1 (${sped.join(', ')}) — the voice is never slowed down or sped up. A rushed take gets pauses in its "say" (commas, "..." between sentences) or a fresh take`);
// …nor for a phrase: drama-3's <fast>…</fast> / <slow>…</slow> change the speed (tone directions like [hurried] are fine)
const speedTags = cues.filter((c) => /<\/?\s*(fast|slow)\b[^>]*>/i.test(c.say)).map((c) => c.id);
if (speedTags.length) die(`<fast>/<slow> tags in "say" (${speedTags.join(', ')}) — the voice is never slowed down or sped up, not even for a phrase. Remove the tags; a tone direction ([hurried], [calm]) or pauses (commas, "...") are fine`);

const stripTags = (s) => s.replace(/\[[^\]]*\]/g, '').replace(/<\|[^|]*\|>/g, '').replace(/<\/?[a-z]+>/gi, '').replace(/\s+/g, ' ').trim();

/** a setting from the environment, else from a .env file in the project or any parent directory, else the skill's own .env */
const FOUND = {};   // where each setting came from: said on every run, so nobody decides "no key" by looking at one file
function findSetting(names) {
  for (const n of names) if (process.env[n]) { FOUND[names[0]] = `the environment (${n})`; return process.env[n].trim(); }
  for (let d = dir; ; d = path.dirname(d)) {
    const v = fromEnvFile(path.join(d, '.env'), names);
    if (v) { FOUND[names[0]] = path.join(d, '.env'); return v; }
    if (path.dirname(d) === d) break;
  }
  const v = fromEnvFile(SKILL_ENV, names);
  if (v) FOUND[names[0]] = SKILL_ENV;
  return v;
}
const silent = script.narration === false;   // a video without narration, by choice
// a free local/engine voice instead of Fish Audio (the user's choice): script.json "tts": { "provider": "edge", "voice": "ko-KR-InJoonNeural" }
// — Microsoft Edge read-aloud voices through the `edge-tts` CLI (no key, no credits). Speed stays 1.
// …or Google Cloud Text-to-Speech (Chirp 3 HD): "tts": { "provider": "google", "voice": "ko-KR-Chirp3-HD-Enceladus" } — authenticates with
// `gcloud auth print-access-token` and the gcloud default project (free up to 1M characters a month; billing must be enabled). Speed stays 1.
// DEFAULT (since 2026-11-13, the user's choice): Google Chirp 3 HD, voice ko-KR-Chirp3-HD-Enceladus, when script.json has no "tts".
// Fish Audio only with "tts": { "provider": "fish" } (then the user's FISH_API_KEY and voice id are required, as before).
// a project made before the switch that names a Fish voice id in "voice" and has no "tts" stays on Fish Audio (its takes' cache keys depend on it)
const provider = (script.tts && script.tts.provider) || (script.voice ? 'fish' : 'google');
if (!['google', 'edge', 'fish'].includes(provider)) die(`script.json "tts.provider" must be "google" (default), "edge" or "fish" (got ${JSON.stringify(provider)})`);
const googleTts = provider === 'google' ? { voice: script.tts?.voice || 'ko-KR-Chirp3-HD-Enceladus', lang: script.tts?.lang || 'ko-KR', gcloud: script.tts?.gcloud || process.env.GCLOUD_BIN || 'gcloud' } : null;
const edgeTts = provider === 'edge' ? { voice: script.tts.voice || 'ko-KR-InJoonNeural', bin: script.tts.bin || process.env.EDGE_TTS_BIN || 'edge-tts' } : null;
const apiKey = findSetting(['FISH_API_KEY', 'FISH_AUDIO_API_KEY']);
if (googleTts) { cfg.voice = 'google:' + googleTts.voice; FOUND.FISH_VOICE = `Google TTS voice ${googleTts.voice}`; FOUND.FISH_API_KEY = 'not needed (gcloud login)'; }
else if (edgeTts) { cfg.voice = 'edge:' + edgeTts.voice; FOUND.FISH_VOICE = `edge-tts voice ${edgeTts.voice}`; FOUND.FISH_API_KEY = 'not needed (edge-tts)'; }
else if (cfg.voice) FOUND.FISH_VOICE = 'script.json "voice"';
else cfg.voice = findSetting(['FISH_VOICE']) || '';
// real narration only with the user's own voice id AND key — never guess, borrow or default a voice
const missing = (edgeTts || googleTts) ? [] : [!cfg.voice && `the user's Fish Audio voice model id ("voice" in script.json, or FISH_VOICE=<id> in the skill's own .env: ${SKILL_ENV})`,
  !apiKey && `the user's Fish Audio API key (FISH_API_KEY=<key> in the skill's own .env: ${SKILL_ENV} — git-ignored, where the user's keys live; also read from the environment or a .env in the project or a parent folder)`].filter(Boolean);
if (missing.length && !opt.placeholder && !silent) {
  die(
    `Narration is made only with the user's own Fish Audio voice and key. Missing:\n  - ${missing.join('\n  - ')}\n` +
      '  The user didn\'t give them: make the video without narration ("narration": false in script.json), or, if they\n' +
      '  asked for a voiced video, ask for both and meanwhile build with --placeholder (temporary).',
    2,
  );
}

// ---------- audio helpers ----------
function wavBuffer(samples) {
  const data = Buffer.from(samples.buffer, samples.byteOffset, samples.byteLength);
  const h = Buffer.alloc(44);
  h.write('RIFF', 0);
  h.writeUInt32LE(36 + data.length, 4);
  h.write('WAVE', 8);
  h.write('fmt ', 12);
  h.writeUInt32LE(16, 16);
  h.writeUInt16LE(1, 20); // PCM
  h.writeUInt16LE(1, 22); // mono
  h.writeUInt32LE(SR, 24);
  h.writeUInt32LE(SR * 2, 28);
  h.writeUInt16LE(2, 32);
  h.writeUInt16LE(16, 34);
  h.write('data', 36);
  h.writeUInt32LE(data.length, 40);
  return Buffer.concat([h, data]);
}

/** Fish returns raw 16-bit LE PCM for format "pcm"; tolerate a WAV header just in case. */
function toSamples(buf) {
  if (buf.length >= 12 && buf.toString('ascii', 0, 4) === 'RIFF' && buf.toString('ascii', 8, 12) === 'WAVE') {
    let p = 12;
    while (p + 8 <= buf.length) {
      const id = buf.toString('ascii', p, p + 4);
      const size = buf.readUInt32LE(p + 4);
      if (id === 'data') {
        buf = buf.subarray(p + 8, Math.min(buf.length, p + 8 + (size || buf.length)));
        break;
      }
      p += 8 + size + (size & 1);
    }
  }
  const even = buf.length - (buf.length % 2);
  const copy = Buffer.from(buf.subarray(0, even));
  return new Int16Array(copy.buffer, copy.byteOffset, even / 2);
}

/** Rough speaking-time estimate for placeholders and the duration check, for any script: Korean ≈ 5.2 syllables/s,
 *  Japanese/Chinese ≈ 6 characters/s; words of other scripts by length (an English-length word ≈ 0.38 s, ≈ 2.6 words/s),
 *  scripts written without spaces (Thai, Lao, Khmer, Myanmar) per letter. */
const CJK = /[\p{Script=Hangul}\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}ー]/gu;
const NO_SPACES = /[\p{Script=Thai}\p{Script=Lao}\p{Script=Khmer}\p{Script=Myanmar}]/u;
function estimateSeconds(say) {
  let pause = 0;
  for (const tag of say.match(/\[[^\]]*\]/g) || []) {
    if (/long-break/i.test(tag)) pause += 0.9;
    else if (/break/i.test(tag)) pause += 0.35;
  }
  const s = stripTags(say).normalize('NFC');
  const count = (re) => (s.match(re) || []).length;
  let words = 0;   // letters with their combining marks (accents, matras, Thai vowels) stay one word; it's / l’heure too
  for (const w of s.replace(CJK, ' ').match(/[\p{L}\p{M}]+(?:['’][\p{L}\p{M}]+)*/gu) || []) {
    const n = (w.match(/\p{L}/gu) || []).length;
    if (n) words += NO_SPACES.test(w) ? n * 0.075 : 0.12 + n * 0.055;
  }
  const secs =
    count(/[가-힣]/g) / 5.2 +
    words +
    count(/\p{Nd}/gu) * 0.3 +
    count(/[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}ー]/gu) / 6 +
    count(/[,、，،]/g) * 0.2 +
    count(/[.!?。！？…؟।॥]/g) * 0.35;
  return Math.max(0.6, secs + pause + 0.15);
}

// ---------- synthesis ----------
const cacheDir = path.join(dir, '.tts-cache');
fs.mkdirSync(cacheDir, { recursive: true });

// v 2: the take exactly as Fish Audio returned it. v 1: a take cached before 2026-11-09, stored after this script had cut
// its edges (−38 dBFS) — still used when there is no v 2 take, so nothing already paid for is recorded again
function cacheKey(c, v = 2) {
  const p = {
    v,
    model: cfg.model,
    voice: cfg.voice,
    say: c.say,
    speed: 1,   // always 1 (kept in the key so the takes recorded before the rule stay valid)
    temperature: cfg.temperature,
    top_p: cfg.top_p,
    sr: SR,
  };
  return crypto.createHash('sha256').update(JSON.stringify(p)).digest('hex').slice(0, 24);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
// the video project whose generated.json records what this run writes (dub/<lang> is part of the project above it)
const projectRoot = () => projectOf(dir) || dir;

async function synthesizeEdge(c) {
  const tmp = path.join(cacheDir, `_edge_${c.id}.mp3`);
  const r1 = spawnSync(edgeTts.bin, ['-v', edgeTts.voice, '-t', stripTags(c.say), '--write-media', tmp], { encoding: 'utf8' });
  if (r1.error || r1.status !== 0) throw new Error(`edge-tts failed for ${c.id}: ${(r1.error && r1.error.message) || r1.stderr}`);
  const r2 = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', tmp, '-f', 's16le', '-ac', '1', '-ar', String(SR), '-'], { maxBuffer: 1 << 28 });
  fs.rmSync(tmp, { force: true });
  if (r2.error || r2.status !== 0) throw new Error(`ffmpeg failed for ${c.id}`);
  return toSamples(r2.stdout);
}

let gTok = null;
function googleAuth() {
  if (gTok) return gTok;
  const a = spawnSync(googleTts.gcloud, ['auth', 'print-access-token'], { encoding: 'utf8' });
  const p = spawnSync(googleTts.gcloud, ['config', 'get', 'project'], { encoding: 'utf8' });
  if (a.error || a.status !== 0 || !a.stdout.trim()) throw new Error('gcloud auth print-access-token failed — run: gcloud auth login');
  gTok = { token: a.stdout.trim(), project: (p.stdout || '').trim() };
  return gTok;
}
async function synthesizeGoogle(c) {
  const { token, project } = googleAuth();
  // Google Chirp 3 HD takes pause tags ([pause short] / [pause] / [pause long]) only as "markup" input: keep those, strip the rest
  const PAUSE_TAG = /\[(pause(?: short| long)?)\]/g;
  const input = PAUSE_TAG.test(c.say)
    ? { markup: stripTags(c.say.replace(PAUSE_TAG, '{{$1}}')).replace(/\{\{(pause(?: short| long)?)\}\}/g, '[$1]') }
    : { text: stripTags(c.say) };
  const body = { input, voice: { languageCode: googleTts.lang, name: googleTts.voice }, audioConfig: { audioEncoding: 'MP3' } };
  for (let attempt = 1; ; attempt++) {
    const res = await fetch('https://texttospeech.googleapis.com/v1/text:synthesize', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token, 'x-goog-user-project': project, 'Content-Type': 'application/json; charset=utf-8' },
      body: JSON.stringify(body), signal: AbortSignal.timeout(120_000),
    }).catch((e) => ({ ok: false, status: 0, text: async () => e.message }));
    if (res.ok) {
      const j = await res.json();
      const tmp = path.join(cacheDir, `_g_${c.id}.mp3`);
      fs.writeFileSync(tmp, Buffer.from(j.audioContent, 'base64'));
      const r2 = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', tmp, '-f', 's16le', '-ac', '1', '-ar', String(SR), '-'], { maxBuffer: 1 << 28 });
      fs.rmSync(tmp, { force: true });
      if (r2.error || r2.status !== 0) throw new Error(`ffmpeg failed for ${c.id}`);
      return toSamples(r2.stdout);
    }
    const detail = (await res.text().catch(() => '')).slice(0, 300);
    if ([429, 500, 503].includes(res.status) && attempt < 4) { await sleep(2000 * 2 ** (attempt - 1)); continue; }
    throw new Error(`Google TTS HTTP ${res.status} ${detail}`);
  }
}

async function synthesize(c) {
  if (googleTts) return synthesizeGoogle(c);
  if (edgeTts) return synthesizeEdge(c);
  const body = {
    text: c.say,
    reference_id: cfg.voice,
    format: 'pcm',
    sample_rate: SR,
    latency: 'normal',
    temperature: cfg.temperature,
    top_p: cfg.top_p,
    prosody: { speed: 1, volume: 0 },
  };
  for (let attempt = 1; ; attempt++) {
    let res;
    try {
      res = await fetch(API, {
        method: 'POST',
        headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json', model: cfg.model },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(180_000),
      });
    } catch (err) {
      if (attempt >= 4) throw new Error(`network error: ${err.message}`);
      await sleep(2000 * 2 ** (attempt - 1));
      continue;
    }
    if (res.ok) return toSamples(Buffer.from(await res.arrayBuffer()));
    const detail = (await res.text().catch(() => '')).slice(0, 300);
    if (res.status === 401) throw new Error('401 unauthorized — FISH_API_KEY is invalid');
    if (res.status === 402) throw new Error('402 payment required — the Fish Audio account is out of credit');
    if ([429, 500, 502, 503, 504].includes(res.status) && attempt < 4) {
      await sleep(2000 * 2 ** (attempt - 1));
      continue;
    }
    throw new Error(`HTTP ${res.status} ${detail}`);
  }
}

let fresh = 0;
let cached = 0;
let placeholders = 0;

// the voice is recorded only when the user decided to (--approved: after reviewing the finished video, or they asked for
// these takes); until then new cues get placeholders and the video is finished on them
const approved = opt.approved === true;
if ((opt.force || only) && !approved && !silent && !opt.placeholder) {
  die('--force / --only record new takes: add --approved only once the user has decided to record (after reviewing the finished video) or asked for this re-take');
}
let unapproved = 0;

async function takeFor(c) {
  const key = cacheKey(c);
  const file = path.join(cacheDir, key + '.pcm');
  const oldKey = cacheKey(c, 1), oldFile = path.join(cacheDir, oldKey + '.pcm');
  const wantNew = opt.force || (only && only.has(c.id));
  // no narration by choice: silent, timed by estimated reading — never a cached voice take
  if (silent) return { samples: new Int16Array(Math.round(estimateSeconds(c.say) * SR)), placeholder: false, silent: true, key };
  if (!wantNew && fs.existsSync(file)) {
    cached++;
    return { samples: toSamples(fs.readFileSync(file)), placeholder: false, key, asRecorded: true };
  }
  if (!wantNew && fs.existsSync(oldFile)) {
    cached++;
    return { samples: toSamples(fs.readFileSync(oldFile)), placeholder: false, key: oldKey };
  }
  if (opt.placeholder || !approved) {
    placeholders++;
    if (!opt.placeholder) unapproved++;
    return { samples: new Int16Array(Math.round(estimateSeconds(c.say) * SR)), placeholder: true, key };
  }
  const samples = await synthesize(c);   // kept exactly as received: what (if anything) comes out is the agent's call
  if (!samples.length) throw new Error(`cue ${c.id}: Fish Audio returned no audio`);
  // local (SOURCE.md): a re-take of an unchanged say has the same key; keep the take it replaces, so the take a review
  // note was about can still be measured later (PN c12, 2026-11-20: the take heard as too fast was overwritten)
  if (fs.existsSync(file)) {
    const keep = path.join(cacheDir, 'replaced'); fs.mkdirSync(keep, { recursive: true });
    fs.renameSync(file, path.join(keep, `${key}.${c.id}.${new Date().toISOString().replace(/[:.]/g, '-')}.pcm`));
  }
  fs.writeFileSync(file, Buffer.from(samples.buffer, samples.byteOffset, samples.byteLength));
  freshFiles.push(file);
  fresh++;
  process.stdout.write(`  ✓ ${c.id} (${(samples.length / SR).toFixed(2)}s)\n`);
  return { samples, placeholder: false, key, asRecorded: true };
}

/** fn over items, `limit` at a time. After a failure no new item starts, but the ones in flight finish (their takes are
 *  paid for and get cached); then it throws with every distinct error. */
async function mapLimit(items, limit, fn) {
  const out = new Array(items.length);
  const errors = [];
  let next = 0;
  const worker = async () => {
    while (next < items.length && !errors.length) {
      const i = next++;
      try {
        out[i] = await fn(items[i], i);
      } catch (err) {
        errors.push(err);
      }
    }
  };
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker));
  if (errors.length) throw new Error([...new Set(errors.map((e) => e.message))].join('\n  '));
  return out;
}

// a cut's shape is checked before any take is asked for, so a mistake in it stops the run before credits are spent;
// whether its ranges lie inside the take is checked once the take is there (applyCut)
const FADE = Math.round(0.01 * SR);
for (const c of cues) {
  if (c.cut == null) continue;
  const k = c.cut;
  const isRange = (r) => Array.isArray(r) && r.length === 2 && r.every((x) => typeof x === 'number' && Number.isFinite(x));
  if (!k || typeof k !== 'object' || typeof k.take !== 'string' || !Array.isArray(k.ranges) || !k.ranges.every(isRange)) {
    die(`cue ${c.id}: "cut" must be { "take": "<take id>", "ranges": [[from, to], …] } with the times as numbers (seconds in the take)`);
  }
  const rs = k.ranges.map(([a, b]) => [a, b]).sort((x, y) => x[0] - y[0]);
  rs.forEach(([a, b], i) => {
    if (!(a >= 0 && b > a)) die(`cue ${c.id}: cut [${a}, ${b}] is not a stretch (from ≥ 0, to > from)`);
    if (i && a < rs[i - 1][1]) die(`cue ${c.id}: cut ranges overlap ([${rs[i - 1]}] and [${a}, ${b}])`);
    if (Math.round((b - a) * SR) <= FADE) die(`cue ${c.id}: cut [${a}, ${b}] is shorter than its 10 ms crossfade`);
  });
}

// ---------- paragraph recording (Google only): several cues in one request, so the voice keeps one pace ----------
// script.json "tts": { …, "paragraphs": 5 } groups up to 5 consecutive cues per request (never over 4,500 bytes of text);
// "paragraphs": [["a01","a02"], ["b01", …], …] names the groups (consecutive cues, every cue once). Measured on PN part 4
// (2026-11-22): line-to-line pace sd 0.49 → 0.19 syllables/s, adjacent jumps ≥ 0.8 syl/s 3 → 0 (local, SOURCE.md; references/narration.md).
// A paragraph take is cut into one take per cue at the split times: script.json "splits": { "<paragraph take id>":
// [t1, t2, …] } — seconds in the paragraph take where each cue after the first starts. Without them this script PROPOSES
// splits (in the middle of the longest pause near where the cue's syllables should end) and says so: they are a guess,
// confirmed by the agent with phrasing-check.mjs (each cue's pieces must start and end with that cue's own words) and
// written into "splits". Each cue's piece is then an ordinary take (.tts-cache/<take>.pcm) that "cut", "at", wave.mjs,
// sync.mjs and check.mjs use as before. Changing a split gives the cues new take ids (their cuts must be set again).
// --only <id> takes the cue's whole paragraph again: every cue in it gets a new reading.
const paraSetting = googleTts ? script.tts?.paragraphs : null;
if (script.tts?.paragraphs != null && !googleTts) die('"tts.paragraphs" works with the Google voice only');
const paraMode = paraSetting != null && paraSetting !== false && !silent;
const PARA_BYTES = 4500;
function paragraphGroups() {
  const ids = cues.map((c) => c.id);
  if (Array.isArray(paraSetting)) {
    const flat = paraSetting.flat();
    if (flat.length !== ids.length || flat.some((id, i) => id !== ids[i])) die('"tts.paragraphs": the groups must list every cue once, in script order');
    return paraSetting.map((g) => g.map((id) => cues[ids.indexOf(id)]));
  }
  const max = Number.isInteger(paraSetting) && paraSetting > 0 ? paraSetting : 5;
  const out = [];
  let cur = [];
  for (const c of cues) {
    const bytes = Buffer.byteLength([...cur, c].map((x) => x.say).join(' '));
    if (cur.length && (cur.length >= max || bytes > PARA_BYTES)) { out.push(cur); cur = []; }
    cur.push(c);
  }
  if (cur.length) out.push(cur);
  for (const g of out) if (Buffer.byteLength(g.map((x) => x.say).join(' ')) > PARA_BYTES) die(`paragraph ${g[0].id}…: over ${PARA_BYTES} bytes — make it smaller`);
  return out;
}
const paraKey = (g) => crypto.createHash('sha256').update(JSON.stringify({ v: 'para1', voice: cfg.voice, says: g.map((c) => c.say), sr: SR })).digest('hex').slice(0, 24);
const sylCount = (s) => (stripTags(s).match(/[가-힣]/g) || []).length || stripTags(s).replace(/\s+/g, '').length;
/** proposal only: per 10 ms frame the level; voice = within 35 dB of the loudest frame; a pause = 150 ms or more without it */
function proposeSplits(samples, g) {
  const h = Math.round(SR * 0.01), F = Math.floor(samples.length / h), db = new Float64Array(F);
  for (let f = 0; f < F; f++) { let s = 0; for (let j = f * h; j < (f + 1) * h; j++) s += (samples[j] / 32768) ** 2; db[f] = 10 * Math.log10(s / h + 1e-18); }
  const top = Math.max(...db), v = Array.from(db, (x) => x > top - 35);
  const first = v.indexOf(true), last = v.lastIndexOf(true), pauses = [];
  for (let f = first; f <= last; f++) if (!v[f]) { let e = f; while (!v[e]) e++; if (e - f >= 15) pauses.push([f, e]); f = e; }
  const voicedBefore = (f) => { let n = 0; for (let k = first; k < f; k++) if (v[k]) n++; return n; };
  const total = voicedBefore(last + 1), syl = g.map((c) => sylCount(c.say)), all = syl.reduce((a, b) => a + b, 0);
  const out = [];
  let acc = 0, floor = first;
  for (let k = 0; k < g.length - 1; k++) {
    acc += syl[k];
    const want = (acc / all) * total;
    const near = pauses.filter(([a]) => a > floor).map((p) => ({ p, off: Math.abs(voicedBefore(p[0]) - want) }));
    if (!near.length) die(`paragraph ${g[0].id}…: no pause found for the split after ${g[k].id} — set "splits" by hand (wave.mjs)`);
    const inWin = near.filter((x) => x.off < 120);
    const pick = (inWin.length ? inWin.sort((a, b) => (b.p[1] - b.p[0]) - (a.p[1] - a.p[0])) : near.sort((a, b) => a.off - b.off))[0].p;
    out.push(Math.round(((pick[0] + pick[1]) / 2) * h) / SR);
    floor = pick[1];
  }
  return out.map((t) => Math.round(t * 1000) / 1000);
}
const proposed = [];
async function paragraphTakes() {
  const groups = paragraphGroups(), out = new Array(cues.length);
  const splitsSet = script.splits || {};
  await mapLimit(groups, 2, async (g) => {
    const pk = paraKey(g), file = path.join(cacheDir, pk + '.pcm');
    const wantNew = opt.force || (only && g.some((c) => only.has(c.id)));
    let samples;
    if (!wantNew && fs.existsSync(file)) { cached++; samples = toSamples(fs.readFileSync(file)); }
    else if (opt.placeholder || !approved) {
      for (const c of g) { placeholders++; if (!opt.placeholder) unapproved++; out[cues.indexOf(c)] = { samples: new Int16Array(Math.round(estimateSeconds(c.say) * SR)), placeholder: true, key: null }; }
      return;
    } else {
      if (fs.existsSync(file)) {   // keep the paragraph take a re-take replaces (as for single takes)
        const keep = path.join(cacheDir, 'replaced'); fs.mkdirSync(keep, { recursive: true });
        fs.renameSync(file, path.join(keep, `${pk}.${g[0].id}.${new Date().toISOString().replace(/[:.]/g, '-')}.pcm`));
      }
      samples = await synthesizeGoogle({ id: `${g[0].id}…${g[g.length - 1].id}`, say: g.map((c) => c.say).join(' ') });
      if (!samples.length) throw new Error(`paragraph ${g[0].id}…: Google returned no audio`);
      fs.writeFileSync(file, Buffer.from(samples.buffer, samples.byteOffset, samples.byteLength));
      freshFiles.push(file); fresh++;
      process.stdout.write(`  ✓ paragraph ${g.map((c) => c.id).join(' ')} (${(samples.length / SR).toFixed(2)}s)\n`);
    }
    let sp = splitsSet[pk];
    const dur = samples.length / SR;
    if (sp != null) {
      if (!Array.isArray(sp) || sp.length !== g.length - 1 || sp.some((t, i) => typeof t !== 'number' || t <= 0 || t >= dur || (i && t <= sp[i - 1])))
        die(`"splits" for paragraph ${pk} (${g[0].id}…): ${g.length - 1} increasing times inside the take (0 – ${dur.toFixed(3)} s) are needed`);
    } else { sp = proposeSplits(samples, g); proposed.push({ pk, ids: g.map((c) => c.id), sp }); }
    const edges = [0, ...sp.map((t) => Math.round(t * SR)), samples.length];
    g.forEach((c, k) => {
      const piece = samples.slice(edges[k], edges[k + 1]);
      const key = crypto.createHash('sha256').update(JSON.stringify({ v: 'piece1', para: pk, k, from: edges[k], to: edges[k + 1] })).digest('hex').slice(0, 24);
      const pf = path.join(cacheDir, key + '.pcm');
      if (!fs.existsSync(pf)) { fs.writeFileSync(pf, Buffer.from(piece.buffer, piece.byteOffset, piece.byteLength)); freshFiles.push(pf); }
      out[cues.indexOf(c)] = { samples: piece, placeholder: false, key, asRecorded: true, para: pk };
    });
  });
  return out;
}

const freshFiles = [];   // takes synthesized in this run — recorded in generated.json as soon as the synthesis ends,
let takes;               // whether it succeeded or not, so nothing that stops the run later leaves a paid take unrecorded
try {
  takes = paraMode ? await paragraphTakes() : await mapLimit(cues, 3, takeFor);
} catch (err) {
  if (freshFiles.length) recordGenerated(freshFiles, 'tts.mjs');
  die(err.message + (fresh ? `\n  ${fresh} new take(s) recorded before it are cached in .tts-cache — the next run reuses them (no new charge)` : ''));
}
if (freshFiles.length) recordGenerated(freshFiles, 'tts.mjs');
// the cached takes this script uses that have no record (cached before generated.json was kept): listed, and recorded
// only with --record-cache
const cacheFile = (t) => path.join(cacheDir, t.key + '.pcm');
let unrecorded = [];
{
  let rec = { files: {} };
  try { rec = readRecord(projectRoot()); } catch { /* an unreadable generated.json: check.mjs reports it */ }
  unrecorded = [...new Set(takes.filter((t) => !t.placeholder && !t.silent && fs.existsSync(cacheFile(t))).map(cacheFile))]
    .filter((f) => !rec.files[path.relative(projectRoot(), f).split(path.sep).join('/')]);   // (a take changed since its record: check.mjs reports it)
}
if (unrecorded.length && opt['record-cache']) {
  recordGenerated(unrecorded, 'tts.mjs (--record-cache)');
  console.log(`• --record-cache: recorded ${unrecorded.length} cached take(s) of this script's cues in generated.json`);
  unrecorded = [];
}

// ---------- cuts: the stretches the agent chose to take out of a take (script.json "cut") ----------
// (their shape was checked before the takes; here only that they lie inside this take)
function applyCut(samples, ranges, id) {
  const rs = ranges.map(([a, b]) => [a, b]).sort((x, y) => x[0] - y[0]);
  const N = samples.length, dur = N / SR;
  // (wave.mjs prints the take's length to the millisecond: an end written as that length is the end)
  for (const [a, b] of rs) if (b > dur + 0.0005) die(`cue ${id}: cut [${a}, ${b}] reaches past the end of the take (0 – ${dur.toFixed(3)} s)`);
  // kept parts: before the first range, between ranges, after the last — a range from 0 or up to the end leaves nothing
  // of itself; at each join between two kept parts the earlier one runs FADE samples on and crossfades into the next
  const kept = [];
  let from = 0;
  for (const [a, b] of rs) {
    const s0 = Math.min(N, Math.round(a * SR)), e0 = Math.min(N, Math.round(b * SR));
    if (s0 > from) kept.push([from, s0]);
    from = Math.max(from, e0);
  }
  if (from < N) kept.push([from, N]);
  if (!kept.length) die(`cue ${id}: the cut takes out the whole take`);
  const parts = kept.map(([s0, e0], i) => [s0, i < kept.length - 1 ? Math.min(N, e0 + FADE) : e0]);
  const out = new Int16Array(parts.reduce((n, [s, e]) => n + (e - s), 0) - FADE * (parts.length - 1));
  let o = 0;
  parts.forEach(([s, e], i) => {
    for (let j = s; j < e; j++) {
      const k = j - s;
      if (i > 0 && k < FADE) { const g = k / FADE; out[o - FADE + k] = Math.round(out[o - FADE + k] * (1 - g) + samples[j] * g); }
      else out[o + k - (i > 0 ? FADE : 0)] = samples[j];
    }
    o += (e - s) - (i > 0 ? FADE : 0);
  });
  return out;
}
const cutsApplied = [];
cues.forEach((c, i) => {
  const t = takes[i];
  if (c.cut == null) return;
  if (t.placeholder || t.silent) { console.warn(`⚠ ${c.id}: "cut" is set but the cue has no recorded take — not applied`); return; }
  if (c.cut.take !== t.key) { console.warn(`⚠ ${c.id}: "cut" was set on take ${c.cut.take}, the take now is ${t.key} — not applied; read this take (node wave.mjs <dir> --cue ${c.id}) and set it again`); return; }
  if (!c.cut.ranges.length) return;
  const before = t.samples.length;
  t.samples = applyCut(t.samples, c.cut.ranges, c.id);
  t.cut = c.cut.ranges.map(([a, b]) => [a, b]).sort((x, y) => x[0] - y[0]);
  cutsApplied.push(`${c.id} −${((before - t.samples.length) / SR).toFixed(2)} s`);
});

// a take kept as recorded with no "cut" for it yet: nobody has read it — what comes out of it (its edges included) is
// the agent's call, never this script's
const unreviewed = [];
cues.forEach((c, i) => {
  const t = takes[i];
  if (t.asRecorded && !(c.cut && c.cut.take === t.key)) { t.unreviewed = true; unreviewed.push(c.id); }
});

// ---------- timeline ----------
const r3 = (x) => Math.round(x * 1000) / 1000;
let cursor = cfg.leadIn;
const timeline = cues.map((c, i) => {
  const duration = r3(takes[i].samples.length / SR);
  const start = r3(cursor);
  const end = r3(start + duration);
  cursor = end + (c.gapAfter ?? cfg.gap);
  const cueOut = { id: c.id, text: c.text ? String(c.text) : stripTags(c.say), say: c.say, start, end, duration };
  if (takes[i].placeholder) cueOut.placeholder = true;   // silent placeholder, estimated timing (sync/check skip it)
  if (!takes[i].silent && !takes[i].placeholder) cueOut.take = takes[i].key;   // the recorded take's id (.tts-cache/<take>.pcm): a cut names it
  if (takes[i].asRecorded) cueOut.asRecorded = true;     // the take is kept exactly as Fish Audio returned it
  if (takes[i].unreviewed) cueOut.unreviewed = true;     // …and has no cut for it yet: the agent has not read it
  if (takes[i].cut) cueOut.cut = takes[i].cut;           // the stretches taken out of it (seconds in the take as recorded)
  if (Array.isArray(c.captions) && c.captions.length) cueOut.captions = c.captions.map(String); // one-line caption segments, chosen by hand
  return cueOut;
});
const audioDuration = timeline[timeline.length - 1].end;
const duration = r3(audioDuration + cfg.tail);

// a recorded cue must not turn silent behind anyone's back (exact: by take ids and files, nothing guessed) — e.g. the voice
// id was not found this time, so every cache key changed and every recorded cue would become a placeholder
{
  const prevFile = path.join(dir, 'js', 'cues.js');
  if (fs.existsSync(prevFile) && !opt.force && !opt['drop-takes']) {
    let prev = null;
    try { const box = { window: {} }; vm.runInNewContext(fs.readFileSync(prevFile, 'utf8'), box); prev = box.window.VIDEO_DATA; } catch { /* unreadable: nothing to compare */ }
    const lost = prev ? cues.filter((c, i) => {
      const p = (prev.cues || []).find((x) => x.id === c.id);
      return p && p.take && p.say === c.say && takes[i].placeholder && fs.existsSync(path.join(cacheDir, p.take + '.pcm'));
    }).map((c) => c.id) : [];
    if (lost.length) {
      die(`${lost.length} recorded cue(s) would turn into silent placeholders: ${lost.slice(0, 8).join(', ')}${lost.length > 8 ? ' …' : ''}. ` +
        `js/cues.js names their takes and the takes are in .tts-cache, but this run's settings give them other cache keys — the voice id, ` +
        `model, temperature or top_p differ from what they were recorded with (voice ${cfg.voice ? `from ${FOUND.FISH_VOICE}` : 'not found'}). ` +
        'Nothing was written. Run with the settings they were recorded with; if the change is meant, record them anew (--approved --force) or pass --drop-takes.');
    }
  }
}

// ---------- write audio ----------
const audioDir = path.join(dir, 'audio');
const cueDir = path.join(audioDir, 'cues');
fs.mkdirSync(cueDir, { recursive: true });
for (const f of fs.readdirSync(cueDir)) if (f.endsWith('.wav')) fs.unlinkSync(path.join(cueDir, f));

const mix = new Int16Array(Math.ceil(audioDuration * SR) + 1);
timeline.forEach((c, i) => {
  const s = takes[i].samples;
  fs.writeFileSync(path.join(cueDir, `${c.id}.wav`), wavBuffer(s));
  mix.set(s.subarray(0, Math.max(0, mix.length - Math.round(c.start * SR))), Math.round(c.start * SR));
});
const wavPath = path.join(audioDir, 'narration.wav');
const mp3Path = path.join(audioDir, 'narration.mp3');
fs.writeFileSync(wavPath, wavBuffer(mix));
if (fs.existsSync(mp3Path)) fs.unlinkSync(mp3Path);

let runtimeAudio = 'audio/narration.wav';
const ff = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', wavPath, '-codec:a', 'libmp3lame', '-b:a', '192k', mp3Path]);
if (!ff.error && ff.status === 0) runtimeAudio = 'audio/narration.mp3';
else console.warn('⚠ ffmpeg unavailable or failed — the player will use narration.wav');
recordGenerated([...timeline.map((c) => path.join(cueDir, `${c.id}.wav`)), wavPath, ...(fs.existsSync(mp3Path) ? [mp3Path] : [])], 'tts.mjs');

// ---------- write js/cues.js ----------
const data = {
  title: script.title || '',
  lang: script.lang || 'ko',
  audio: runtimeAudio,
  audioDuration,
  duration,
  leadIn: cfg.leadIn,
  tail: cfg.tail,
  placeholder: takes.some((t) => t.placeholder),   // any cue a placeholder (each one has placeholder: true)
  narration: !silent,
  voice: silent ? '' : cfg.voice,
  model: cfg.model,
  scriptSig: scriptSignature(script),   // script.json as this file was built from it (check.mjs: re-run tts.mjs on a change)
  cues: timeline,
};
fs.mkdirSync(path.join(dir, 'js'), { recursive: true });
fs.writeFileSync(
  path.join(dir, 'js', 'cues.js'),
  '// Generated by tts.mjs from script.json — edit script.json and re-run instead of editing this file.\n' +
    `window.VIDEO_DATA = ${JSON.stringify(data, null, 2)};\n`,
);

// ---------- write script.txt: the script text only (no ids, no times), one cue per line ----------
fs.writeFileSync(path.join(dir, 'script.txt'), timeline.map((c) => c.text.replace(/\s+/g, ' ').trim()).join('\n') + '\n');

// ---------- report ----------
const clip = (s, n) => (s.length > n ? s.slice(0, n - 1) + '…' : s);
console.log('');
for (const c of timeline) {
  console.log(`${c.id.padEnd(6)} ${c.start.toFixed(2).padStart(7)} → ${c.end.toFixed(2).padStart(7)}  (${c.duration.toFixed(2)}s)  ${clip(c.text, 60)}`);
}
console.log('');
console.log(
  `narration ${runtimeAudio} ${audioDuration.toFixed(2)}s · video ${duration.toFixed(2)}s · ` +
    `${cues.length} cues (${fresh} new, ${cached} cached${placeholders ? `, ${placeholders} PLACEHOLDER` : ''})`,
);
if (unrecorded.length) console.log(`⚠ ${unrecorded.length} cached take(s) this script uses have no record in generated.json (cached before the tools kept it) — check.mjs refuses them. Ask the user; with their OK run once: node tts.mjs ${opt._[0] || '.'} --record-cache`);
if (proposed.length) {
  console.log(`🧩 ${proposed.length} paragraph take(s) split at PROPOSED times (a guess from pauses and syllable counts) — confirm each with phrasing-check.mjs (every cue's pieces must start and end with its own words), then write them into script.json "splits" (adjust where a word landed in the wrong cue):`);
  for (const p of proposed) console.log(`   "${p.pk}": ${JSON.stringify(p.sp)}   // ${p.ids.join(' ')}`);
}
if (cutsApplied.length) console.log(`✂ cuts (script.json "cut") applied: ${cutsApplied.join(', ')}`);
if (unreviewed.length) console.log(`👂 ${unreviewed.length} take(s) not read yet (${unreviewed.join(', ')}): kept exactly as recorded, with whatever the TTS put before, between and after the words. Where the silence is, and what comes out, is yours to decide — read them: node wave.mjs ${opt._[0] || '.'} --unreviewed, then set each cue's "cut" in script.json ("ranges": [] when nothing goes) and run tts.mjs again (references/sound.md §1). check.mjs refuses the hand-off until every take has its cut.`);
if (silent) console.log(`· no narration ("narration": false): silent audio, each cue timed by its estimated reading time. To voice it later: set "narration": true and run tts.mjs again${googleTts ? ' (Google TTS needs only a gcloud login)' : edgeTts ? '' : ' with the user\'s Fish Audio voice id + API key'} — the scenes follow the new timings.`);
// whether the user's key and voice are available is decided here, by this search — never by looking at one .env file
if (googleTts) console.log(`🔑 Google Cloud TTS: voice ${googleTts.voice} (default provider), no key — signs in with \`${googleTts.gcloud} auth print-access-token\` and the gcloud default project; if it fails: gcloud auth login`);
else if (edgeTts) console.log(`🔑 edge-tts: voice ${edgeTts.voice}, no key`);
else if (apiKey && cfg.voice) console.log(`🔑 Fish Audio key and voice: available — key from ${FOUND.FISH_API_KEY}, voice from ${FOUND.FISH_VOICE}${silent ? '. "narration": false is for a user WITHOUT them: this video can be voiced — set "narration": true (the recording still waits for the user)' : ''}`);
else console.log(`🔑 Fish Audio ${[!apiKey && 'key', !cfg.voice && 'voice'].filter(Boolean).join(' and ')}: not found (looked in the environment, ${dir}/.env and every parent folder's .env, ${SKILL_ENV}) — a video without narration unless the user gives them`);
if (unapproved) console.log(`⏸ ${unapproved} cue(s) not recorded yet: silent placeholders with estimated timing (placeholder: true in js/cues.js). Finish the whole video on them; the user reviews it and decides whether to record — only then: node tts.mjs <dir> --approved (the scenes follow the new timings; then read every new take with wave.mjs --unreviewed and set its cut, set the phrase times for when(), sync.mjs).`);
else if (placeholders) console.log('⚠ placeholder narration is silent with estimated timing — re-run without --placeholder' + (googleTts || edgeTts ? ' (and with --approved once the user decides to record).' : ' once the user has given their Fish Audio voice id and API key.'));
