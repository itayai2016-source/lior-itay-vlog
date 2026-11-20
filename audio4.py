import numpy as np, wave
SR = 44100
DUR = 293.0
N = int(SR*DUR)
music = np.zeros(N); sfx = np.zeros(N)
rng = np.random.default_rng(4)

def addto(buf, sig, t, gain=1.0):
    i = int(t*SR)
    if i >= N or i + len(sig) <= 0: return
    j = min(N, i+len(sig)); buf[i:j] += sig[:j-i]*gain
def env(n, a=0.005, r=0.1):
    e = np.ones(n); na = min(n, max(1, int(a*SR))); nr = min(n, max(1, int(r*SR)))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e
def tone(f, d, kind="sq", vol=1.0, r=0.05, a=0.005):
    n = int(d*SR); t = np.arange(n)/SR
    ph = 2*np.pi*np.cumsum(f(t))/SR if callable(f) else 2*np.pi*f*t
    if kind == "sq": s = np.sign(np.sin(ph))*0.5
    elif kind == "tri": s = 2/np.pi*np.arcsin(np.sin(ph))
    elif kind == "saw": s = 2*((ph/(2*np.pi)) % 1) - 1
    else: s = np.sin(ph)
    return s*env(n, a=a, r=r)*vol
def noise(d, vol=1.0, decay=30):
    n = int(d*SR); return rng.uniform(-1, 1, n)*np.exp(-np.arange(n)/SR*decay)*vol
def lowpass(x, k=8):
    c = np.cumsum(np.insert(x, 0, 0)); return (c[k:] - c[:-k])/k
def midi(m): return 440*2**((m-69)/12)

# ------------- music styles -------------
def kick(t, v=0.6): addto(music, tone(lambda x: 150*np.exp(-x*25)+45, 0.18, "sin", v), t)
def snare(t, v=0.25): addto(music, noise(0.15, v, 25), t)
def hat(t, v=0.1): addto(music, noise(0.04, v, 90), t)

def style_fun(t0, t1, seed=0):
    bpm = 128; beat = 60/bpm
    chords = [48, 43, 45, 41]
    mel = [72,74,76,79, 79,76,74,72, 71,74,79,74, 76,72,69,72, 72,76,77,76, 74,72,71,74, 72,76,81,79, 77,76,74,72]
    t = t0; k = seed*8
    while t < t1 - 0.05:
        b = int(round((t-t0)/beat)); root = chords[(b//4) % 4]
        addto(music, tone(midi(root if b % 2 == 0 else root+12), beat*0.9, "sq", 0.16), t)
        hat(t + beat/2)
        if b % 4 in (0, 2): kick(t)
        else: snare(t)
        for h in range(2):
            addto(music, tone(midi(mel[k % len(mel)]), beat*0.45, "tri", 0.15), t + h*beat/2); k += 1
        t += beat

def style_party(t0, t1):
    bpm = 140; beat = 60/bpm
    roots = [45, 41, 48, 43]
    riff = [69,72,76,72, 69,72,77,72, 67,71,74,71, 67,71,76,74]
    t = t0; k = 0
    while t < t1 - 0.05:
        b = int(round((t-t0)/beat)); root = roots[(b//4) % 4]
        kick(t, 0.7); hat(t + beat/2, 0.14)
        if b % 2: snare(t, 0.22)
        for h in range(2): addto(music, tone(midi(root + (12 if h else 0)), beat*0.45, "sq", 0.15), t + h*beat/2)
        addto(music, tone(midi(riff[k % len(riff)]), beat*0.4, "sq", 0.09), t); k += 1
        addto(music, tone(midi(riff[k % len(riff)]+12), beat*0.3, "tri", 0.08), t + beat/2)
        t += beat

def style_epic(t0, t1, major=False):
    bpm = 112; beat = 60/bpm
    prog = [(57,[69,72,76]), (53,[69,72,77]), (48,[67,72,76]), (55,[67,71,74])] if not major else \
           [(48,[67,72,76]), (55,[67,71,74]), (57,[69,72,76]), (53,[69,72,77])]
    t = t0
    while t < t1 - 0.05:
        b = int(round((t-t0)/beat)); root, ch = prog[(b//4) % 4]
        if b % 4 == 0:
            d = min(beat*4, t1-t)
            for m in ch: addto(music, tone(midi(m), d, "saw", 0.045, r=0.3, a=0.05), t)
            addto(music, tone(midi(root-12), d, "tri", 0.3, r=0.3), t)
        kick(t, 0.75)
        if b % 2: snare(t, 0.3)
        if b % 4 == 3:
            for i in range(3): addto(music, tone(lambda x: 120*np.exp(-x*10)+70, 0.2, "sin", 0.35), t + i*beat/3)
        hat(t + beat/2, 0.08)
        t += beat

def style_tension(t0, t1):
    beat = 60/100
    t = t0
    while t < t1 - 0.05:
        b = int(round((t-t0)/(beat/2)))
        addto(music, tone(midi(33 if (b//8) % 2 == 0 else 34), beat*0.4, "sq", 0.2), t)
        if b % 2 == 0: addto(music, tone(1800, 0.02, "sq", 0.06), t)
        if b % 8 == 0: kick(t, 0.5)
        t += beat/2

def style_calm(t0, t1):
    beat = 60/90
    prog = [[60,64,67,72], [55,59,62,67], [57,60,64,69], [53,57,60,65]]
    t = t0
    while t < t1 - 0.05:
        b = int(round((t-t0)/(beat/2))); ch = prog[(b//8) % 4]
        addto(music, tone(midi(ch[b % 4]), beat*0.9, "tri", 0.13, r=0.3), t)
        if b % 8 == 0: addto(music, tone(midi(ch[0]-24), beat*4, "sin", 0.25, r=0.8), t)
        t += beat/2

def drumroll(t0, d, vol=0.35):
    n = int(d*SR); x = rng.uniform(-1, 1, n)
    trem = 0.5 + 0.5*np.sign(np.sin(2*np.pi*28*np.arange(n)/SR))
    e = np.linspace(0.3, 1, n)
    addto(sfx, x*trem*e*vol, t0)

def fade(t0, t1, g0, g1):
    i, j = int(t0*SR), int(t1*SR); music[i:j] *= np.linspace(g0, g1, j-i)
def mute(t0, t1, g=0.06):
    i, j = int(t0*SR), int(t1*SR); music[i:j] *= g

# ------------- sfx -------------
def S(sig, t, g=1.0): addto(sfx, sig, t, g)
def pop(t): S(tone(lambda x: 400+1600*x/0.08, 0.08, "sin", 0.5, r=0.03), t)
def boing(t): S(tone(lambda x: 180+120*np.sin(x*40)*np.exp(-x*4)+x*200, 0.4, "sin", 0.55, r=0.15), t)
def whoosh(t, v=0.35): n = noise(0.35, v, 6); n *= np.sin(np.linspace(0, np.pi, len(n))); S(n, t)
def ding(t):
    for f, v in ((1318, 0.35), (1760, 0.25)): S(tone(f, 0.6, "sin", v, r=0.5), t)
    S(tone(1046, 0.6, "sin", 0.2, r=0.5), t+0.08)
def tick(t): S(tone(1800, 0.03, "sq", 0.2, r=0.02), t)
def beep(t, f=880): S(tone(f, 0.18, "sq", 0.3), t)
def whistle_down(t): S(tone(lambda x: 1400 - 1000*x/0.6, 0.6, "sin", 0.35), t)
def clank(t):
    for f in (2200, 3100, 4700): S(tone(f, 0.25, "sin", 0.18, r=0.24), t)
def crunch(t):
    for i in range(5): S(noise(0.04, 0.5, 60), t + i*0.03)
def thud(t, v=0.9): S(tone(lambda x: 90*np.exp(-x*6)+40, 0.4, "sin", v), t); S(noise(0.2, 0.4*v, 20), t)
def slip(t): S(tone(lambda x: 300 + 1500*x/0.5, 0.5, "sin", 0.35), t)
def sad(t):
    for i, m in enumerate([62, 61, 60]): S(tone(midi(m), 0.25, "sq", 0.18), t + i*0.25)
    S(tone(lambda x: midi(59)*(1-0.03*x), 0.6, "sq", 0.18, r=0.3), t+0.75)
def laugh(t):
    for i in range(6): S(tone(lambda x: 520 - 300*x, 0.11, "sq", 0.12, r=0.05), t + i*0.16)
def swish(t): n = noise(0.3, 0.3, 10); S(n*np.linspace(0.2, 1, len(n)), t)
def scratch(t): S(tone(lambda x: 900 - 700*x/0.35, 0.35, "sq", 0.25), t); S(noise(0.35, 0.3, 4), t)
def boom(t): S(tone(lambda x: 70*np.exp(-x*3)+30, 1.2, "sin", 1.0, r=0.8), t); S(noise(1.0, 0.5, 4), t)
def burst(t, v=0.35):
    S(noise(0.6, v, 7), t)
    for i in range(8): S(noise(0.03, v*0.6, 80), t + 0.15 + i*0.07 + rng.uniform(0, 0.04))
def cheer(t, d=3.0, v=0.25):
    n = int(d*SR); x = lowpass(rng.uniform(-1, 1, n+6), 6)[:n]
    e = np.sin(np.linspace(0, np.pi, n))**0.6
    S(x*e*v*3, t)
    for i in range(int(d*3)): S(noise(0.05, 0.08, 40), t + rng.uniform(0, d))
def clap(t): S(noise(0.06, 0.8, 70), t)
def crash(t): S(noise(2.0, 0.45, 2.2), t)
def chime(t):
    for i, m in enumerate([84, 88, 91, 96]): S(tone(midi(m), 0.4, "sin", 0.15, r=0.35), t + i*0.06)
def fanfare(t):
    for i, m in enumerate([67, 72, 76, 79]): S(tone(midi(m), 0.16 if i < 3 else 0.7, "sq", 0.22, r=0.08 if i < 3 else 0.5), t + i*0.13)

# ------------- timeline -------------
O = dict(open=0, recap=16, host=37, spoon=51, basket=71, bottle=101, dance=123, half=155, lemon=167, final=185, bloop=213, cer=243, cred=269)

style_tension(0, 3); style_epic(3, 16)
style_calm(16, 37)
style_fun(37, 51)
style_fun(51, 55); style_tension(55, 63); style_fun(63, 71, seed=1)
style_fun(71, 101, seed=2); style_fun(101, 123, seed=3)
style_party(123, 155)
style_calm(155, 167)
style_tension(167, 185)
style_party(185, 198); style_epic(207.5, 213, major=True)
style_fun(213, 243, seed=4)
style_epic(243, 269, major=True)
style_calm(269, 293)
fade(0, 0.5, 0, 1); fade(290.5, 293, 1, 0)
mute(O["lemon"]+6.0, O["lemon"]+9.2, 0.15)
mute(O["cer"], O["cer"]+3.0, 0.1)

# open
for i in range(3): beep(i, 440)
boom(3.0)
for t0 in (3.0, 3.5, 4.1, 5.0, 5.6, 9.8, 12.0, 12.4): burst(t0 + 0.45)
cheer(3.2, 4.0); whoosh(6.5); whoosh(6.8); chime(9.0); cheer(11.5, 3.0)
# recap
for t0 in (16, 19, 25, 31): whoosh(t0)
# host
cheer(O["host"]+10, 2.5); pop(O["host"]+10)
# spoon
o = O["spoon"]; whoosh(o)
for s_ in range(8): tick(o + 4 + s_)
whistle_down(o + 11.6); clank(o + 12.05); ding(o + 12.4); cheer(o + 12.4, 2.5, 0.18)
# basket
o = O["basket"]; whoosh(o)
for w, t0, r in [("I", 3.0, "in"), ("L", 6.5, "in"), ("I", 10.0, "in"), ("L", 13.5, "rim"), ("I", 17.0, "miss"), ("L", 20.5, "rim")]:
    whoosh(o + t0, 0.2)
    if r == "in": swish(o + t0 + 0.75); chime(o + t0 + 0.85)
    elif r == "rim": clank(o + t0 + 0.8); boing(o + t0 + 0.82)
    else: thud(o + t0 + 0.8, 0.4)
ding(o + 24.5); cheer(o + 24.5, 2.5, 0.18)
# bottle
o = O["bottle"]; whoosh(o)
for t0, ok in ((3.0, True), (6.0, True), (9.0, True), (12.0, False)):
    whoosh(o + t0, 0.2)
    if ok: clank(o + t0 + 0.8)
    else: thud(o + t0 + 0.8); sad(o + t0 + 0.9)
ding(o + 13.5)
# dance
o = O["dance"]; whoosh(o)
cheer(o + 11.5, 2.0); whoosh(o + 18.0); cheer(o + 18.6, 2.0); cheer(o + 26.5, 3.5, 0.3); ding(o + 29.5)
# half
cheer(O["half"], 3.0, 0.12)
# lemon
o = O["lemon"]; whoosh(o)
for s_ in range(3): beep(o + 3 + s_)
beep(o + 6, 1320); crunch(o + 6); boing(o + 9.2); sad(o + 9.6)
# final
o = O["final"]; whoosh(o)
scratch(o + 13); whoosh(o + 13.1); thud(o + 13.6)
drumroll(o + 15.5, 5.0); ding(o + 20.5); crash(o + 22.5); fanfare(o + 22.5); cheer(o + 22.5, 4.0, 0.3)
# bloopers
o = O["bloop"]
for k in range(4): clap(o + k*7.5)
slip(o + 2.7); thud(o + 3.6); laugh(o + 3.3); laugh(o + 4.5)
b = o + 7.5; boing(b + 2.4); thud(b + 3.6); laugh(b + 3.9)
b = o + 15; clank(b + 1.6); thud(b + 1.6); thud(b + 2.1, 0.6); laugh(b + 4.1); laugh(b + 4.8)
b = o + 22.5; boing(b + 2.0); whoosh(b + 2.0); thud(b + 2.8); laugh(b + 3.1)
# ceremony
o = O["cer"]
drumroll(o, 3.0); crash(o + 3.0); fanfare(o + 3.05); cheer(o + 3.0, 6.0, 0.3)
for t0 in (3.0, 3.3, 3.7, 6.0, 6.3, 9.0, 9.4, 19.0, 19.5, 20.0): burst(o + t0 + 0.45, 0.25)
chime(o + 6.0); cheer(o + 19.0, 5.0, 0.25)
# credits
pop(O["cred"] + 18.0); chime(O["cred"] + 18.0)

out = np.tanh((music*0.75 + sfx)*0.9)*0.9
fo = int(1.0*SR); out[-fo:] *= np.linspace(1, 0, fo)
pcm = (out*32767).astype(np.int16)
st = np.repeat(pcm[:, None], 2, axis=1)
with wave.open("ep4/audio.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
print("ok", len(out)/SR)
