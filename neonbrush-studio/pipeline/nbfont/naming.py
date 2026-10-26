"""File name -> Unicode character mapping and family-name cleanup."""
import re

# keyword file stems -> character
KEYWORDS = {
    'COMMA': ',', 'APOS': "'", 'APOSTROPHE': "'", 'EXCL': '!', 'EXCLAIM': '!', 'QUEST': '?', 'QUESTION': '?',
    'AMP': '&', 'AMPERSAND': '&', 'AT': '@', 'PERIOD': '.', 'DOT': '.', 'HYPHEN': '-', 'DASH': '-', 'COLON': ':',
    'SEMI': ';', 'SEMICOLON': ';', 'SLASH': '/', 'HASH': '#', 'PERCENT': '%', 'PLUS': '+', 'EQUALS': '=',
    'STAR': '*', 'UNDERSCORE': '_', 'LPAREN': '(', 'RPAREN': ')', 'QUOTE': '"', 'DQUOTE': '"', 'SPACE': ' ',
}
PSNAMES = {',': 'comma', "'": 'quotesingle', '!': 'exclam', '?': 'question', '&': 'ampersand', '@': 'at', '.': 'period',
           '-': 'hyphen', ':': 'colon', ';': 'semicolon', '/': 'slash', '#': 'numbersign', '%': 'percent', '+': 'plus',
           '=': 'equal', '*': 'asterisk', '_': 'underscore', '(': 'parenleft', ')': 'parenright', '"': 'quotedbl',
           '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six', '7': 'seven',
           '8': 'eight', '9': 'nine'}
LETTERS = [chr(c) for c in range(ord('A'), ord('Z') + 1)]
DIGITS = [str(i) for i in range(10)]


def stem_to_char(stem):
    """'A' -> 'A', 'COMMA' -> ',', 'u0041' / 'U+0041' -> 'A', '10' / 'foo' -> None (not a single glyph)."""
    s = stem.strip()
    if len(s) == 1:
        return s
    if s.upper() in KEYWORDS:
        return KEYWORDS[s.upper()]
    m = re.fullmatch(r'(?:u\+?|uni)([0-9a-fA-F]{4,6})', s)
    if m:
        return chr(int(m.group(1), 16))
    return None


def glyph_name(ch):
    if ch.isalpha() and ch.isascii():
        return ch
    return PSNAMES.get(ch, 'uni%04X' % ord(ch))


def clean_family(raw):
    """'bold_calligraphy_alphabet_30chars_white_1024x1024' -> 'Bold Calligraphy Alphabet'"""
    s = re.sub(r'[_\-]+', ' ', raw)
    s = re.sub(r'\b\d+\s*chars?\b|\b\d{3,4}x\d{3,4}\b|\b\d+\s*pct\b', ' ', s, flags=re.I)
    s = re.sub(r'\s+', ' ', s).strip()
    def fix(w):
        if w.isupper() and w.isalpha() and len(w) > 2:
            return w.capitalize()
        return w if (w.isupper() and len(w) > 1) or any(c.isupper() for c in w[1:]) else w.capitalize()
    return ' '.join(fix(w) for w in s.split())
