"""Synthesize the SFX library from scratch (no samples, no licensing issues, no music).
Run: python3 tools/sfx.py  -> writes assets/sfx/*.wav (48 kHz mono)"""
import numpy as np, wave, os

SR = 48000
rng = np.random.default_rng(7)
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "sfx")


def t(d): return np.arange(int(SR * d)) / SR
def noise(d): return rng.standard_normal(int(SR * d))


def env(n, a=0.005, r=0.2, curve=4.0):
    x = np.arange(n) / SR
    e = np.minimum(1, x / max(a, 1e-4)) * np.exp(-curve * np.maximum(0, x - a) / max(r, 1e-4))
    return e


def lp(x, cutoff):
    """one-pole low-pass; cutoff may be array"""
    c = np.broadcast_to(np.asarray(cutoff, float), x.shape)
    a = 1 - np.exp(-2 * np.pi * c / SR)
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)):
        s += a[i] * (x[i] - s); y[i] = s
    return y


def hp(x, cutoff): return x - lp(x, cutoff)


def bp(x, f, q=4):
    # state-variable band-pass, f may be array
    f = np.broadcast_to(np.asarray(f, float), x.shape)
    y = np.empty_like(x); low = band = 0.0; damp = 1 / q
    for i in range(len(x)):
        F = 2 * np.sin(np.pi * min(f[i], SR / 6) / SR)
        high = x[i] - low - damp * band
        band += F * high; low += F * band; y[i] = band
    return y


def tone(freq, d, shape="sine"):
    f = np.broadcast_to(np.asarray(freq, float), (int(SR * d),))
    ph = 2 * np.pi * np.cumsum(f) / SR
    if shape == "sine": return np.sin(ph)
    if shape == "square": return np.sign(np.sin(ph)) * 0.6
    if shape == "saw": return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if shape == "tri": return 2 * np.abs(2 * ((ph / (2 * np.pi)) % 1) - 1) - 1


def norm(x, peak=0.9):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def save(name, x, peak=0.9):
    os.makedirs(OUT, exist_ok=True)
    x = norm(x, peak)
    fade = min(len(x), int(0.004 * SR)); x[-fade:] *= np.linspace(1, 0, fade)
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def mix(*parts):
    n = max(len(p) for p in parts); y = np.zeros(n)
    for p in parts: y[:len(p)] += p
    return y


def pad(x, pre=0.0):
    return np.concatenate([np.zeros(int(pre * SR)), x])


def build():
    # whoosh: band-passed noise sweeping up then down
    d = 0.55; n = int(SR * d); x = np.linspace(0, 1, n)
    f = 300 + 2600 * np.sin(np.pi * x) ** 2
    save("whoosh", bp(noise(d), f, 2.5) * np.sin(np.pi * x) ** 1.5)
    d = 0.28; n = int(SR * d); x = np.linspace(0, 1, n)
    save("whoosh_short", bp(noise(d), 500 + 3500 * x, 2) * np.sin(np.pi * x))

    # impact: sub drop + click + noise tail
    d = 1.2; tt = t(d)
    sub = tone(90 * np.exp(-tt * 3) + 38, d) * env(len(tt), 0.002, 0.35)
    clk = lp(noise(d), 3000) * env(len(tt), 0.0005, 0.03, 6)
    save("impact", mix(sub * 1.0, clk * 0.6))
    d = 2.4; tt = t(d)
    sub = tone(70 * np.exp(-tt * 2) + 30, d) * env(len(tt), 0.003, 0.8)
    rum = lp(noise(d), 180) * env(len(tt), 0.01, 0.7) * 3
    clk = lp(noise(d), 4000) * env(len(tt), 0.0005, 0.05, 6)
    save("boom", mix(sub, rum, clk * 0.5))

    # riser: noise + rising tone, ends abruptly
    d = 1.6; tt = t(d); x = tt / d
    r = bp(noise(d), 400 + 5000 * x ** 2, 3) * x ** 2 + tone(200 + 900 * x ** 2, d, "saw") * 0.15 * x ** 3
    save("riser", r)

    # pop / bloop (underwater bubble)
    d = 0.12; tt = t(d)
    save("pop", tone(500 + 2500 * tt / d, d) * env(len(tt), 0.001, 0.03, 5))
    d = 0.18; tt = t(d)
    save("bloop", tone(250 + 1400 * (tt / d) ** 1.5, d) * env(len(tt), 0.002, 0.05, 4))
    bub = np.zeros(int(SR * 1.0))
    for k in range(9):
        d = 0.06 + rng.random() * 0.08; tt = t(d)
        b = tone((400 + rng.random() * 900) * (1 + 2.5 * tt / d), d) * env(len(tt), 0.002, d / 3)
        s = int(rng.random() * 0.8 * SR); bub[s:s + len(b)] += b * (0.5 + rng.random() * 0.5)
    save("bubbles", bub)

    # typewriter key + burst
    def key():
        d = 0.07; tt = t(d)
        return hp(noise(d), 1500) * env(len(tt), 0.0003, 0.012, 6) + tone(1800, d) * env(len(tt), 0.0003, 0.01, 6) * 0.3
    save("type", key())
    burst = np.zeros(int(SR * 0.9))
    for k in range(10):
        s = int((k * 0.075 + rng.random() * 0.02) * SR); kk = key() * (0.6 + 0.4 * rng.random())
        burst[s:s + len(kk)] += kk
    save("type_burst", burst)

    # ding (bell, inharmonic partials)
    d = 1.8; tt = t(d)
    bell = sum(a * tone(1320 * r, d) * np.exp(-tt * k) for a, r, k in
               [(1, 1, 2.2), (.6, 2.76, 3.5), (.4, 5.4, 5), (.25, 8.93, 7)])
    save("ding", bell * env(len(tt), 0.001, 3, 0.1))

    # cash register: drawer rattle + bell
    rattle = bp(noise(0.25), 2500, 3) * env(int(SR * .25), 0.001, 0.08)
    save("cha_ching", mix(rattle * 0.8, pad(bell[:int(SR * 1.2)] * 0.9, 0.12)))

    # record scratch: noise with fast pitch wobble
    d = 0.6; tt = t(d)
    f = 900 + 700 * np.sin(2 * np.pi * 9 * tt) * np.exp(-tt * 2)
    sc = bp(noise(d), f, 6) * env(len(tt), 0.002, 0.25) + tone(f * 0.4, d, "saw") * 0.15 * env(len(tt), 0.002, 0.2)
    save("scratch", sc)

    # camera shutter
    def clickk(): d = 0.03; tt = t(d); return hp(noise(d), 2000) * env(len(tt), 0.0002, 0.006, 6)
    save("shutter", mix(clickk(), pad(clickk() * 0.8, 0.09), pad(lp(noise(0.08), 3000) * 0.3 * env(int(SR * .08), .001, .03), 0.02)))

    # stamp: thud + paper slap
    d = 0.5; tt = t(d)
    thud = tone(110 * np.exp(-tt * 8) + 50, d) * env(len(tt), 0.001, 0.08, 5)
    slap = bp(noise(d), 1800, 1.5) * env(len(tt), 0.0005, 0.02, 6)
    save("stamp", mix(thud, slap * 0.8))

    # glitch: bit-crushed chopped bursts
    d = 0.45; g = np.zeros(int(SR * d)); pos = 0
    while pos < len(g):
        L = int(SR * (0.01 + rng.random() * 0.04))
        seg = tone(rng.choice([80, 160, 440, 880, 1760]) * (1 + rng.random()), L / SR, "square")
        if rng.random() < .4: seg = hp(noise(L / SR), 800)
        g[pos:pos + L] = seg[:len(g) - pos] * (rng.random() > .2); pos += L
    save("glitch", np.round(g * 6) / 6)

    # vhs rewind: warbly fast tones
    d = 1.0; tt = t(d)
    save("rewind", tone(1200 + 600 * np.sin(2 * np.pi * 23 * tt) + 800 * tt, d, "saw") * 0.4 * env(len(tt), 0.05, 2, 0.5)
         + hp(noise(d), 4000) * 0.2)

    # door slam
    d = 0.9; tt = t(d)
    slam = tone(65 * np.exp(-tt * 5) + 40, d) * env(len(tt), 0.001, 0.25) + lp(noise(d), 900) * env(len(tt), 0.001, 0.07, 6) * 1.2
    rat = bp(noise(d), 1400, 8) * env(len(tt), 0.05, 0.2) * 0.5
    save("door_slam", mix(slam, pad(rat, 0.03)))

    # slide whistle down (plankton's sad arc) + up
    d = 0.9; tt = t(d)
    f = 1400 * np.exp(-tt * 1.6) + 300 + 25 * np.sin(2 * np.pi * 6 * tt)
    save("slide_down", tone(f, d) * env(len(tt), 0.02, 2, 0.6))
    f = 300 + 1100 * (tt / d) ** 1.3
    save("slide_up", tone(f, d) * env(len(tt), 0.02, 2, 0.6))

    # wrong buzzer
    d = 0.6; tt = t(d)
    save("buzzer", (tone(140, d, "square") + tone(147, d, "square")) * env(len(tt), 0.005, 2, 0.3), 0.6)

    # counter tick (rolling numbers)
    d = 0.04; tt = t(d)
    save("tick", tone(2400, d) * env(len(tt), 0.0005, 0.01, 6))

    # tape stop
    d = 0.8; tt = t(d)
    f = 220 * (1 - tt / d) ** 2 + 10
    save("tape_stop", tone(f, d, "saw") * (1 - tt / d) + tone(f * 2, d) * 0.4 * (1 - tt / d))

    # pen scribble (for hand-drawn circles)
    d = 0.6; tt = t(d)
    am = 0.5 + 0.5 * np.sin(2 * np.pi * 11 * tt) ** 2
    save("scribble", bp(noise(d), 3000 + 1500 * np.sin(2 * np.pi * 7 * tt), 3) * am * env(len(tt), 0.02, 1, 1))

    # paper rip
    d = 0.7; tt = t(d)
    crack = np.zeros(len(tt))
    for k in range(60):
        s = int(rng.random() * len(tt) * 0.9); L = int(SR * .004)
        crack[s:s + L] += rng.standard_normal(L) * (0.3 + rng.random())
    save("rip", hp(crack + noise(d) * 0.15, 1200) * env(len(tt), 0.01, 0.5, 2))

    # heartbeat-like low thump (single)
    d = 0.35; tt = t(d)
    save("thump", tone(60 * np.exp(-tt * 6) + 35, d) * env(len(tt), 0.002, 0.08, 5))

    # balloon squeak (for the balloon callback)
    d = 0.5; tt = t(d)
    f = 900 + 300 * np.sin(2 * np.pi * 3 * tt) + 200 * tt
    save("squeak", bp(tone(f, d, "saw"), f * 1.5, 5) * env(len(tt), 0.02, 0.4, 2))

    # coin drop
    d = 0.6; tt = t(d)
    coin = sum(a * tone(f0, d) * np.exp(-tt * k) for a, f0, k in [(1, 4200, 9), (.7, 6100, 12), (.5, 2900, 7)])
    save("coin", mix(coin, pad(coin[:int(SR * .3)] * .5, 0.11), pad(coin[:int(SR * .2)] * .3, 0.19)))

    # silence-break "ring" (tinnitus after big hit)
    d = 1.5; tt = t(d)
    save("ring", tone(3800, d) * env(len(tt), 0.01, 1.4, 1) * 0.5)

    # paper slide: soft band-passed swish with fibre crackle
    d = 0.42; tt = t(d); x = tt / d
    sw = bp(noise(d), 1800 + 1800 * x, 1.2) * np.sin(np.pi * x) ** 1.2
    cr = np.zeros(len(tt))
    for k in range(25):
        s0 = int(rng.random() * len(tt) * .9); L = int(SR * .003); cr[s0:s0 + L] += rng.standard_normal(L) * .5
    save("paper", sw + hp(cr, 2500) * .6, 0.7)
    # pin into board: tiny click + soft thud
    d = 0.18; tt = t(d)
    save("pin", hp(noise(d), 3000) * env(len(tt), 0.0003, 0.008, 6) + tone(140 * np.exp(-tt * 20) + 60, d) * env(len(tt), 0.001, 0.04, 5) * .6, 0.7)

    # crowd gasp substitute: short reversed noise swell
    d = 0.6; tt = t(d)
    save("reverse_swell", (lp(noise(d), 2500) * (tt / d) ** 3))


if __name__ == "__main__":
    build()
    print("sfx:", sorted(os.listdir(OUT)))
