"""Build a storyboard sheet: one frame per scene + VO line + on-screen text."""
import json, sys, textwrap
from PIL import Image, ImageDraw, ImageFont
F = 'assets/fonts/'
def font(name, size): return ImageFont.truetype(F + name, size)
stills_dir, audit_path, title, out = sys.argv[1:5]
stills = json.load(open(f'{stills_dir}/stills.json')); audit = json.load(open(audit_path))
COLS, FW, FH, CAP = 4, 324, 576, 330
rows = (len(stills) + COLS - 1) // COLS
W, H = COLS * (FW + 24) + 24, 150 + rows * (FH + CAP + 24)
sheet = Image.new('RGB', (W, H), (18, 18, 18)); d = ImageDraw.Draw(sheet)
d.text((24, 28), title, font=font('SpaceMono-Bold.ttf', 34), fill=(235, 235, 235))
d.text((24, 84), 'Storyboard · one frame per scene · timings estimated until the VO is recorded', font=font('SpaceMono-Regular.ttf', 20), fill=(140, 140, 140))
fb, fr, fs = font('SpaceMono-Bold.ttf', 19), font('SpaceMono-Regular.ttf', 16), font('SpaceMono-Regular.ttf', 15)
for i, s in enumerate(stills):
    x, y = 24 + (i % COLS) * (FW + 24), 150 + (i // COLS) * (FH + CAP + 24)
    im = Image.open(s['file']).convert('RGB').resize((FW, FH), Image.LANCZOS); sheet.paste(im, (x, y))
    d.rectangle([x, y + FH, x + FW, y + FH + CAP], fill=(28, 28, 28))
    a = audit[i]; sc = s['scene']
    d.text((x + 10, y + FH + 8), f"SCENE {i+1}  {sc['t']:.1f}-{sc['end']:.1f}s", font=fb, fill=(122, 214, 90))
    yy = y + FH + 36
    for line in textwrap.wrap('VO: ' + a['narration'], 34)[:8]:
        d.text((x + 10, yy), line, font=fr, fill=(210, 210, 210)); yy += 20
    yy += 6
    ons = [o for o in a['onscreen'] if not o.startswith('[hdr]')]
    hdr = ' / '.join(o[6:] for o in a['onscreen'] if o.startswith('[hdr]'))
    for line in textwrap.wrap('HEADER: ' + hdr, 36)[:2]:
        d.text((x + 10, yy), line, font=fs, fill=(110, 170, 90)); yy += 18
    for line in textwrap.wrap('ON SCREEN: ' + (' | '.join(ons) if ons else '(visual only)'), 36)[:4]:
        d.text((x + 10, yy), line, font=fs, fill=(120, 190, 255)); yy += 18
sheet.save(out, optimize=True); print('sheet ->', out, sheet.size)
