"""Contact sheets and labelled frames for render.py --screenshot (run inside work/ with the venv's python).
  sheet.py '<glob>' out.png [cols]        tiles in name order, each labelled "m:ss.ss [cue]" from its file name
  sheet.py --label "text" in.png out.png  one frame with its label (render.py --at)
File names are <seconds>[_<cue>].png; the label is the same time and cue the player's S key copies."""
import glob, os, re, sys
from PIL import Image, ImageDraw, ImageFont


def font(px):
    for f in ('fonts/PretendardVariable.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf', 'arial.ttf'):
        try: return ImageFont.truetype(f, px)
        except OSError: pass
    return ImageFont.load_default()


def label_of(path):
    m = re.match(r'([\d.]+)(?:_(\w+))?$', os.path.basename(path).rsplit('.', 1)[0])
    if not m: return os.path.basename(path)
    t = float(m.group(1)); mm, ss = divmod(t, 60)
    return f'{int(mm)}:{ss:05.2f}' + (f'  [{m.group(2)}]' if m.group(2) else '')


def stamp(im, text):
    d = ImageDraw.Draw(im); px = max(16, im.size[1] // 40)
    d.text((px // 2, px // 3), text, fill='yellow', font=font(px), stroke_width=max(2, px // 8), stroke_fill='black')


if sys.argv[1] == '--label':
    im = Image.open(sys.argv[3]).convert('RGB'); stamp(im, sys.argv[2]); im.save(sys.argv[4]); sys.exit(0)
files = sorted(glob.glob(sys.argv[1])); out = sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
# vertical tiles: 3 rows of 6 per image (3240x2880 at 540x960 tiles, nearly square). One tall sheet of 70 tiles
# (3240x12480) gets shrunk by any viewer or model until a tile is a thumbnail, so longer runs go into parts _p1, _p2 ...
ROWS = 3; per = cols * ROWS
parts = [files[i:i + per] for i in range(0, len(files), per)]
for n, part in enumerate(parts, 1):
    ims = [Image.open(f).convert('RGB') for f in part]
    w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * w, rows * h), 'black')
    for i, (f, im) in enumerate(zip(part, ims)):
        stamp(im, label_of(f)); sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    path = out if len(parts) == 1 else out[:-4] + f'_p{n}.png'
    sheet.save(path); print(os.path.abspath(path))
