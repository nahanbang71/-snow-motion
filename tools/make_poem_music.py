#!/usr/bin/env python3
"""Synthesises the 96 s soundtrack for the 'A single butterfly' film (numpy only).
60 bpm, 4/4 -> 1 bar = 4 s, 24 bars. Bars follow the film's acts:
  1-4 dawn (sparse music-box)   5-8 meeting (tentative, lonely)   9-12 resting/bloom (gentle arpeggio)
  13-15 dance (livelier)        16-20 golden hour / heart (the theme)   21-24 goodbye (thins out, last note)
usage: python3 tools/make_poem_music.py out.wav
"""
import sys
import wave

import numpy as np

SR = 44100
DUR = 96.0
N = int(SR * (DUR + 4))
L = np.zeros(N)
R = np.zeros(N)
rng = np.random.default_rng(7)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def put(sig, t0, pan=0.0, gain=1.0):
    i = int(t0 * SR)
    if i < 0:
        sig, i = sig[-i:], 0
    if i >= N:
        return
    sig = sig[: N - i]
    l = gain * np.sqrt(.5 * (1 - pan))
    r = gain * np.sqrt(.5 * (1 + pan))
    L[i:i + len(sig)] += sig * l
    R[i:i + len(sig)] += sig * r


def bell(m, vel=.5, dur=5.0):
    f = hz(m)
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t / 1.9) * (1 - np.exp(-t / .004))
    s = (np.sin(2 * np.pi * f * t) + .45 * np.sin(2 * np.pi * 2.0 * f * t) * np.exp(-t / .7)
         + .22 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t / .4) + .12 * np.sin(2 * np.pi * 4.2 * f * t) * np.exp(-t / .22)
         + .06 * np.sin(2 * np.pi * 5.4 * f * t) * np.exp(-t / .12))
    return vel * .5 * s * env


def pluck(m, vel=.3, dur=2.4):
    f = hz(m)
    t = np.arange(int(dur * SR)) / SR
    s = np.zeros_like(t)
    for h in range(1, 7):
        s += (1.0 / h) * np.sin(2 * np.pi * f * h * t + rng.uniform(0, .3)) * np.exp(-t / (.9 / h ** .8))
    return vel * .5 * s * (1 - np.exp(-t / .003))


def pad(ms, dur, vel=.1):
    t = np.arange(int(dur * SR)) / SR
    env = np.minimum(1, t / 1.8) * np.minimum(1, (dur - t) / 2.2)
    env = np.clip(env, 0, 1) ** 1.3
    s = np.zeros_like(t)
    for m in ms:
        f = hz(m)
        for det in (-.0025, .0025):
            ff = f * (1 + det)
            s += np.sin(2 * np.pi * ff * t) + .3 * np.sin(2 * np.pi * 2 * ff * t) + .1 * np.sin(2 * np.pi * 3 * ff * t)
    trem = 1 + .06 * np.sin(2 * np.pi * .13 * t + rng.uniform(0, 6))
    return vel * s / max(1, len(ms)) * env * trem


def bass(m, dur, vel=.22):
    f = hz(m)
    t = np.arange(int(dur * SR)) / SR
    env = np.minimum(1, t / .9) ** 1.5 * np.exp(-t / 3.8) * np.minimum(1, (dur - t) / .9)
    return vel * (np.sin(2 * np.pi * f * t) + .25 * np.sin(2 * np.pi * 2 * f * t)) * env


CH = {  # voicing (pad), root
    'Cmaj7': ([55, 59, 64, 67], 36), 'Fmaj7': ([53, 57, 60, 64], 41), 'G': ([55, 59, 62, 67], 43),
    'Am7': ([57, 60, 64, 67], 45), 'Em7': ([55, 59, 62, 64], 40), 'C': ([55, 60, 64, 67], 36), 'F': ([53, 57, 60, 65], 41),
}
PROG = ['Cmaj7', 'Cmaj7', 'Fmaj7', 'G', 'Am7', 'Am7', 'Fmaj7', 'Fmaj7', 'Cmaj7', 'Em7', 'Fmaj7', 'G',
        'Am7', 'Fmaj7', 'C', 'G', 'F', 'G', 'Em7', 'Am7', 'Fmaj7', 'Cmaj7', 'Am7', 'Cmaj7']
BAR = 4.0


def tb(bar, beat):          # bar 1-based, beat 1-based (may be fractional) -> seconds
    return (bar - 1) * BAR + (beat - 1)


# ---- pads + bass ----
for b, name in enumerate(PROG, 1):
    ms, root = CH[name]
    lvl = .075 if b <= 4 else .095 if b <= 15 else .115 if b <= 20 else .085 * (1 - (b - 20) * .12)
    put(pad(ms, BAR + 2.2, lvl), tb(b, 1) - .4, pan=-.1)
    put(pad([m_ + 12 for m_ in ms[:3]], BAR + 2.2, lvl * .5), tb(b, 1) - .2, pan=.2)
    if b >= 9 and b <= 22:
        put(bass(root, BAR, (.07 + .018 * (b - 9)) if b < 15 else .13 if b < 21 else .09), tb(b, 1), pan=0)

# ---- melody (bars, beat, midi, velocity) ----
MEL = [
    # dawn: a few music-box notes, rising with the sun
    (1, 1, 76, .30), (1, 3.5, 71, .22), (2, 2, 79, .32), (2, 4, 76, .24), (3, 1, 81, .34), (3, 3, 72, .22), (4, 1, 83, .34), (4, 3.5, 74, .24),
    # meeting: tentative, lonely, lots of rests
    (5, 1, 72, .34), (5, 4, 76, .26), (6, 2, 74, .30), (6, 3.5, 72, .22), (7, 1, 69, .32), (7, 3, 72, .26), (8, 1, 76, .36), (8, 3.5, 74, .22),
    # rest / bloom
    (9, 1, 79, .34), (9, 3, 76, .24), (10, 1, 83, .30), (10, 3, 79, .24), (11, 1, 81, .32), (11, 3, 76, .24), (12, 1, 83, .32), (12, 3, 74, .26),
    # dance: livelier
    (13, 1, 81, .34), (13, 2, 79, .26), (13, 3, 76, .28), (13, 4, 79, .26), (14, 1, 81, .34), (14, 2, 84, .30), (14, 3, 77, .26), (14, 4, 76, .26),
    (15, 1, 79, .34), (15, 2, 76, .26), (15, 3, 72, .28), (15, 4, 76, .26),
    # golden hour / heart: the theme
    (16, 1, 83, .40), (16, 3, 86, .34), (16, 4, 81, .28), (17, 1, 84, .40), (17, 2, 81, .30), (17, 3, 77, .32), (17, 4, 81, .28),
    (18, 1, 83, .40), (18, 3, 79, .32), (18, 4, 74, .28), (19, 1, 76, .40), (19, 3, 79, .32), (19, 4, 83, .28), (20, 1, 81, .42), (20, 4, 76, .26),
    # goodbye: thins out
    (21, 1, 84, .34), (21, 3, 81, .26), (22, 1, 79, .30), (22, 3, 76, .22), (23, 1, 72, .26), (24, 1, 76, .26),
]
for bar, beat, m_, v in MEL:
    put(bell(m_, v), tb(bar, beat), pan=rng.uniform(-.25, .25))
    if 16 <= bar <= 20:   # theme doubled softly an octave below for warmth
        put(bell(m_ - 12, v * .35), tb(bar, beat), pan=-.15)

# ---- landing: bright chime + three ripples ----
for k, m_ in enumerate((84, 79, 76)):
    put(bell(m_, .38), tb(9, 1) + k * .14, pan=(-.3, 0, .3)[k])
put(bell(79, .30), 33.8, pan=-.2)
put(bell(76, .22), 35.6, pan=.2)

# ---- arpeggios: gentle (9-12), livelier (13-15), tender (16-20) ----
for b in range(9, 21):
    ms, _ = CH[PROG[b - 1]]
    notes = [m_ + 12 for m_ in ms]
    step = .25 if 13 <= b <= 15 else .5
    pat = [0, 1, 2, 3, 2, 1, 2, 1] if step == .5 else [0, 1, 2, 3, 2, 1, 2, 3, 1, 2, 3, 2, 1, 2, 0, 1]
    vel = .15 if b < 13 else .17 if b <= 15 else .13
    for k, idx in enumerate(pat):
        put(pluck(notes[idx % 4], vel * (1.15 if k % 4 == 0 else .85)), tb(b, 1) + k * step, pan=-.4 + .8 * (idx / 3))

# ---- sunrise shimmer at the very start; sparkles into the sun at 90 s; the last note ----
for k, m_ in enumerate((84, 88, 91, 96)):
    put(bell(m_, .12), 6.0 + k * 1.7, pan=rng.uniform(-.5, .5))
for k in range(9):
    m_ = int(rng.choice([88, 91, 93, 96, 100, 103]))
    put(bell(m_, .14 - k * .008, 4.0), 90.0 + k * .45, pan=rng.uniform(-.6, .6))
put(bell(76, .22, 6.0), 92.0, pan=0)
put(bell(84, .20, 7.0), 93.6, pan=.1)
put(pad([60, 64, 67, 72], 8, .09), 90.5)

# ---- reverb (synthetic stereo room) ----
irlen = int(3.4 * SR)
tt = np.arange(irlen) / SR
ir = []
for _ in range(2):
    n = rng.standard_normal(irlen) * np.exp(-tt / .95)
    k = np.cumsum(n)                      # gentle low-pass: darker tail
    n = n * .35 + (k - np.convolve(k, np.ones(200) / 200, mode='same')) * .02
    n[:int(.012 * SR)] *= np.linspace(0, 1, int(.012 * SR))
    ir.append(n / np.sqrt(np.sum(n ** 2)))


def verb(x, h):
    n = 1 << int(np.ceil(np.log2(len(x) + len(h))))
    return np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(h, n), n)[: len(x)]


wl, wr = verb(L, ir[0]), verb(R, ir[1])
oL = L * .62 + wl * .75
oR = R * .62 + wr * .75
oL, oR = oL[: int(DUR * SR)], oR[: int(DUR * SR)]
fade_in, fade_out = np.minimum(1, np.arange(len(oL)) / (1.2 * SR)), np.minimum(1, (len(oL) - np.arange(len(oL))) / (2.5 * SR))
g = fade_in * fade_out
oL, oR = oL * g, oR * g
peak = max(np.abs(oL).max(), np.abs(oR).max())
oL, oR = oL / peak * .70, oR / peak * .70
pcm = (np.stack([oL, oR], 1) * 32767).astype('<i2')
with wave.open(sys.argv[1] if len(sys.argv) > 1 else 'poem.wav', 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
rms = np.sqrt(np.mean(pcm.astype(float) ** 2)) / 32767
print('wrote', len(oL) / SR, 's, rms', round(float(rms), 3), 'peak', round(float(peak), 3))
