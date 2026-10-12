"""Static contact-sheet preview of pattern functions: python3 preview.py <module> [out.png]"""
import importlib, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import frame

def sheet(patterns, out_html, cols=4, size=420):
    cells = []
    for slug, (cat, ko, fn) in patterns.items():
        try:
            inner = fn()
        except Exception as e:  # show the error in the cell
            inner = f'<text fill="red" font-size="10">{slug}: {e}</text>'
        cells.append(f'<div style="position:relative"><svg viewBox="-140 -140 280 280" width="{size}" height="{size}">'
                     '<defs><clipPath id="clipc"><circle r="102"/></clipPath>'
                     '<filter id="glow"><feGaussianBlur stdDeviation="1.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'
                     '<style>.l{fill:none;stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}</style>'
                     f'<rect x="-140" y="-140" width="280" height="280" fill="#0d1030"/><g filter="url(#glow)">{frame()}{inner}</g></svg>'
                     f'<div style="position:absolute;left:6px;top:4px;color:#aab;font:12px sans-serif">{slug} {ko}</div></div>')
    open(out_html, 'w').write(f'<body style="margin:0;background:#000;display:grid;grid-template-columns:repeat({cols},{size}px)">' + ''.join(cells) + '</body>')

if __name__ == '__main__':
    mod = importlib.import_module(sys.argv[1])
    sheet(mod.PATTERNS, sys.argv[2])
