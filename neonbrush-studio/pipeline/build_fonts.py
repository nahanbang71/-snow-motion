#!/usr/bin/env python3
"""Batch converter: every .zip (or folder) in <packs> -> output_fonts/<Family>/{.ttf,.otf,-Color.otf,specimen,report}

  python3 pipeline/build_fonts.py                       # ../packs  ->  ../output_fonts
  python3 pipeline/build_fonts.py my.zip other/ -o out  # explicit inputs
Options: --color auto|all|none   --no-lower   --only TEXT   --overrides FILE   --webpacks DIR   --watermarks DIR
"""
import argparse
import json
import os
import shutil
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from nbfont import packs as pk, build, specimen, verify, webpack  # noqa: E402

ROOT = os.path.dirname(HERE)


def convert_one(p, o):
    """Build + verify one pack. Returns (log text, ok, (name, n_glyphs, files, ok) | None). Runs in a worker process."""
    import io
    import contextlib
    t0 = time.time()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            outdir = os.path.join(o['out'], p.name)
            r = build.build_pack(p, outdir, color=o['color'], svg_px=o['svg_px'], lower=o['lower'])
            checks = [verify.verify(r['files']['ttf'], r['chars']), verify.verify(r['files']['otf'], r['chars'])]
            if 'color' in r['files']:
                checks.append(verify.verify(r['files']['color'], r['chars'], color=True))
            specimen.mono(r['files']['ttf'], os.path.join(outdir, 'specimen.png'))
            if 'color' in r['files']:
                specimen.color(r['arrays'], r['place'], os.path.join(outdir, 'specimen_color.png'))
            if o['webpacks']:
                os.makedirs(o['webpacks'], exist_ok=True)
                webpack.write_webpack(os.path.join(o['webpacks'], p.slug + '.zip'), p.name, r['arrays'], r['boxes'], r['place'], r['is_color'], p.source)
            ok = all(c['ok'] for c in checks)
            rep = {k: v for k, v in r.items() if k not in ('arrays', 'place', 'boxes')}
            rep['files'] = {k: os.path.basename(v) for k, v in rep['files'].items()}
            rep['verify'] = checks
            with open(os.path.join(outdir, 'report.json'), 'w', encoding='utf-8') as f:
                json.dump(rep, f, indent=1, ensure_ascii=False, default=str)
            flags = [f'layout={r["layout"]["mode"]}'] + (['COLOR'] if 'color' in r['files'] else [])
            if r['skipped']:
                flags.append('skipped ' + ','.join(r['skipped']))
            print(f'{"OK " if ok else "FAIL"} {p.name:36s} {len(r["chars"]):2d} glyphs  {" ".join(flags)}  ({time.time() - t0:.0f}s)')
            miss = [c for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' if c not in r['chars']]
            if miss:
                print('     missing glyphs:', ''.join(miss))
            for n in r['notes']:
                print('     note:', n)
            for c in checks:
                for e in c['errors']:
                    print('     ERROR:', e)
            return buf.getvalue().rstrip(), ok, (p.name, len(r['chars']), r['files'], ok)
        except Exception:
            traceback.print_exc(file=buf)
            print(f'FAIL {p.name}')
            return buf.getvalue().rstrip(), False, None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('inputs', nargs='*', default=[os.path.join(ROOT, 'packs')])
    ap.add_argument('-o', '--out', default=os.path.join(ROOT, 'output_fonts'))
    ap.add_argument('--overrides', default=None, help='pack_overrides.json (default: <packs>/pack_overrides.json)')
    ap.add_argument('--color', choices=['auto', 'all', 'none'], default='auto',
                    help='OpenType-SVG colour .otf: auto = only for colourful packs')
    ap.add_argument('--no-lower', action='store_true', help='do not map a-z to the capital glyphs')
    ap.add_argument('--only', default='', help='only packs whose name contains this text')
    ap.add_argument('--svg-px', type=int, default=512, help='max size of the PNG embedded per colour glyph')
    ap.add_argument('-j', '--jobs', type=int, default=min(4, os.cpu_count() or 1), help='packs converted in parallel')
    ap.add_argument('--webpacks', default=None, help='also write normalised web pack zips for the web app here')
    ap.add_argument('--watermarks', default=None, help='copy watermark images found in packs here')
    a = ap.parse_args(argv)

    sources = []
    for i in a.inputs:
        if os.path.isdir(i) and not any(f.lower().endswith('.png') for f in os.listdir(i)):
            sources += [os.path.join(i, f) for f in sorted(os.listdir(i)) if f.lower().endswith('.zip') or os.path.isdir(os.path.join(i, f))]
        else:
            sources.append(i)
    cands = [a.overrides] if a.overrides else []
    for i in a.inputs:
        cands.append(os.path.join(i if os.path.isdir(i) else os.path.dirname(os.path.abspath(i)), 'pack_overrides.json'))
    cands.append(os.path.join(ROOT, 'packs', 'pack_overrides.json'))
    ov_path = next((c for c in cands if c and os.path.exists(c)), None)
    if ov_path:
        print(f'pack overrides: {os.path.relpath(ov_path)}')
    overrides = pk.load_overrides(ov_path)
    os.makedirs(a.out, exist_ok=True)
    summary, failures, used_names, tasks = [], 0, set(), []
    for src in sources:
        try:
            gpacks, marks = pk.discover(src, overrides)
        except Exception as e:
            print(f'!! cannot read {src}: {e}'); failures += 1; continue
        if marks and a.watermarks:
            os.makedirs(a.watermarks, exist_ok=True)
            for rel, data in marks:
                open(os.path.join(a.watermarks, os.path.basename(rel)), 'wb').write(data)
            print(f'[{os.path.basename(src)}] {len(marks)} watermark images -> {a.watermarks}')
        elif marks:
            print(f'[{os.path.basename(src)}] {len(marks)} watermark images (use --watermarks DIR to export them)')
        for p in gpacks:
            if a.only.lower() not in p.name.lower():
                continue
            base_name, n = p.name, 2
            while p.name in used_names:                      # two packs that clean up to the same name
                p.name = f'{base_name} {n}'; n += 1
            used_names.add(p.name)
            tasks.append(p)
    opts = dict(out=a.out, color=a.color, svg_px=a.svg_px, lower=not a.no_lower, webpacks=a.webpacks)
    if a.jobs > 1 and len(tasks) > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=a.jobs) as ex:
            results = list(ex.map(convert_one, tasks, [opts] * len(tasks)))
    else:
        results = [convert_one(p, opts) for p in tasks]
    for text, ok, row in results:
        print(text)
        failures += (not ok)
        if row:
            summary.append(row)
    with open(os.path.join(a.out, 'INDEX.md'), 'w', encoding='utf-8') as f:
        f.write('# output_fonts\n\n| Font | Glyphs | Files |\n|---|---|---|\n')
        for name, n, files, ok in summary:
            f.write(f'| {name} | {n} | {", ".join(os.path.basename(v) for v in files.values())} |\n')
    print(f'\n{len(summary)} fonts built, {failures} failure(s) -> {a.out}')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
