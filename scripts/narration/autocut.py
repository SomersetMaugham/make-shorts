import json,sys,array,math,re
INTERIOR_SILENCE_DB = -45
proj=sys.argv[1]; ids=sys.argv[2].split(',')
cj=open(proj+'/js/cues.js').read(); data=json.loads(cj[cj.index('{'):cj.rindex('}')+1])
takes={c['id']:c.get('take') for c in data['cues']}
p=proj+'/script.json'; s=open(p).read(); d=json.loads(s)
for c in d['cues']:
  if c['id'] not in ids: continue
  t=takes[c['id']]; a=array.array('h',open(f'{proj}/.tts-cache/{t}.pcm','rb').read())
  sr=44100; n=441; db=[]
  for i in range(0,len(a)-n+1,n):
    q=sum(x*x for x in a[i:i+n])/n; db.append(-120 if q==0 else 10*math.log10(q/32768**2))
  L=len(a)/sr; sp=[k for k,v in enumerate(db) if v>-45]
  t0=sp[0]*0.01; t1=(sp[-1]+1)*0.01
  R=[]
  if t0-0.06>0.02: R.append([0,round(t0-0.06,2)])
  # interior silences (< -45 dB) longer than 0.35 s -> keep ~0.27
  st=None; gaps=[]
  for k in range(sp[0],sp[-1]+1):
    if db[k]<INTERIOR_SILENCE_DB: st=k if st is None else st
    else:
      if st is not None: gaps.append((st*0.01,k*0.01))
      st=None
  # local (SOURCE.md): a [pause] / [pause long] in say is a pause someone asked for. Chirp makes it the line's longest
  # silence, so the longest n gaps keep 0.55 s / 0.8 s instead of 0.27 (shrunk to 0.27 it was heard as no pause, PN n008)
  say=c.get('say',''); n_long=len(re.findall(r'\[pause long\]',say)); n_mid=len(re.findall(r'\[pause\]',say))
  keep={}
  for j,g in enumerate(sorted(gaps,key=lambda g:g[0]-g[1])[:n_long+n_mid]): keep[g]=0.8 if j<n_long else 0.55
  for a0,b0 in gaps:
    kp=keep.get((a0,b0),0.27)
    h0,h1=(0.13,0.14) if kp==0.27 else (kp/2,kp/2)
    if b0-a0>kp+0.08: R.append([round(a0+h0,2),round(b0-h1,2)])
  if L-(t1+0.10)>0.02: R.append([round(t1+0.10,2),round(L,3)])
  c['cut']={'take':t,'ranges':R}; print(c['id'],t,R)
open(p,'w').write(json.dumps(d,ensure_ascii=False,indent=2)+("\n" if s.endswith("\n") else ""))
