# Constellation videos — 10 places × 4 constellations = 40 clips

Each clip: 16 s, 1920×1080, 30 fps, English text only, no audio.

1. A wide, far-away night sky over the place (about 40,000 real Hipparcos stars). Only the *rooftops* of buildings / tops of objects show above the horizon.
2. The constellation lines are drawn star to star like a laser.
3. When the last line closes, the stars **twinkle** (cross-shaped flares).
4. The constellation name appears at the top (Latin, with the common English name underneath), then each named star gets its name.

| Place | Constellations |
|---|---|
| 01 desert | Scorpius, Leo, Crux, Cancer |
| 02 snow_mountain | Ursa Major, Ursa Minor, Cassiopeia, Cepheus |
| 03 beach | Delphinus, Pisces, Aquarius, Piscis Austrinus |
| 04 forest | Lyra, Cygnus, Aquila, Sagitta |
| 05 city | Orion, Gemini, Canis Major, Canis Minor |
| 06 grassland | Bootes, Virgo, Libra, Corona Borealis |
| 07 lake | Pegasus, Andromeda, Perseus, Aries |
| 08 hanok_village | Taurus, Auriga, Lepus, Cetus |
| 09 volcano | Sagittarius, Capricornus, Ophiuchus, Corvus |
| 10 polar | Draco, Hercules, Centaurus, Lacerta |

Files
- `clips/NN_place/N_Constellation.mp4` — the 40 clips
- `constellations_part1_places01-05.mp4`, `constellations_part2_places06-10.mp4` — places 01–05 and 06–10 joined (5:20 each, short fades between clips)

Rebuild
- `python3 tools/prep_constellations.py <d3-celestial/data>` → `data.js`
- `node tools/render_constellation.js <0-39>` renders one clip (see `scenes.js` for the places and the drawing code)

Data credit: star positions, constellation lines and names come from d3-celestial (Copyright (c) 2015, Olaf Frohn, BSD-3-Clause), which is based on the Hipparcos catalogue.
