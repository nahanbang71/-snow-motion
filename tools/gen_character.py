#!/usr/bin/env python3
"""2D 'Character Builder' animated SVG -> character/character_builder.svg
usage: python3 tools/gen_character.py
render: node tools/render_svg_video.js character/character_builder.svg character/character_builder.mp4 20 1280 720
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'character')
DUR = 20  # seconds, one full cycle

SKIN, HAIR, CAP = '#f3c8a8', '#3a2a24', '#5a4036'


def kf(name, pts, prop):
    """pts: [(percent, value)] -> @keyframes; prop is a css template with {v}"""
    body = ''.join(f'{p}%{{{prop.format(v=v)}}}' for p, v in pts)
    return f'@keyframes {name}{{{body}}}'


def knob(frac):
    return f'transform:translateX({frac * 260:.1f}px)'


css = [
    # background / outfit colour changes
    kf('bg', [(0, '#d9d1c5'), (50, '#d9d1c5'), (56, '#e8863a'), (68, '#e8863a'), (74, '#1e7fe0'),
              (84, '#1e7fe0'), (88, '#8fc7c9'), (94, '#8fc7c9'), (99, '#d9d1c5'), (100, '#d9d1c5')], 'fill:{v}'),
    kf('hood', [(0, '#4a3b33'), (50, '#4a3b33'), (56, '#6a3a24'), (68, '#6a3a24'), (74, '#17407a'),
                (84, '#17407a'), (88, '#4a3b33'), (100, '#4a3b33')], 'fill:{v}'),
    # head size / height / body shape (slider values)
    kf('head', [(0, 1), (15, 1), (22, 1.45), (34, 1.45), (41, 1), (80, 1), (85, .85), (90, .85), (96, 1), (100, 1)],
       'transform:scale({v})'),
    kf('tall', [(0, 1), (42, 1), (50, 1.12), (62, 1.12), (70, 1), (100, 1)], 'transform:scale({v})'),
    kf('wide', [(0, 1), (62, 1), (68, 1.25), (78, 1.25), (84, 1), (100, 1)], 'transform:scaleX({v})'),
    kf('k_head', [(0, knob(.33)), (15, knob(.33)), (22, knob(.83)), (34, knob(.83)), (41, knob(.33)),
                  (80, knob(.33)), (85, knob(.17)), (90, knob(.17)), (96, knob(.33)), (100, knob(.33))], '{v}'),
    kf('k_body', [(0, knob(.33)), (62, knob(.33)), (68, knob(.75)), (78, knob(.75)), (84, knob(.33)), (100, knob(.33))], '{v}'),
    kf('k_tall', [(0, knob(.4)), (42, knob(.4)), (50, knob(.75)), (62, knob(.75)), (70, knob(.4)), (100, knob(.4))], '{v}'),
    # swatch rings
    kf('r_beige', [(0, 1), (52, 1), (56, 0), (96, 0), (99, 1), (100, 1)], 'opacity:{v}'),
    kf('r_orange', [(0, 0), (55, 0), (58, 1), (70, 1), (73, 0), (100, 0)], 'opacity:{v}'),
    kf('r_blue', [(0, 0), (73, 0), (76, 1), (85, 1), (87, 0), (100, 0)], 'opacity:{v}'),
    kf('r_teal', [(0, 0), (87, 0), (89, 1), (95, 1), (97, 0), (100, 0)], 'opacity:{v}'),
    # expressions
    kf('m_smile', [(0, 1), (19, 1), (21, 0), (35, 0), (37, 1), (68, 1), (70, 0), (88, 0), (90, 1), (100, 1)], 'opacity:{v}'),
    kf('m_puff', [(0, 0), (19, 0), (21, 1), (35, 1), (37, 0), (100, 0)], 'opacity:{v}'),
    kf('m_smirk', [(0, 0), (68, 0), (70, 1), (88, 1), (90, 0), (100, 0)], 'opacity:{v}'),
    kf('blush', [(0, .55), (20, .55), (24, 1), (34, 1), (40, .55), (100, .55)], 'opacity:{v}'),
    # raised waving arm
    kf('arm', [(0, -8), (24, -8), (28, -125), (30, -105), (32, -125), (34, -105), (36, -125), (40, -8), (100, -8)],
       'transform:rotate({v}deg)'),
    # idle loops
    '@keyframes blink{0%,92%,100%{transform:scaleY(1)}95%{transform:scaleY(.1)}}',
    '@keyframes breathe{0%,100%{transform:scaleY(1)}50%{transform:scaleY(1.018)}}',
    '@keyframes tilt{0%,100%{transform:rotate(-2.5deg)}50%{transform:rotate(2.5deg)}}',
    '@keyframes look{0%,100%{transform:translateX(-2px)}50%{transform:translateX(3px)}}',
    '@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}',
    f'.bg{{animation:bg {DUR}s linear infinite}}',
    f'.hood{{animation:hood {DUR}s linear infinite}}',
    f'.tall{{transform-origin:400px 640px;animation:tall {DUR}s ease-in-out infinite}}',
    f'.wide{{transform-origin:400px 450px;animation:wide {DUR}s ease-in-out infinite}}',
    f'.head{{transform-origin:400px 300px;animation:head {DUR}s ease-in-out infinite}}',
    '.tilt{transform-origin:400px 300px;animation:tilt 4s ease-in-out infinite}',
    '.breathe{transform-origin:400px 640px;animation:breathe 3s ease-in-out infinite}',
    '.bob{animation:bob 3s ease-in-out infinite}',
    f'.arm{{transform-origin:480px 312px;animation:arm {DUR}s ease-in-out infinite}}',
    '.eye{transform-origin:0 0;animation:blink 4s ease-in-out infinite}',
    '.look{animation:look 6s ease-in-out infinite}',
    f'.blush{{animation:blush {DUR}s ease-in-out infinite}}',
    f'.k_head{{animation:k_head {DUR}s ease-in-out infinite}}',
    f'.k_body{{animation:k_body {DUR}s ease-in-out infinite}}',
    f'.k_tall{{animation:k_tall {DUR}s ease-in-out infinite}}',
    f'.r_beige{{animation:r_beige {DUR}s linear infinite}}',
    f'.r_orange{{animation:r_orange {DUR}s linear infinite}}',
    f'.r_blue{{animation:r_blue {DUR}s linear infinite}}',
    f'.r_teal{{animation:r_teal {DUR}s linear infinite}}',
    f'.m_smile{{animation:m_smile {DUR}s linear infinite}}',
    f'.m_puff{{animation:m_puff {DUR}s linear infinite}}',
    f'.m_smirk{{animation:m_smirk {DUR}s linear infinite}}',
    'text{font-family:Helvetica,Arial,sans-serif;fill:#3a3a3a}',
]


def slider(y, label, lo, hi, cls):
    return f'''<text x="880" y="{y - 12}" font-size="14" font-weight="600">{label}</text>
<rect x="880" y="{y}" width="260" height="4" rx="2" fill="#3a3a3a" opacity=".35"/>
<circle class="{cls}" cx="880" cy="{y + 2}" r="8" fill="#3a3a3a"/>
<text x="880" y="{y + 24}" font-size="11" opacity=".6">{lo}</text>
<text x="1140" y="{y + 24}" font-size="11" opacity=".6" text-anchor="end">{hi}</text>'''


swatches = ['#ffffff', '#f28c28', '#f6c945', '#ec4899', '#8b5cf6', '#3b82f6']
bgs = [('r_beige', '#d9d1c5'), (None, '#ffffff'), ('r_orange', '#e8863a'), ('r_blue', '#1e7fe0'),
       ('r_teal', '#8fc7c9'), (None, '#7fb069'), (None, '#f2c14e')]

panel = ['<g>',
         '<text x="880" y="70" font-size="30" font-weight="800" opacity=".85">Magnific</text>',
         '<text x="880" y="150" font-size="11" opacity=".6">Character Builder</text>',
         '<text x="880" y="170" font-size="16" font-weight="700">Nieve · 2D</text>',
         slider(210, 'Head size', 'Smaller', 'Bigger', 'k_head'),
         slider(290, 'Body shape', 'Lean', 'Stocky', 'k_body'),
         slider(370, 'Height', 'Shorter', 'Taller', 'k_tall'),
         '<text x="880" y="438" font-size="13" font-weight="600">Colour / lighting</text>']
for i, c in enumerate(swatches):
    panel.append(f'<circle cx="{890 + i * 34}" cy="460" r="11" fill="{c}" stroke="#3a3a3a" stroke-opacity=".2"/>')
panel.append('<text x="880" y="508" font-size="13" font-weight="600">Background</text>')
for i, (ring, c) in enumerate(bgs):
    x = 890 + i * 34
    panel.append(f'<circle cx="{x}" cy="530" r="11" fill="{c}" stroke="#3a3a3a" stroke-opacity=".2"/>')
    if ring:
        panel.append(f'<circle class="{ring}" cx="{x}" cy="530" r="15" fill="none" stroke="#3a3a3a" stroke-width="2"/>')
panel.append('<rect x="880" y="580" width="260" height="30" rx="15" fill="none" stroke="#3a3a3a" stroke-opacity=".5"/>'
             '<text x="1010" y="600" font-size="12" text-anchor="middle">Back to original</text></g>')

character = f'''
<ellipse cx="400" cy="640" rx="130" ry="14" fill="#000" opacity=".18"/>
<g class="tall"><g class="breathe">
  <g class="wide">
    <!-- legs -->
    <path d="M350 440h46v180h-52z" fill="#6b6a3c"/><path d="M404 440h46l8 180h-52z" fill="#6b6a3c"/>
    <rect x="352" y="520" width="34" height="28" rx="5" fill="#5c5b33"/><rect x="414" y="520" width="34" height="28" rx="5" fill="#5c5b33"/>
    <ellipse cx="338" cy="628" rx="34" ry="14" fill="#e8e4dc"/><ellipse cx="470" cy="628" rx="34" ry="14" fill="#e8e4dc"/>
    <rect x="310" y="618" width="52" height="8" rx="4" fill="#9a8f80"/><rect x="444" y="618" width="52" height="8" rx="4" fill="#9a8f80"/>
    <!-- left arm (hand in pocket) -->
    <path class="hood" d="M324 316c-26 8-30 60-20 120l34 8c-2-40 4-80 14-110z"/>
    <!-- hoodie -->
    <rect class="hood" x="320" y="290" width="160" height="170" rx="46"/>
    <path d="M360 292q40 34 80 0l6 14q-46 44-92 0z" fill="#000" opacity=".18"/>
    <path d="M388 330v46M412 330v46" stroke="#e9dfd2" stroke-width="3" stroke-linecap="round"/>
    <path d="M340 410q60 30 120 0v30q-60 26-120 0z" fill="#000" opacity=".12"/>
  </g>
  <!-- right arm: waves -->
  <g class="arm">
    <rect class="hood" x="466" y="296" width="38" height="132" rx="19"/>
    <circle cx="485" cy="440" r="19" fill="{SKIN}"/>
  </g>
  <!-- head -->
  <g class="bob"><g class="tilt"><g class="head">
    <rect x="388" y="262" width="24" height="44" fill="#e3b494"/>
    <path d="M318 215c-4-70 40-104 82-104s86 34 82 104c4 40 0 80 10 96-24 14-52 8-62-14H370c-10 22-38 28-62 14 10-16 6-56 10-96z" fill="{HAIR}"/>
    <ellipse cx="400" cy="214" rx="74" ry="82" fill="{SKIN}"/>
    <!-- bangs -->
    <path d="M326 190c20-28 52-36 74-34 30 0 56 12 74 38-22-8-46-12-74-10-30 0-52 4-74 6z" fill="{HAIR}"/>
    <!-- cap -->
    <path d="M326 168c-4-56 34-84 76-84s80 28 74 84c-26-12-50-16-76-16s-50 4-74 16z" fill="{CAP}"/>
    <path d="M318 170q82-26 164 0l-6 12q-76-20-152 0z" fill="#3e2b24"/>
    <circle cx="372" cy="128" r="7" fill="#e9dfd2" opacity=".85"/>
    <!-- eyes -->
    <g class="look">
      <g transform="translate(366 218)"><g class="eye"><ellipse rx="13" ry="15" fill="#fff"/><circle r="9" fill="#3a2418"/><circle cx="3" cy="-4" r="3" fill="#fff"/></g></g>
      <g transform="translate(434 218)"><g class="eye"><ellipse rx="13" ry="15" fill="#fff"/><circle r="9" fill="#3a2418"/><circle cx="3" cy="-4" r="3" fill="#fff"/></g></g>
    </g>
    <path d="M350 196q16-10 32 0M418 196q16-10 32 0" stroke="{HAIR}" stroke-width="4" fill="none" stroke-linecap="round"/>
    <g class="blush"><ellipse cx="346" cy="250" rx="20" ry="13" fill="#ef6f78"/><ellipse cx="454" cy="250" rx="20" ry="13" fill="#ef6f78"/></g>
    <!-- mouths -->
    <path class="m_smile" d="M384 262q16 14 32 0" stroke="#a0463e" stroke-width="4" fill="none" stroke-linecap="round"/>
    <ellipse class="m_puff" cx="400" cy="266" rx="7" ry="9" fill="#c4584f"/>
    <path class="m_smirk" d="M384 266q20 8 34-6" stroke="#a0463e" stroke-width="4" fill="none" stroke-linecap="round"/>
  </g></g></g>
</g></g>'''

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
<style>{''.join(css)}</style>
<defs><radialGradient id="floor" cx=".3" cy=".95" r=".6"><stop offset="0" stop-color="#fff" stop-opacity=".45"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient></defs>
<rect class="bg" width="1280" height="720" fill="#d9d1c5"/>
<rect width="1280" height="720" fill="url(#floor)"/>
{character}
{''.join(panel)}
</svg>'''

os.makedirs(OUT, exist_ok=True)
path = os.path.join(OUT, 'character_builder.svg')
open(path, 'w', encoding='utf-8').write(svg)
print('wrote', os.path.relpath(path))
