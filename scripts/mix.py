"""The short's sound: the narration alone, mastered for the platforms.
usage: python scripts/mix.py s1        -> <sk>/stems/voice.wav, <sk>/mix.wav, <sk>/mix.json

There is no music and there are no sound effects (script-to-motion's narration, carried over as it is): what the viewer
hears is the narration timeline timeline.py wrote (<sk>/voice.wav), every take exactly as recorded with the agent's cuts.
The master only changes the level - never the timing, the speed or the pitch:
- gain to -14 LUFS integrated (the platforms play shorts at about that loudness),
- then, only if the true peak would pass -1 dBTP, a limiter (alimiter, 5 ms attack) and a re-measure.
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
    g = 10 ** ((TARGET - lufs) / 20)
    y = x * g
    tp = true_peak_db(y)
    info.update(voice_lufs=round(lufs, 2), gain_db=round(20 * np.log10(g), 2), tp_before_limiter=round(tp, 2), limiter=False)
    sf.write(f'{sk}/mix.wav', y, SR, subtype='FLOAT')
    if tp > TP_MAX:
        lim = 10 ** ((TP_MAX - 0.5) / 20)                     # half a dB of headroom for the inter-sample peaks the limiter misses
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{sk}/mix.wav', '-af',
                        f'alimiter=limit={lim:.4f}:attack=5:release=50:level=false', '-c:a', 'pcm_f32le', f'{sk}/mix_lim.wav'], check=True)
        y, _ = sf.read(f'{sk}/mix_lim.wav', dtype='float32', always_2d=True); os.remove(f'{sk}/mix_lim.wav')
        y = y[:len(x)] if len(y) >= len(x) else np.pad(y, ((0, len(x) - len(y)), (0, 0)))
        info['limiter'] = True
    sf.write(f'{sk}/mix.wav', y, SR, subtype='PCM_24')
    info.update(mix_lufs=round(meter.integrated_loudness(y), 2), mix_tp_dbtp=round(true_peak_db(y), 2))
    print(f'{sk}: voice {lufs:.1f} LUFS, gain {info["gain_db"]:+.1f} dB{" + limiter" if info["limiter"] else ""} -> '
          f'mix_lufs {info["mix_lufs"]:.1f}, true peak {info["mix_tp_dbtp"]:.1f} dBTP')
json.dump(info, open(f'{sk}/mix.json', 'w'), indent=1)
