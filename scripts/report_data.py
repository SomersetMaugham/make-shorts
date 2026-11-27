# Prints the numbers a short's report.md needs: the narration (provider, voice, every cue with its take, cut and phrase
# times), the runs, the mix and the final file's loudness, the picked thumbnail. usage: python scripts/report_data.py s3
import json, os, re, subprocess, sys

sk = sys.argv[1]
C = json.load(open('cut.json', encoding='utf-8'))[sk]; S = json.load(open('shorts.json', encoding='utf-8'))[sk]
nd = f'narration/{sk}'
script = json.load(open(f'{nd}/script.json', encoding='utf-8'))
N = C['narration']
print(f'# {sk}: {S["title"]}  cover={S.get("cover")}')
print(f'\n## narration: {N["provider"]} {N["voice"]}{" (model " + str(N["model"]) + ")" if N.get("model") and N["provider"] == "fish" else ""}'
      f' · leadIn {N.get("leadIn")} s · tail {N.get("tail")} s · {"PLACEHOLDERS" if N["placeholder"] else "recorded" if N["narration"] else "no narration"}')
sc = {c['id']: c for c in script['cues']}
print('id | start-end (s) | take | cut ranges (s in the take) | phrase times set ("at") | gapAfter | text / say')
for c in C['cues']:
    s = sc.get(c['id'], {})
    cut = (s.get('cut') or {}).get('ranges') if (s.get('cut') or {}).get('take') == c.get('take') else None
    at = (s.get('at') or {}).get('phrases') if (s.get('at') or {}).get('take') == c.get('take') else None
    print(f"{c['id']} | {c['start']:.3f}-{c['end']:.3f} | {c.get('take', 'placeholder' if c.get('placeholder') else '-')} | {cut} | "
          f"{at} | {s.get('gapAfter', script.get('gap'))} | {c.get('text')}" + (f" / say: {c['say']}" if c.get('say') and c['say'] != c.get('text') else ''))
est = sum(w['est'] for w in C['words'])
print(f'words: {len(C["words"])}, {len(C["words"]) - est} at set phrase times, {est} estimated by character position')
print('\n## runs')
for r in C['runs']:
    print(f"{r['i']} | {r['scene']} | {r['T0']:.3f}-{r['T1']:.3f} | {r['dur']:.2f} | {r.get('text', '')[:90]}")
print(f"END={C['END']:.3f}")
if os.path.exists(f'{sk}/mix.json'):
    print('\n## mix', json.dumps(json.load(open(f'{sk}/mix.json', encoding='utf-8'))))
# finish.sh records the name it wrote; renders from before that are final_video.mp4
final_mp4 = f"{sk}/{open(f'{sk}/final_name.txt').read().strip()}" if os.path.exists(f'{sk}/final_name.txt') else f'{sk}/final_video.mp4'
p = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_name,profile,width,height,r_frame_rate,nb_frames,sample_rate,channels:format=duration',
                    '-of', 'compact', final_mp4], capture_output=True, text=True).stdout
print('\n## file\n' + p.strip())
r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', final_mp4, '-map', '0:a', '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                   capture_output=True, text=True).stderr
summ = r[r.rfind('Summary:'):]
I = re.search(r'I:\s+(-?[\d.]+) LUFS', summ); TP = re.search(r'Peak:\s+(-?[\d.]+) dBFS', summ)
print(f"## loudness integrated {I.group(1) if I else '?'} LUFS, true peak {TP.group(1) if TP else '?'} dBFS")
try:
    th = json.load(open(f'{sk}/thumbnail.json', encoding='utf-8'))
    print(f"## thumbnail {th['t']} s (run {th['run']}, {th.get('scene')}), q{th['quality']} {th['bytes'] / 1e6:.2f} MB; candidates: "
          + ', '.join(f"{c['t']} s r{c['run']} sharp {c['sharpness']}" for c in th.get('candidates', [])))
except Exception as e: print('no thumbnail picked yet', e)
