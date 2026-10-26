"""Find glyph packs inside .zip files / folders, apply per-pack overrides, separate watermark packs."""
import io
import json
import os
import zipfile
from dataclasses import dataclass, field

from .naming import stem_to_char, clean_family

IMG_EXT = ('.png',)


@dataclass
class Pack:
    name: str                    # human family name
    source: str                  # zip / folder it came from
    folder: str                  # sub folder inside the source ('' = root)
    glyphs: dict = field(default_factory=dict)   # char -> png bytes
    skipped: list = field(default_factory=list)  # file names that are not single glyphs
    notes: list = field(default_factory=list)
    options: dict = field(default_factory=dict)  # from overrides

    @property
    def slug(self):
        return ''.join(c for c in self.name if c.isalnum())


def _read_source(path):
    """-> {relative_path: bytes}"""
    files = {}
    if os.path.isdir(path):
        for root, _, names in os.walk(path):
            for n in names:
                full = os.path.join(root, n)
                files[os.path.relpath(full, path).replace(os.sep, '/')] = open(full, 'rb').read()
    else:
        with zipfile.ZipFile(path) as z:
            for i in z.infolist():
                if not i.is_dir() and not i.filename.startswith('__MACOSX') and '/._' not in i.filename:
                    files[i.filename] = z.read(i)
    return files


def load_overrides(path):
    if path and os.path.exists(path):
        return json.load(open(path, encoding='utf-8'))
    return {}


def discover(path, overrides=None):
    """Return (glyph_packs, watermark_images). overrides is the parsed pack_overrides.json."""
    overrides = overrides or {}
    files = _read_source(path)
    base = os.path.splitext(os.path.basename(path.rstrip('/')))[0]
    if '-' in base and len(base.split('-')[0]) in (8, 9):      # strip upload-id prefixes like 'a4e9af40-'
        base = base.split('-', 1)[1]
    groups = {}
    for rel, data in files.items():
        if not rel.lower().endswith(IMG_EXT):
            continue
        folder, fname = os.path.split(rel)
        groups.setdefault(folder, {})[os.path.splitext(fname)[0]] = data
    packs, marks = [], []
    # a single top-level wrapper folder (zip made from a folder) should not become part of the name
    top = {f.split('/')[0] for f in groups if f}
    wrapper = top.pop() if len(top) == 1 and all(f for f in groups) else None
    multi = len(groups) > 1
    for folder, imgs in sorted(groups.items()):
        chars = {s: stem_to_char(s) for s in imgs}
        n_glyph = sum(1 for c in chars.values() if c)
        if n_glyph < max(5, len(imgs) // 2):
            marks.extend((f'{folder}/{s}.png'.lstrip('/'), imgs[s]) for s in sorted(imgs))
            continue
        sub = folder[len(wrapper) + 1:] if wrapper and folder.startswith(wrapper) else folder
        sub = sub.strip('/')
        name = clean_family(base) if not sub else (clean_family(base) + ' ' + clean_family(sub.replace('/', ' '))).strip()
        if wrapper and not sub and clean_family(wrapper) and not multi:
            name = clean_family(base)
        p = Pack(name=name, source=os.path.basename(path), folder=folder)
        key = f'{os.path.basename(path)}::{sub}'
        ov = _find_override(overrides, base, sub)
        p.options = dict(ov.get('options', {}))
        relabel = ov.get('labels', {})
        for stem, data in imgs.items():
            ch = stem_to_char(stem)
            if ch is None:
                p.skipped.append(stem + '.png')
                continue
            ch = relabel.get(stem, ch) if relabel else ch
            if ch in p.glyphs:
                p.notes.append(f'duplicate glyph {ch!r} ({stem}.png ignored)')
                continue
            p.glyphs[ch] = data
        if relabel:
            p.notes.append(f'{len(relabel)} file labels remapped by pack_overrides.json')
        packs.append(p)
    return packs, marks


def _find_override(overrides, base, sub):
    for k, v in overrides.items():
        kb, _, ks = k.partition('::')
        if kb.lower() in base.lower() and ks.strip('/') == sub:
            return v
    return {}
