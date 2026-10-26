"""python3 -m unittest discover -s tests -v     (generates the synthetic sample packs first)"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
from fontTools.ttLib import TTFont  # noqa: E402
from nbfont import clean, naming, packs, build, verify  # noqa: E402
import build_fonts  # noqa: E402


def sample(name):
    p = os.path.join(ROOT, 'samples', name)
    if not os.path.exists(p):
        subprocess.check_call([sys.executable, os.path.join(ROOT, 'samples', 'make_samples.py')])
    return p


class Naming(unittest.TestCase):
    def test_stems(self):
        self.assertEqual(naming.stem_to_char('A'), 'A')
        self.assertEqual(naming.stem_to_char('7'), '7')
        self.assertEqual(naming.stem_to_char('COMMA'), ',')
        self.assertEqual(naming.stem_to_char('APOS'), "'")
        self.assertEqual(naming.stem_to_char('EXCL'), '!')
        self.assertEqual(naming.stem_to_char('QUEST'), '?')
        self.assertEqual(naming.stem_to_char('AMP'), '&')
        self.assertEqual(naming.stem_to_char('AT'), '@')
        self.assertEqual(naming.stem_to_char('u0041'), 'A')
        self.assertIsNone(naming.stem_to_char('10'))
        self.assertIsNone(naming.stem_to_char('BRSh_Design1'))

    def test_family(self):
        self.assertEqual(naming.clean_family('bold_calligraphy_alphabet_30chars_white_1024x1024'), 'Bold Calligraphy Alphabet')
        self.assertEqual(naming.clean_family('DRY_SCRATCH'), 'Dry Scratch')


class Cleaning(unittest.TestCase):
    def test_neighbour_fragments_removed(self):
        a = np.zeros((1024, 1024, 4), np.uint8)
        a[200:800, 450:560] = 255                    # main glyph (centre)
        a[200:800, 250:300] = 255                    # cut-off neighbour on the left
        a[200:800, 740:768] = 255                    # cut-off neighbour on the right
        out, info = clean.keep_center_groups(a, gap=10, band=48)
        ys, xs = np.where(out[..., 3] > 0)
        self.assertEqual((xs.min(), xs.max()), (450, 559))
        self.assertEqual(info['removed_groups'], 2)

    def test_border_components_removed(self):
        a = np.zeros((256, 256, 4), np.uint8)
        a[50:200, 100:140] = 255
        a[:, 0:4] = 255                              # sliver touching the border
        out, info = clean.clean(a)
        self.assertEqual(out[10, 1, 3], 0)
        self.assertEqual(out[100, 120, 3], 255)


class Overrides(unittest.TestCase):
    def test_relabel(self):
        d = tempfile.mkdtemp()
        zpath = os.path.join(d, 'Pack_X.zip')
        with zipfile.ZipFile(zpath, 'w') as z:
            for stem in ['A', 'B', 'C', 'D', 'E', 'F']:
                b = io.BytesIO(); Image.new('RGBA', (64, 64), (255, 255, 255, 255)).save(b, 'PNG'); z.writestr(f'Style1/{stem}.png', b.getvalue())
        ov = {'Pack_X::Style1': {'labels': {'A': 'F', 'F': 'A'}}}
        ps, marks = packs.discover(zpath, ov)
        self.assertEqual(len(ps), 1)
        self.assertEqual(set(ps[0].glyphs), set('ABCDEF'))
        self.assertEqual(ps[0].name, 'Pack X')
        shutil.rmtree(d)

    def test_watermark_pack_is_not_a_font(self):
        d = tempfile.mkdtemp()
        zpath = os.path.join(d, 'wm.zip')
        with zipfile.ZipFile(zpath, 'w') as z:
            for stem in ['BRSh_Design1_100pct', 'BRSh_Design2_100pct']:
                b = io.BytesIO(); Image.new('RGBA', (200, 100)).save(b, 'PNG'); z.writestr(f'1_100pct/{stem}.png', b.getvalue())
        ps, marks = packs.discover(zpath)
        self.assertEqual(ps, []); self.assertEqual(len(marks), 2)
        shutil.rmtree(d)


class FontBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = tempfile.mkdtemp()
        cls.web = os.path.join(cls.out, 'web')
        rc = build_fonts.main([sample('TestMono.zip'), sample('TestNeon.zip'), '-o', cls.out, '--webpacks', cls.web])
        cls.rc = rc

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.out, ignore_errors=True)

    def test_batch_ok(self):
        self.assertEqual(self.rc, 0)

    def test_mono_fonts(self):
        for kind in ('ttf', 'otf'):
            p = os.path.join(self.out, 'TestMono', f'TestMono-Regular.{kind}')
            self.assertTrue(os.path.exists(p), p)
            t = TTFont(p)
            cm = t.getBestCmap()
            for ch in 'AZaz09,\'!?&@ ':
                self.assertIn(ord(ch), cm, ch)
            self.assertEqual(('glyf' in t), kind == 'ttf')
            self.assertEqual(('CFF ' in t), kind == 'otf')
            r = verify.verify(p, 'ABC')
            self.assertTrue(r['ok'], r)

    def test_color_font_opentype_svg(self):
        p = os.path.join(self.out, 'TestNeon', 'TestNeon-Color.otf')
        self.assertTrue(os.path.exists(p))
        t = TTFont(p)
        self.assertIn('SVG ', t)
        self.assertIn('CFF ', t)
        self.assertGreaterEqual(len(t['SVG '].docList), 36)
        r = verify.verify(p, 'ABC', color=True)
        self.assertTrue(r['ok'], r)

    def test_mono_pack_has_no_colour_font(self):
        self.assertFalse(os.path.exists(os.path.join(self.out, 'TestMono', 'TestMono-Color.otf')))

    def test_webpack(self):
        z = zipfile.ZipFile(os.path.join(self.web, 'TestMono.zip'))
        meta = json.loads(z.read('pack.json'))
        self.assertEqual(meta['format'], 'neonbrush-webpack')
        self.assertIn('A', meta['glyphs'])
        self.assertIn(meta['glyphs']['A']['file'], z.namelist())

    def test_glyph_geometry(self):
        """cap height ~700 units and baseline at 0 for the sample (centred) pack"""
        t = TTFont(os.path.join(self.out, 'TestMono', 'TestMono-Regular.ttf'))
        gs = t.getGlyphSet()
        from fontTools.pens.boundsPen import BoundsPen
        bp = BoundsPen(gs); gs['H'].draw(bp)
        self.assertAlmostEqual(bp.bounds[1], 0, delta=25)
        self.assertAlmostEqual(bp.bounds[3], 700, delta=40)


if __name__ == '__main__':
    unittest.main()
