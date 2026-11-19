import json,sys,array,math,re
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
  # interior silences (< -50 dB) longer than 0.35 s -> keep ~0.27
  st=None
  for k in range(sp[0],sp[-1]+1):
    if db[k]<-50: st=k if st is None else st
    else:
      if st is not None:
        a0,b0=st*0.01,k*0.01
        if b0-a0>0.35: R.append([round(a0+0.13,2),round(b0-0.14,2)])
      st=None
  if L-(t1+0.10)>0.02: R.append([round(t1+0.10,2),round(L,3)])
  c['cut']={'take':t,'ranges':R}; print(c['id'],t,R)
open(p,'w').write(json.dumps(d,ensure_ascii=False,indent=2)+("\n" if s.endswith("\n") else ""))
