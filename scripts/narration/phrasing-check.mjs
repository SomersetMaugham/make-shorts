import { spawnSync } from 'node:child_process'; import fs from 'node:fs';
const [proj_dir, ...ids] = process.argv.slice(2);
const tok = spawnSync('gcloud',['auth','print-access-token'],{encoding:'utf8'}).stdout.trim();
const proj = spawnSync('gcloud',['config','get','project'],{encoding:'utf8'}).stdout.trim();
const cues = JSON.parse(fs.readFileSync(proj_dir+'/script.json','utf8')).cues;
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
  c._line=line;
}));
for (const c of cues) if (c._line!==undefined) console.log(`${c.id} 들림: ${c._line}\n    say: ${c.say}`);
