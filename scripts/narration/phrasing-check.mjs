import { spawnSync } from 'node:child_process'; import fs from 'node:fs';
import { judgeBreaks } from './lib/breaks.mjs';   // local: the verdict (SOURCE.md)
const [proj_dir, ...ids] = process.argv.slice(2);
const tok = spawnSync('gcloud',['auth','print-access-token'],{encoding:'utf8'}).stdout.trim();
const proj = spawnSync('gcloud',['config','get','project'],{encoding:'utf8'}).stdout.trim();
const cues = JSON.parse(fs.readFileSync(proj_dir+'/script.json','utf8')).cues;
const box = {}; try { new Function('window', fs.readFileSync(proj_dir+'/js/cues.js','utf8'))(box); } catch {}
const takes = new Map((box.VIDEO_DATA?.cues||[]).map(c=>[c.id,c.take||null]));
async function rec(buf){
  const r = await fetch(`https://us-central1-speech.googleapis.com/v2/projects/${proj}/locations/us-central1/recognizers/_:recognize`,{method:'POST',
    headers:{Authorization:'Bearer '+tok,'x-goog-user-project':proj,'Content-Type':'application/json'},
    body:JSON.stringify({config:{autoDecodingConfig:{},languageCodes:['ko-KR'],model:'chirp_2'},content:buf.toString('base64')})});
  const j=await r.json(); if(!r.ok) return 'ERR'+r.status;
  return (j.results||[]).map(x=>x.alternatives?.[0]?.transcript||'').join(' ').trim() || '∅';
}
await Promise.all(cues.filter(c=>!ids.length||ids.includes(c.id)).map(async c=>{
  const f=`${proj_dir}/audio/cues/${c.id}.wav`;
  const sd=spawnSync('ffmpeg',['-v','info','-i',f,'-af','silencedetect=n=-42dB:d=0.15','-f','null','-'],{encoding:'utf8'}).stderr;
  const dur=parseFloat(spawnSync('ffprobe',['-v','error','-show_entries','format=duration','-of','csv=p=0',f],{encoding:'utf8'}).stdout);
  const S=[...sd.matchAll(/silence_start: ([\d.]+)/g)].map(m=>+m[1]), E=[...sd.matchAll(/silence_end: ([\d.]+)/g)].map(m=>+m[1]);
  const gaps=S.map((s,i)=>[s,E[i]??dur]).filter(([s,e])=>s>0.05&&e<dur-0.05);
  const cuts=[0,...gaps.flatMap(g=>[g[0],g[1]]),dur]; const parts=[];
  for(let i=0;i<cuts.length;i+=2){
    const buf=spawnSync('ffmpeg',['-v','error','-i',f,'-ss',String(Math.max(0,cuts[i]-0.03)),'-to',String(cuts[i+1]+0.03),'-ar','16000','-ac','1','-f','wav','-'],{maxBuffer:1<<26}).stdout;
    parts.push(await rec(buf));
  }
  let line=parts[0]; gaps.forEach((g,i)=>{line+=` ‖${(g[1]-g[0]).toFixed(2)}‖ `+parts[i+1];});
  c._line=line; c._v=judgeBreaks(c.say, parts, gaps.map(g=>g[1]-g[0]), {noPause: !!c.noPause});
}));
// the verdict, kept in phrasing.json for check_narration.py (stale once the cue's take or cut changes)
const pj = proj_dir+'/phrasing.json'; const store = fs.existsSync(pj) ? JSON.parse(fs.readFileSync(pj,'utf8')) : {};
let bad = 0;
for (const c of cues) {
  if (c._line===undefined) continue;
  const v = c._v, m = v.missing.map(x=>`"${x.word}" ${x.got ? x.got+'s' : '쉼 없음'} (필요 ≥${x.need}s)`);
  const verdict = v.unknown ? `UNKNOWN (${v.unknown})` : m.length ? `MISSING ${m.join(', ')}` : 'ok';
  if (v.unknown || m.length) bad++;
  console.log(`${c.id} 들림: ${c._line}\n    say: ${c.say}\n    판정: ${verdict}`);
  store[c.id] = { take: takes.get(c.id) ?? null, cut: c.cut ?? null, say: c.say, missing: v.missing, unknown: v.unknown, heard: c._line };
}
fs.writeFileSync(pj, JSON.stringify(store, null, 1));
if (bad) { console.log(`\n✖ ${bad} cue(s) with a missing pause: tag the break in say (shorts.json), re-take with --only, recut, check again.`
  + ` A pause the user heard and accepted: "phrasingOk": true on the cue in script.json.`); process.exit(1); }
console.log('\nphrasing ok: every comma, tag and sentence end has its pause');
