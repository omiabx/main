"""The edit. Builds a timeline (shots, overlays, global fx, audio events) from VO alignment + clip table."""
import json, re, sys, pickle
sys.path.insert(0, '/home/user/media/tools')
from engine import *

CLIPS = json.load(open(ROOT + '/tools/clips.json'))
CLIPWORDS = json.load(open(ROOT + '/tr/clipwords.json'))
SCENES = json.load(open(ROOT + '/tr/scenes.json'))
import bisect


def snap(sh, d):
    k = sh.kw
    if sh.kind != 'video' or k['freeze'] or not k.get('snap', True) or k['src'] not in SCENES:
        return
    cuts = SCENES[k['src']]
    t = k['t']
    i = bisect.bisect_right(cuts, t) - 1
    if i < 0 or i + 1 >= len(cuts):
        return
    s0, s1 = cuts[i], cuts[i + 1]
    if s1 - t < d - 0.05:
        k['t'] = max(s0 + 0.05, s1 - d - 0.03)
        avail = s1 - k['t'] - 0.04
        over = d - avail
        if 0 < over < 0.45 and avail / d >= 0.72:
            k['speed'] = round(avail / d, 3)
    elif t - s0 < 0.1:
        k['t'] = s0 + 0.1
SFX = ROOT + '/sfx/'

S1, S3, S9, MMB, BTTP = 'src/s1d1.mp4', 'src/s3d2.mp4', 'src/s9d1.mp4', 'src/mmbegins.mp4', 'src/bttp.mp4'
MCH, BAT = 'arch/mchale_credits.mp4', 'arch/batman_trailer.mp4'
ARCH = {'look': 'archive'}
BW = {'look': 'bw'}
YEL = (255, 205, 0)
RED = (235, 40, 45)


class Build:
    def __init__(self, align):
        self.A = align
        self.t = 0.0
        self.shots, self.ovs, self.gfx, self.audio = [], [], [], []
        self.marks = {}

    # ---- helpers
    def sfx(self, name, t, gain=-14.0, **kw):
        self.audio.append(dict(path=SFX + name + '.wav', t=t, gain=gain + 2.0, **kw))

    def add_shot(self, sh, a, b):
        sh.start, sh.end = a, b
        self.shots.append(sh)

    def ov(self, fn, _a, _b, **kw):
        o = Ov(fn, _a, _b, **kw)
        self.ovs.append(o)
        return o

    def fx(self, kind, a, dur, **kw):
        self.gfx.append(GFX(kind, a, dur, **kw))

    # ---- anchors
    def anchor(self, bid, spec, base):
        """spec: None | 'END' | float (seconds from block start) | 'phrase' | ('phrase', offset) | ('phrase', offset, 'end')"""
        o = self.A[bid]
        if spec is None:
            return base
        if isinstance(spec, (int, float)):
            return base + spec
        if spec == 'END':
            return base + (o['t1'] - o['a0'])
        if isinstance(spec, str):
            spec = (spec, 0.0)
        phrase, off = spec[0], spec[1]
        use_end = len(spec) > 2 and spec[2] == 'end'
        p = norm_tokens(phrase)
        tok = o['tok']
        for i in range(len(tok) - len(p) + 1):
            if tok[i:i + len(p)] == p:
                tt = o['times'][i + len(p) - 1][1] if use_end else o['times'][i][0]
                return base + (tt - o['a0']) + off
        raise ValueError(f'anchor not found in VO {bid}: {phrase!r}')

    # ---- VO block
    def vo(self, bid, beats, ovs=(), sfx=(), gfx=(), tail=0.12):
        o = self.A[bid]
        base = self.t
        self.marks['VO' + bid] = base
        dur = o['a1'] - o['a0']
        self.audio.append(dict(path=o['path'], trim=(o['a0'], o['a1']), t=base, gain=0, vo=True, fade_in=0.02, fade_out=0.04))
        end = base + dur + tail
        times = [self.anchor(bid, b[0], base) for b in beats]
        for i, b in enumerate(beats):
            a = times[i]
            z = times[i + 1] if i + 1 < len(beats) else end
            snap(b[1], z - a)
            self.add_shot(b[1], a, z)
            if len(b) > 2 and b[2]:
                nm = b[2] if isinstance(b[2], str) else b[2][0]
                g = -16 if isinstance(b[2], str) else b[2][1]
                self.sfx(nm, a - (0.18 if 'whoosh' in nm or nm == 'swish' else 0), g)
        for spec in ovs:
            a_spec, b_spec, fn, kw = spec
            a = self.anchor(bid, a_spec, base)
            b = self.anchor(bid, b_spec, base) if not (isinstance(b_spec, tuple) and b_spec[0] == '+') else a + b_spec[1]
            self.ov(fn, a, b, **kw)
        for spec in sfx:
            a_spec, nm, g = spec[:3]
            self.sfx(nm, self.anchor(bid, a_spec, base), g)
        for spec in gfx:
            a_spec, kind, d = spec[:3]
            kw = spec[3] if len(spec) > 3 else {}
            self.fx(kind, self.anchor(bid, a_spec, base), d, **kw)
        self.t = end
        return base

    # ---- clip
    def clip(self, cid, zooms=None, y=0.42, x=0.5, subs=True, gap_before=0.1, tail=0.22, gain=0.0, grade=None,
             events=(), cut_sfx='swish'):
        c = CLIPS[cid]
        self.t += gap_before
        start = self.t
        lines = []
        words = CLIPWORDS.get(cid if cid in CLIPWORDS else cid, [])
        for i, (a, b) in enumerate(c['segs']):
            d = b - a
            z = zooms[i] if zooms else (1.0, 1.06) if i % 2 == 0 else (1.14, 1.2)
            self.add_shot(V(c['src'], a, z[0], z[1], y=y if not isinstance(y, list) else y[i],
                            x=x if not isinstance(x, list) else x[i], grade=grade), self.t, self.t + d)
            aa = c.get('asegs', c['segs'])[i][0]
            self.audio.append(dict(path=f'{ROOT}/clipaudio/{cid}_{i}_vox.wav', t=self.t - (a - aa), gain=gain, clip=True,
                                   fade_in=0.01, fade_out=0.03, trim=(a - aa, b - aa)))
            if i > 0 and cut_sfx:
                self.sfx(cut_sfx, self.t - 0.08, -22)
            # subtitles from word timings
            ws = [w for w in CLIPWORDS.get(cid, []) if a - 0.05 <= w[0] < b]
            cur, cur_s = [], None
            for w in ws:
                if not cur:
                    cur_s = w[0]
                cur.append(w)
                txt = ' '.join(x[2] for x in cur)
                if re.search(r'[.?!]$', w[2]) or len(txt) > 38:
                    lines.append((self.t + cur_s - a - start, min(self.t + w[1] - a - start + 0.25, self.t + d - start), txt))
                    cur = []
            if cur:
                lines.append((self.t + cur_s - a - start, self.t + d - start, ' '.join(x[2] for x in cur)))
            self.t += d
        end = self.t
        if subs:
            fixed = []
            for (a, b, txt) in lines:
                txt = txt.replace('coop', 'coot').replace('particle', 'Barnacle').replace('Pit Squeak', 'Pip Squeak')
                txt = txt.replace('Justice Kyle', 'justice, Kyle').replace('Ah, feels', 'It feels').replace('Uh, feels', 'It feels')
                fixed.append((a, b, txt))
            self.ov('subs', start, end, lines=fixed)
        for ev in events:   # (local_t, kind, args)
            lt, kind = ev[0], ev[1]
            kw = ev[2] if len(ev) > 2 else {}
            if kind in ('shake', 'punch'):
                self.fx(kind, start + lt, kw.pop('dur', 0.4), **kw)
            elif kind == 'sfx':
                self.sfx(kw['name'], start + lt, kw.get('gain', -14))
            else:
                self.ov(kind, start + lt, start + lt + kw.pop('dur', 1.0), **kw)
        self.t = end + tail
        return start, end

    def word_t(self, cid, word, nth=0):
        """local time of a word inside a clip (relative to clip start), handles multi-seg"""
        c = CLIPS[cid]
        acc = 0.0
        k = 0
        for (a, b) in c['segs']:
            for w in CLIPWORDS[cid]:
                if a - 0.05 <= w[0] < b and re.sub(r'\W', '', w[2]).lower() == word.lower():
                    if k == nth:
                        return acc + w[0] - a
                    k += 1
            acc += b - a
        raise ValueError(f'{word} not in {cid}')

    def gap(self, d, shot=None):
        if shot:
            self.add_shot(shot, self.t, self.t + d)
        self.t += d

    def timeline(self):
        self.shots.sort(key=lambda s: s.start)
        # make shots contiguous: extend each shot to the next one's start (no black holes)
        for i in range(len(self.shots) - 1):
            if self.shots[i].end < self.shots[i + 1].start:
                self.shots[i].end = self.shots[i + 1].start
            if self.shots[i].end > self.shots[i + 1].start:
                self.shots[i].end = self.shots[i + 1].start
        return dict(shots=self.shots, ovs=self.ovs, gfx=self.gfx, audio=self.audio, total=self.t, marks=self.marks)


def build(align):
    B = Build(align)
    wt = B.word_t

    # ================================================================ COLD OPEN
    s, e = B.clip('C01', zooms=[(1.0, 1.12)], y=0.4, gap_before=0.0, tail=0.35,
                  events=[(wt('C01', 'No', 0), 'punch', dict(dur=1.2, amt=0.12))])
    B.ov('fade', s, s + 0.4, mode='in')
    B.sfx('reverse_swell', e - 0.25, -20)

    # VO 01
    B.vo('01', [
        (None, V(MMB, 96.5, 1.0, 1.1), 'tv_off'),
        ('sits down to tell', V(MMB, 236, 1.0, 1.08)),
        ('washing machine', V(MMB, 258.5, 1.05, 1.15), 'scratch'),
        ('falls asleep', V(MMB, 286.5, 1.0, 1.1)),
        ("that's kind of his whole deal", V(S1, 6646.5, 1.0, 1.12, y=0.4)),
        ('oldest superhero', V(S1, 6594, 1.0, 1.08)),
        ("can't remember his own past", V(MMB, 86.6, 1.0, 1.12), 'whoosh2'),
        ('except that same episode', V(MMB, 489.5, 1.0, 1.1, grade={'look': 'desat', 'amt': 0.4}), 'glitch'),
        ('two first names', CARD(card_dark)),
        ('a tv show that went off the air', V(MCH, 1.0, 1.0, 1.12, grade=ARCH), 'projector'),
    ], ovs=[
        ('washing machine', ('+', 1.3), 'text', dict(txt='WASHING MACHINE?', y=0.82, size=96, color=YEL)),
        ("can't remember his own past", ('+', 1.9), 'text', dict(txt='???', y=0.5, size=220, color=(255, 255, 255))),
        ('except that same episode', ('+', 0.35), 'glitch', {}),
        ('two first names', 'a tv show that went off the air', 'redact', dict(names=['ERNIE', 'TIM'], paper=True)),
        ('went off the air in 1966', 'END', 'text', dict(txt='1966', y=0.5, size=230, color=(245, 240, 225), font='SpecialElite-Regular.ttf', stroke=0, anim='fade')),
    ], sfx=[('two first names', 'typewriter', -14), ('went off the air in 1966', 'impact', -9)],
        gfx=[('went off the air in 1966', 'shake', 0.35, dict(amp=14))])

    # title sting: show logo swirl
    B.gap(1.1, V(S1, 6198.4, 1.0, 1.1))
    B.sfx('bubbles', B.t - 1.15, -12)
    B.sfx('whoosh3', B.t - 1.1, -16)

    # VO 02
    B.vo('02', [
        (None, V(S1, 6238.4, 1.0, 1.1)),
        ('show up in season one', V(S1, 6222.0, 1.0, 1.1)),
        ('obsessed with their old tv show', V(S1, 6242.5, 1.0, 1.08)),
        ('so they go looking', V(S1, 6350.0, 1.0, 1.1)),
        ('and they find them', V(S1, 6359.25, 1.0, 1.15, y=0.45, snap=False), 'whoosh1'),
        ('which is a retirement home', V(S1, 6402.5, 1.0, 1.08), 'thud'),
    ], ovs=[
        (None, ('+', 3.0), 'label', dict(txt='MERMAID MAN AND BARNACLE BOY', sub='SEASON 1  ·  AUGUST 1999')),
        ('which is a retirement home', ('+', 1.6), 'text', dict(txt='A RETIREMENT HOME.', y=0.8, size=100)),
    ])

    B.clip('C02', zooms=[(1.0, 1.1)], y=0.42)

    # VO 03
    B.vo('03', [
        (None, V(S1, 6406.5, 1.0, 1.06)),
        ('for the next thirteen years', V(S1, 6666, 1.0, 1.08)),
        ('mermaid man cannot handle', V(S1, 6426.2, 1.0, 1.35, freeze=True, y=0.38), 'riser_short'),
    ], ovs=[('for the next thirteen years', ('+', 1.8), 'text', dict(txt='1999 → 2012', y=0.8, size=110, color=YEL))],
        sfx=[('one specific word', 'heartbeat', -14)])

    s, e = B.clip('C03', zooms=[(1.0, 1.08)], y=0.42, tail=0.2,
                  events=[(wt('C03', 'Evil'), 'shake', dict(dur=0.9, amp=26)),
                          (wt('C03', 'Evil'), 'flash', dict(dur=0.25, amt=0.7)),
                          (wt('C03', 'Evil'), 'sfx', dict(name='impact', gain=-11))])

    # VO 04
    B.vo('04', [(None, V(S1, 6530.0, 1.0, 1.06, grade='dark'))],
         ovs=[('treated like', ('+', 2.0), 'sticker', dict(path='frames/bb_angry_x4.png', mask='frames/bb_angry_x4_mask.png', height=760, x=0.24, y=0.58, from_='left')),
              ("like he's eight", ('+', 1.4), 'text', dict(txt="(HE'S NOT 8)", x=0.68, y=0.5, size=110, color=YEL, angle=4))],
         sfx=[('treated like', 'whoosh2', -16), ("like he's eight", 'pop', -14)])

    B.clip('C04', zooms=[(1.0, 1.08), (1.15, 1.22)], y=0.42)

    # VO 05
    B.vo('05', [
        (None, V(S1, 6670, 1.0, 1.08)),
        ('at the end of that very first episode', V(S1, 6782.5, 1.0, 1.08)),
        ('and says', V(S1, 6794.2, 1.0, 1.25, freeze=True), 'shutter'),
    ])
    B.clip('C05', zooms=[(1.0, 1.05)], y=0.42, tail=0.35,
           events=[(wt('C05', 'Who'), 'punch', dict(dur=1.3, amt=0.28)), (wt('C05', 'Who'), 'sfx', dict(name='scratch', gain=-15))])

    # VO 06
    B.vo('06', [
        (None, V(BTTP, 92.0, 1.0, 1.08)),
        ('the cabinet', V(BTTP, 84.0, 1.0, 1.15)),
    ], ovs=[('in back to the past', ('+', 2.6), 'label', dict(txt='BACK TO THE PAST', sub='SEASON 7  ·  2010'))])
    B.clip('C06', zooms=[(1.0, 1.1)], y=0.42, tail=0.45,
           events=[(wt('C06', 'remember'), 'punch', dict(dur=1.0, amt=0.15)), (wt('C06', 'remember') + 0.6, 'sfx', dict(name='tick', gain=-16))])

    # VO 07
    B.vo('07', [
        (None, V(MMB, 3.0, 1.0, 1.08)),
        ('a storm knocks out', V(MMB, 104, 1.0, 1.1)),
        ('never before aired origin special', V(MMB, 97.5, 1.0, 1.1)),
        ('go straight to the source', V(MMB, 178, 1.0, 1.08)),
        ('just ask him', V(MMB, 226.5, 1.0, 1.08)),
        ('starts with the creation of the ocean', V(MMB, 232.5, 1.0, 1.1)),
        ('barnacle boy has to stop him', V(MMB, 246.5, 1.0, 1.08)),
        ('then he tries again', V(MMB, 250.5, 1.0, 1.15)),
    ], ovs=[(None, ('+', 2.6), 'label', dict(txt='MERMAID MAN BEGINS', sub='SEASON 8  ·  SEPTEMBER 2011')),
            ('every tv', ('+', 0.5), 'static', dict(amt=0.55))],
        sfx=[('every tv', 'static_short', -16), ('every tv', 'tv_off', -18)])

    B.clip('C07', zooms=[(1.0, 1.1), (1.12, 1.2)], y=0.42,
           events=[(wt('C07', 'washing'), 'punch', dict(dur=1.4, amt=0.12)), (wt('C07', 'stopped') + 0.3, 'sfx', dict(name='scratch', gain=-17))])

    # VO 08
    B.vo('08', [
        (None, V(MMB, 290.5, 1.0, 1.08)),
        ('mermaids save him', V(MMB, 312.5, 1.0, 1.08)),
        ('magic sea star', V(MMB, 316.8, 1.0, 1.12)),
        ('telekinetic powers', V(MMB, 380.5, 1.0, 1.1)),
        ('swap a drowning', V(MMB, 384.0, 1.0, 1.12)),
        ('that kid is barnacle boy', V(MMB, 388.5, 1.0, 1.15), 'pop'),
        ('sitting right there', V(MMB, 399.0, 1.0, 1.08)),
    ], ovs=[('sixty something years', ('+', 2.0), 'text', dict(txt='"60-SOME-ODD YEARS"', y=0.8, size=96, color=YEL))])

    B.clip('C08', zooms=[(1.0, 1.1)], y=0.42)

    # VO 09: origin montage
    B.vo('09', [
        (None, V(MMB, 474.0, 1.0, 1.06)),
        ('they all watch the official version', V(MMB, 483.5, 1.0, 1.06)),
        ("i'm being completely serious", V(MMB, 486.0, 1.0, 1.12)),
        ('a radioactive ant', V(MMB, 509.5, 1.1, 1.25), 'pop'),
        ('a vat of acid', V(MMB, 527.0, 1.0, 1.12), 'pop'),
        ('an alien spaceship', V(MMB, 531.0, 1.0, 1.12), 'pop'),
        ('a solar eclipse', V(MMB, 533.8, 1.0, 1.1), 'pop'),
        ('a neon plaid lightning bolt', V(MMB, 549.2, 1.0, 1.12), 'pop'),
        ('the thing that finally gives them powers', V(MMB, 584.0, 1.0, 1.12)),
        ('left in the microwave too long', V(MMB, 600.0, 1.0, 1.1), 'impact'),
        ('but go back to the first', V(MMB, 600.0, 1.0, 1.0, freeze=True), 'whoosh_rev'),
        ('before any of that happens', V(MMB, 489.0, 1.0, 1.08)),
        ('call each other by name', V(MMB, 495.5, 1.0, 1.18)),
    ], ovs=[
        ('a radioactive ant', ('+', 0.9), 'text', dict(txt='RADIOACTIVE ANT', y=0.84, size=88)),
        ('a vat of acid', ('+', 0.9), 'text', dict(txt='VAT OF ACID', y=0.84, size=88)),
        ('an alien spaceship', ('+', 0.9), 'text', dict(txt='ALIEN SPACESHIP', y=0.84, size=88)),
        ('a solar eclipse', ('+', 1.3), 'text', dict(txt='ECLIPSE (ON A LEAP YEAR)', y=0.84, size=88)),
        ('a neon plaid lightning bolt', ('+', 1.4), 'text', dict(txt='NEON PLAID LIGHTNING', y=0.84, size=88)),
        ('left in the microwave too long', ('+', 1.6), 'text', dict(txt='OVERCOOKED POPCORN', y=0.82, size=110, color=YEL, anim='punch')),
        ('but go back to the first', 'before any of that happens', 'vhs_rewind', {}),
    ], gfx=[('left in the microwave too long', 'shake', 0.4, dict(amp=16))])

    B.clip('C09', zooms=[(1.0, 1.1)], y=0.42, tail=0.3,
           events=[(wt('C09', 'Ernie'), 'text', dict(dur=1.6, txt='"ERNIE"', y=0.16, size=120, color=YEL)),
                   (wt('C09', 'Ernie'), 'sfx', dict(name='pop_hi', gain=-12)),
                   (wt('C09', 'Tim'), 'text', dict(dur=1.2, txt='"TIM"', y=0.16, size=120, color=YEL)),
                   (wt('C09', 'Tim'), 'sfx', dict(name='pop_hi', gain=-12))])

    # VO 10: the reveal
    B.vo('10', [
        (None, CARD(card_dark)),
        ('mermaid man was voiced by', V(MMB, 8.0, 1.0, 1.0, y=0.5, freeze=True), 'whoosh1'),
        ('twelve years into the show', V(S3, 4752.5, 1.0, 1.0, y=0.5, freeze=True), 'swish'),
        ('they just used', CARD(card_dark)),
        ('what those two actors were doing', V(BTTP, 168.0, 1.0, 1.15), 'riser'),
    ], ovs=[
        (None, 'mermaid man was voiced by', 'redact', dict(names=['ERNIE', 'TIM'], lift_at=0.0, paper=True)),
        ('ernest borgnine', ('+', 2.8), 'circle', dict(cx=964, cy=566, rx=700, ry=125, angle=-28)),
        ('tim conway', ('+', 1.9), 'circle', dict(cx=1062, cy=712, rx=520, ry=105, angle=-30)),
        ('twelve years into the show', ('+', 2.0), 'text', dict(txt='1999 → 2011', y=0.16, size=96, color=YEL)),
        ('they just used', 'what those two actors were doing', 'split', dict(
            left=dict(frame=(MMB, 494.0), caption='"ERNIE"', crop=(0.1, 0.05, 0.9, 0.95)),
            right=dict(frame=(MMB, 488.6), caption='"TIM"', crop=(0.1, 0.05, 0.9, 0.95)))),
        ('the actors first names', ('+', 1.6), 'text', dict(txt='ERNEST BORGNINE  ·  TIM CONWAY', y=0.9, size=72, color=YEL)),
        ('in 1962', 'END', 'text', dict(txt='1962', y=0.5, size=260, color=(255, 255, 255), anim='punch')),
    ], sfx=[(None, 'impact_big', -10), ('ernest borgnine', 'pop', -14), ('tim conway', 'pop', -14),
            ('in 1962', 'impact', -9)], gfx=[('in 1962', 'shake', 0.35, dict(amp=16))])
    B.sfx('projector', B.t - 0.3, -20, fade_out=0.6)

    # VO 11: 1962 (archive look)
    B.vo('11', [
        (None, CARD(card_dark)),
        ('abc premieres', V(MCH, 0.5, 1.0, 1.1, grade=ARCH), 'projector'),
        ('ernest borgnine plays the skipper', V(MCH, 10.5, 1.0, 1.08, grade=ARCH, freeze=False)),
        ('lieutenant commander', I('arch/borgnine1962.jpg', (0.62, 0.5, 1.0), (0.66, 0.45, 1.18), grade=ARCH)),
        ("he's already got an oscar", I('arch/mchale_ad1963.jpg', (0.5, 0.62, 1.4), (0.5, 0.66, 1.75), grade=ARCH), 'paper'),
        ("and mchale's second in command", I('arch/conway_1964.png', (0.5, 0.35, 1.0), (0.5, 0.4, 1.15), grade=ARCH, bg='contain'), 'paper'),
        ('the show ran', I('arch/trio_1964.png', (0.5, 0.45, 1.0), (0.62, 0.42, 1.2), grade=ARCH)),
        ('and the two of them', CARD(card_dark)),
    ], ovs=[
        (None, 'abc premieres', 'datecard', dict(txt='OCTOBER 11, 1962', sub='ABC  ·  TUESDAY NIGHT')),
        ('one pt boat', ('+', 2.0), 'text', dict(txt='PT-73', x=0.72, y=0.3, size=150, color=YEL, angle=-4)),
        ('lieutenant commander', ('+', 2.6), 'label', dict(txt='ERNEST BORGNINE', sub='LT. CMDR. QUINTON McHALE')),
        ('a movie called marty', ('+', 1.25), 'text', dict(txt='BEST ACTOR  ·  MARTY (1955)', y=0.85, size=78, color=YEL)),
        ('tim conway', ('+', 2.4), 'label', dict(txt='TIM CONWAY', sub='ENSIGN CHARLES PARKER')),
        ('a hundred and thirty eight episodes', ('+', 2.0), 'counter', dict(n=138, fmt='{} EPISODES', size=150, y=0.82)),
        ('ended in 1966', ('+', 1.4), 'text', dict(txt='1962 – 1966', y=0.16, size=90)),
        ('carol burnett show', ('+', 1.25), 'text', dict(txt='THE CAROL BURNETT SHOW', y=0.85, size=78)),
        ('and the two of them', 'END', 'timeline', dict(a=1966, b=1999, draw=2.2)),
    ], sfx=[(None, 'typewriter', -13), ('one pt boat', 'stamp', -14), ('tim conway', 'shutter', -14),
            ('a hundred and thirty eight episodes', 'tick', -16), ('and the two of them', 'riser', -18)])

    # VO 12: back to color
    B.vo('12', [
        (None, V(S1, 6246.0, 1.0, 1.06), 'whoosh3'),
        ('he and his creative director', V(S1, 6202.5, 1.0, 1.0, y=0.5, freeze=True)),
        ("are mchale's navy fans", I('arch/trio_1964.png', (0.5, 0.5, 1.0), (0.5, 0.45, 1.1), grade=ARCH)),
        ("according to the show's casting supervisor", V(S1, 6222.2, 1.0, 1.08)),
        ('they went to them directly', V(S3, 4752.5, 1.0, 1.0, y=0.5, freeze=True)),
        ('so in 1999', CARD(card_dark), 'whoosh1'),
        ('borgnine is eighty two', V(S1, 6406.5, 1.0, 1.08)),
        ('and the pecking order', V(S1, 6501.5, 1.0, 1.1)),
    ], ovs=[
        ('stephen hillenburg', ('+', 2.6), 'label', dict(txt='STEPHEN HILLENBURG', sub='CREATOR  ·  FORMER MARINE BIOLOGY TEACHER')),
        ('derek drymon', ('+', 2.4), 'circle', dict(cx=1034, cy=800, rx=790, ry=135, angle=-15)),
        ("according to the show's casting supervisor", ('+', 3.0), 'label', dict(txt='CASTING SUPERVISOR JENNIE MONICA HAMMOND', sub="HOGAN'S ALLEY, 2010")),
        ('both of them said yes', ('+', 1.8), 'text', dict(txt='BOTH SAID YES', y=0.16, size=100, color=YEL)),
        ('so in 1999', 'borgnine is eighty two', 'split', dict(
            left=dict(path='arch/trio_1964.png', caption='1964', bw=True, crop=(0.25, 0.2, 1.0, 1.0)),
            right=dict(frame=(S1, 6410.5), caption='1999', crop=(0.15, 0.1, 0.95, 0.95)), mid='→')),
        ('borgnine is eighty two', ('+', 1.4), 'text', dict(txt='BORGNINE: 82', x=0.3, y=0.2, size=96, color=YEL)),
        ('conway is sixty five', ('+', 1.6), 'text', dict(txt='CONWAY: 65', x=0.72, y=0.2, size=96, color=YEL)),
    ], sfx=[('both of them said yes', 'ding', -20), ('borgnine is eighty two', 'pop', -14), ('conway is sixty five', 'pop', -14)])

    B.clip('C10', zooms=[(1.0, 1.08)], y=0.42)

    # VO 13
    B.vo('13', [
        (None, V(S3, 4824.5, 1.0, 1.1)),
        ("in 1962 he's the junior officer", I('arch/conway_1964.png', (0.5, 0.4, 1.0), (0.5, 0.42, 1.12), grade=ARCH, bg='contain'), 'projector'),
        ("in 1999 he's the sidekick", V(S1, 6533.5, 1.0, 1.08), 'whoosh2'),
        ("the character's name is boy", V(S1, 6535.6, 1.15, 1.3, freeze=True)),
        ('and in 2002', V(S3, 4744.5, 1.0, 1.08), 'whoosh1'),
    ], ovs=[("the character's name is boy", ('+', 1.4), 'text', dict(txt='"BOY"', y=0.5, size=260, anim='punch')),
            ('and in 2002', ('+', 2.6), 'label', dict(txt='MERMAID MAN AND BARNACLE BOY V', sub='SEASON 3  ·  JUNE 2002'))],
        sfx=[("the character's name is boy", 'thud', -10)])

    B.clip('C11', zooms=[(1.0, 1.06), (1.0, 1.12), (1.08, 1.14)], y=0.42,
           events=[(wt('C11', '68'), 'punch', dict(dur=1.6, amt=0.16)), (wt('C11', '68'), 'sfx', dict(name='impact', gain=-14)),
                   (wt('C11', 'bra'), 'sfx', dict(name='scratch', gain=-18))])

    # VO 14
    B.vo('14', [
        (None, V(S3, 4838.0, 1.15, 1.3, freeze=True)),
        ('that episode aired', CARD(card_dark)),
        ("i can't prove", V(S3, 4856.0, 1.0, 1.08)),
        ('he quits', V(S3, 4906.0, 1.0, 1.1), 'whoosh2'),
        ('joins the villains', V(S3, 4954.0, 1.0, 1.12)),
        ('gets most of what he asked for', V(S3, 5370.5, 1.0, 1.08)),
        ('and comes back', V(S3, 5392.5, 1.0, 1.1)),
        ('the very last thing', V(S3, 5396.0, 1.0, 1.12)),
    ], ovs=[
        (None, ('+', 1.0), 'text', dict(txt='68', y=0.5, size=330, color=YEL, anim='punch')),
        ('that episode aired', "i can't prove", 'split', dict(
            left=dict(frame=(S3, 4838.0), caption='BARNACLE BOY: 68', crop=(0.1, 0.05, 0.9, 0.95)),
            right=dict(path='arch/conway_1964.png', caption='TIM CONWAY: 68', bw=True),
            mid='=')),
        ('was sixty eight years old', ('+', 2.0), 'text', dict(txt='BORN DEC 15, 1933  ·  EPISODE AIRED JUNE 1, 2002', y=0.9, size=52)),
    ], sfx=[(None, 'impact', -11), ('that episode aired', 'whoosh1', -16), ('was sixty eight years old', 'ding', -18)])

    B.clip('C12', zooms=[(1.0, 1.08)], y=0.42, tail=0.15,
           events=[(wt('C12', 'Kyle'), 'glitch', dict(dur=0.35)), (wt('C12', 'Kyle'), 'sfx', dict(name='glitch', gain=-14))])

    # VO 15
    B.vo('15', [
        (None, V(S3, 5400.6, 1.2, 1.35, freeze=True)),
        ('in 2002', CARD(card_dark)),
        ('so mermaid man', V(MMB, 251.0, 1.0, 1.1)),
        ('the show forgot', V(S3, 4808.5, 1.0, 1.1, grade={'look': 'desat', 'amt': 0.5})),
    ], ovs=[
        (None, 'in 2002', 'text', dict(txt='"KYLE"?', y=0.5, size=240, color=RED, anim='punch')),
        ('in 2002', 'so mermaid man', 'split', dict(
            left=dict(frame=(S3, 5400.6), caption='2002: "KYLE"', crop=(0.1, 0.05, 0.9, 0.95)),
            right=dict(frame=(MMB, 488.6), caption='2011: "TIM"', crop=(0.1, 0.05, 0.9, 0.95)))),
    ], sfx=[(None, 'glitch', -16), ('in 2002', 'whoosh2', -16)])

    # VO 16: EVIL
    B.vo('16', [
        (None, V(MMB, 228.0, 1.0, 1.1)),
        ('the most famous thing', V(S1, 6426.2, 1.0, 1.2, freeze=True)),
        ('his voice cracked', V(S1, 6426.9, 1.25, 1.4, freeze=True)),
        ("here's how borgnine told it", V(S1, 6426.9, 1.25, 1.35, freeze=True)),
        ('in a 2011 interview', V(S1, 6246.0, 1.0, 1.08)),
        ('this is a man who won', I('arch/mchale_ad1963.jpg', (0.5, 0.64, 1.5), (0.5, 0.66, 1.9), grade=ARCH)),
        ('and in his nineties', V(S1, 6246.0, 1.0, 1.1)),
    ], ovs=[
        ('his voice cracked', ('+', 1.8), 'text', dict(txt='E V I - I L', y=0.78, size=150, color=YEL, anim='punch')),
        ("here's how borgnine told it", 'in a 2011 interview', 'quote', dict(txt='By golly! We started something... and we kept it in.', who='ERNEST BORGNINE  ·  ARCHIVE OF AMERICAN TELEVISION')),
        ('in a 2011 interview', 'this is a man who won', 'quote', dict(txt='EVILLLLL! The kids scream and holler when I do that.', who='ERNEST BORGNINE  ·  HUFFPOST, 2011')),
        ('one broken syllable', ('+', 1.4), 'text', dict(txt='ONE SYLLABLE.', y=0.8, size=100)),
    ], sfx=[('his voice cracked', 'glitch', -18), ("here's how borgnine told it", 'typewriter', -18), ('in a 2011 interview', 'typewriter', -18)])

    B.clip('C13', zooms=[(1.05, 1.15)], y=0.42, tail=0.3,
           events=[(0.05, 'shake', dict(dur=1.0, amp=30)), (0.05, 'flash', dict(dur=0.3, amt=0.8)), (0.05, 'sfx', dict(name='impact_big', gain=-11))])

    # VO 17: Batman & Robin
    B.vo('17', [
        (None, V(BTTP, 166.0, 1.0, 1.15), 'whoosh3'),
        ('in 2010', V(BTTP, 236.5, 1.0, 1.08)),
        ('younger versions of the heroes', V(BTTP, 252.5, 1.0, 1.1)),
        ('they cast adam west', V(BAT, 6.8, 1.0, 1.06, y=0.5), 'swish'),
        ('so you get a scene', V(BTTP, 301.5, 1.0, 1.08)),
        ('their younger selves', V(BTTP, 313.0, 1.0, 1.0)),
        ('voiced by mchale and parker', V(BTTP, 331.0, 1.0, 1.0, freeze=True)),
        ('and have no idea', V(BTTP, 320.5, 1.0, 1.1)),
    ], ovs=[
        ('in 2010', ('+', 2.4), 'label', dict(txt='BACK TO THE PAST', sub='SEASON 7  ·  FEBRUARY 2010')),
        ('from the 1966 batman show', ('+', 1.8), 'text', dict(txt='BATMAN · 1966', y=0.14, size=90, color=YEL)),
        ("voiced by tv's batman and robin", 'voiced by mchale and parker', 'names', dict(items=[('BATMAN', 330, 150, 650, 260), ('ROBIN', 1700, 300, 1500, 470)])),
        ('voiced by mchale and parker', ('+', 2.0), 'names', dict(items=[('McHALE', 330, 110, 560, 250), ('PARKER', 1640, 130, 1370, 280)])),
    ], sfx=[("voiced by tv's batman and robin", 'pop', -15), ('voiced by mchale and parker', 'pop', -15)])

    B.clip('C14', zooms=[(1.0, 1.08), (1.08, 1.14)], y=0.42)

    # VO 18
    B.vo('18', [
        (None, V(BTTP, 331.0, 1.0, 1.0, freeze=True)),
        ('i honestly', V(BTTP, 331.0, 1.0, 1.15, freeze=True, grade={'look': 'fade_desat', 'dur': 4.0})),
    ], ovs=[(None, 'i honestly', 'names', dict(items=[('McHALE (1962)', 330, 110, 560, 250), ('PARKER (1962)', 1640, 130, 1370, 280),
                                                      ('BATMAN (1966)', 260, 560, 560, 650), ('ROBIN (1966)', 1700, 760, 1420, 900)], size=56))],
         sfx=[(None, 'shutter', -15)])
    B.gap(0.5)

    # VO 19: July 2012
    B.vo('19', [
        (None, CARD(card_dark)),
        ('ernest borgnine dies', V(BTTP, 496.5, 1.0, 1.15, grade={'look': 'desat', 'amt': 0.75})),
        ('nickelodeon runs', V(MMB, 67.0, 1.0, 1.1)),
        ('that october', V(S9, 1369.3, 1.0, 1.08)),
        ('airs', V(S9, 1375.3, 1.0, 1.08, y=0.5, freeze=True)),
        ('patrick decides', V(S9, 1536.0, 1.0, 1.08)),
        ('after he sees an ad', V(S9, 1462.0, 1.0, 1.08)),
        ("it's an ad for", V(S9, 1474.5, 1.0, 1.08)),
    ], ovs=[
        (None, 'ernest borgnine dies', 'datecard', dict(txt='JULY 8, 2012', cps=0.08)),
        ('ernest borgnine dies', ('+', 3.0), 'text', dict(txt='ERNEST BORGNINE  ·  1917 – 2012', y=0.86, size=70, anim='fade')),
        ('that october', ('+', 2.6), 'label', dict(txt='PATRICK-MAN!', sub='SEASON 9  ·  OCTOBER 2012')),
    ], sfx=[(None, 'typewriter', -15)])

    B.clip('C15', zooms=[(1.0, 1.06)], y=0.42, tail=0.0)

    # VO 20
    b20 = B.vo('20', [
        (None, V(S9, 1486.0, 1.06, 1.06, freeze=True)),
        ('a commercial', CARD(card_dark)),
        ('and behind the scenes', V(BTTP, 85.0, 1.0, 1.12, grade={'look': 'desat', 'amt': 0.6})),
        ("he wouldn't recast", CARD(card_dark)),
        ('showrunner vincent waller', CARD(card_dark)),
        ("the characters didn't disappear", V(S1, 6594.5, 1.0, 1.08, grade={'look': 'desat', 'amt': 0.5})),
        ('in cameos', V(S1, 6766.5, 1.0, 1.1, grade={'look': 'desat', 'amt': 0.5})),
        ("they just don't talk anymore", CARD(card_dark)),
        ('in 2018', CARD(card_dark)),
        ('two months later', CARD(card_dark)),
        ('and in may 2019', CARD(card_dark)),
    ], ovs=[
        (None, 'a commercial', 'tvoff', {}),
        ("he wouldn't recast", 'showrunner vincent waller', 'sticker', dict(path='frames/mmb_230_x4.png', mask='frames/mmb_230_x4_mask.png', height=820, x=0.5, y=0.6, from_='bottom')),
        ("he wouldn't recast", 'showrunner vincent waller', 'text', dict(txt='NO SOUND-ALIKE.', y=0.16, size=110, color=YEL)),
        ('showrunner vincent waller', "the characters didn't disappear", 'quote', dict(txt='Steve was very clear he did not want to replace Ernest Borgnine with a sound alike. It was his call.', who='VINCENT WALLER  ·  SHOWRUNNER, 2019', size=56)),
        ("they just don't talk anymore", 'in 2018', 'sticker', dict(path='frames/mm_taped.png', height=780, x=0.5, y=0.58, from_='pop', outline=12)),
        ('in 2018', 'two months later', 'quote', dict(txt='No, sadly not. Mr. Conway is having health issues.', who='VINCENT WALLER  ·  SEPTEMBER 2018')),
        ('two months later', 'and in may 2019', 'datecard', dict(txt='STEPHEN HILLENBURG', sub='1961 – 2018', cps=0.05)),
        ('and in may 2019', ('+', 4.5), 'datecard', dict(txt='TIM CONWAY', sub='1933 – 2019', cps=0.06)),
    ], sfx=[('a commercial', 'tv_off', -12), ("they just don't talk anymore", 'tape_rip', -14),
            ('two months later', 'typewriter', -18), ('and in may 2019', 'typewriter', -18)])

    # VO 21
    B.vo('21', [
        (None, V(S1, 6795.5, 1.0, 1.06)),
        ('it plays as a joke', V(S1, 6594.0, 1.0, 1.06)),
        ('but the show remembered', V(MMB, 8.0, 1.0, 1.12, y=0.5, freeze=True)),
        ('it knew who these two were', V(MCH, 2.0, 1.0, 1.1, grade=ARCH)),
        ('it gave them a retirement home', V(S1, 6359.9, 1.0, 1.1, snap=False)),
        ('and their real first names', V(MMB, 492.0, 1.0, 1.1)),
        ('when they were gone', V(MMB, 620.0, 1.0, 1.08, grade={'look': 'fade_desat', 'dur': 3.0, 'amt': 0.5})),
        ('which brings me back', V(MMB, 640.0, 1.0, 1.0, freeze=True), 'whoosh_rev'),
    ], ovs=[('which brings me back', 'END', 'vhs_rewind', {})], sfx=[('it knew who these two were', 'projector', -20)])

    B.clip('C01', zooms=[(1.0, 1.15)], y=0.4, tail=0.5, subs=True,
           events=[(wt('C01', 'No', 0), 'punch', dict(dur=1.6, amt=0.1))])

    # VO 22: ending
    B.vo('22', [
        (None, V(S1, 6795.5, 1.0, 1.04, freeze=True, grade=BW)),
        ('for those two', V(MCH, 3.0, 1.0, 1.12, grade=ARCH)),
    ], ovs=[('yesterday was 1962', ('+', 2.6), 'text', dict(txt='1962', y=0.5, size=200, color=(245, 240, 225), font='SpecialElite-Regular.ttf', stroke=0, anim='fade'))],
        sfx=[('for those two', 'projector', -18)], tail=1.6)
    B.ov('fade', B.t - 1.0, B.t, mode='out')
    B.gap(0.6, CARD(card_dark))
    return B.timeline()


if __name__ == '__main__':
    vo_dir, out = sys.argv[1], sys.argv[2]
    A = align_vo(vo_dir, vo_dir)
    tl = build(A)
    pickle.dump(tl, open(out, 'wb'))
    print('total', round(tl['total'], 2), 's  shots', len(tl['shots']), 'ovs', len(tl['ovs']))
