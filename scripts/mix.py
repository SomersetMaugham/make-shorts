"""The short's sound: the narration alone, mastered for the platforms.
usage: python scripts/mix.py s1        -> <sk>/stems/voice.wav, <sk>/mix.wav, <sk>/mix.json

There is no music and there are no sound effects (script-to-motion's narration, carried over as it is): what the viewer
hears is the narration timeline timeline.py wrote (<sk>/voice.wav), every take exactly as recorded with the agent's cuts.
The master only changes the level - never the timing, the speed or the pitch:
- gain to -14 LUFS integrated (the platforms play shorts at about that loudness),
- then, only if the true peak would pass -1 dBTP, a limiter (alimiter, 5 ms attack); gain and limiter are refined
  together for a few passes until the mix sits within 0.3 LU of the target with its true peak under the ceiling.
stems/voice.wav is the narration before the master (to remix); mix.wav is what goes into final.mp4.
A silent narration (placeholders before recording, or "narration": false) is passed through untouched."""
import json, os, subprocess, sys
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.signal import resample_poly

sk = sys.argv[1]
SR = 48000; TARGET, TP_MAX = -14.0, -1.0
x, sr = sf.read(f'{sk}/voice.wav', dtype='float32', always_2d=True)
assert sr == SR, f'{sk}/voice.wav is {sr} Hz (timeline.py writes 48 kHz)'
os.makedirs(f'{sk}/stems', exist_ok=True)
sf.write(f'{sk}/stems/voice.wav', x, SR, subtype='PCM_24')


def true_peak_db(a):
    up = resample_poly(a, 4, 1, axis=0)                      # 4x oversampling (ITU-R BS.1770 true peak)
    p = float(np.abs(up).max())
    return 20 * np.log10(p) if p > 0 else -np.inf


meter = pyln.Meter(SR)
info = dict(target_lufs=TARGET, tp_max_dbtp=TP_MAX)
if not np.any(x):
    sf.write(f'{sk}/mix.wav', x, SR, subtype='PCM_24')
    info.update(silent=True)
    print(f'{sk}: silent narration (placeholders or "narration": false) -> mix.wav untouched')
else:
    lufs = meter.integrated_loudness(x)

    def limit(a, ceil_db):
        sf.write(f'{sk}/mix_in.wav', a, SR, subtype='FLOAT')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{sk}/mix_in.wav', '-af',
                        f'alimiter=limit={10 ** (ceil_db / 20):.4f}:attack=5:release=50:level=false', '-c:a', 'pcm_f32le',
                        f'{sk}/mix_lim.wav'], check=True)
        z, _ = sf.read(f'{sk}/mix_lim.wav', dtype='float32', always_2d=True)
        for f in ('mix_in.wav', 'mix_lim.wav'): os.remove(f'{sk}/{f}')
        return z[:len(a)] if len(z) >= len(a) else np.pad(z, ((0, len(a) - len(z)), (0, 0)))

    # limiting the peaks lowers the loudness a little, so gain and limiter are refined together (a few passes) until the
    # mix is within 0.3 LU of the target with its true peak at or under the ceiling
    g_db, ceil_db, limited = TARGET - lufs, TP_MAX - 0.5, False
    for _ in range(6):
        y = x * 10 ** (g_db / 20)
        if true_peak_db(y) > TP_MAX:
            y = limit(y, ceil_db); limited = True
        l, tp = meter.integrated_loudness(y), true_peak_db(y)
        if tp > TP_MAX: ceil_db -= tp - TP_MAX + 0.1; continue      # inter-sample overshoot past the limiter
        if abs(l - TARGET) <= 0.3: break
        g_db += TARGET - l
    sf.write(f'{sk}/mix.wav', y, SR, subtype='PCM_24')
    info.update(voice_lufs=round(lufs, 2), gain_db=round(g_db, 2), limiter=limited, limiter_ceiling_db=round(ceil_db, 2) if limited else None,
                mix_lufs=round(meter.integrated_loudness(y), 2), mix_tp_dbtp=round(true_peak_db(y), 2))
    ok = abs(info['mix_lufs'] - TARGET) <= 0.5 and info['mix_tp_dbtp'] <= TP_MAX
    print(f'{sk}: voice {lufs:.1f} LUFS, gain {g_db:+.1f} dB{" + limiter at " + format(ceil_db, ".1f") + " dB" if limited else ""} -> '
          f'mix_lufs {info["mix_lufs"]:.1f}, true peak {info["mix_tp_dbtp"]:.1f} dBTP' + ('' if ok else '  OUT OF RANGE: listen to the peaks'))
json.dump(info, open(f'{sk}/mix.json', 'w'), indent=1)
