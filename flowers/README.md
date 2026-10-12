# Neon Flowers

121 animated neon line-art SVGs (`flowers/svg/*.svg`) + gallery (`flowers/index.html`).

- 100 new flowers + colour variants of the reference video's rose / tulip / sunflower / cherry blossom / lotus / daisy
- Each file is self-contained: stem draws first, then the head, then English name, meaning and Korean name
- Colours are CSS variables on the root `<svg>` (`--c`, `--c2`), so recolouring is a one-line edit

Regenerate everything: `python3 tools/gen_flowers.py` (shapes in `tools/flower_shapes.py`,
flower list/colours/meanings in `tools/gen_flowers.py`).
