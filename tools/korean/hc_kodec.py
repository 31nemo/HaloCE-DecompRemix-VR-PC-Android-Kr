# Halo CE Korean Xbox maps (maps_kr, build 01.12.09.0135): decode their strings. Hangul is stored as
# code = (index of the glyph in the map's ui\large_ui font characters) + 0xA1; ASCII stays ASCII. (Found from
# "...니다." endings: 니/다 are glyphs 189/191 = codes 0x15E/0x160.) The fonts carry no character tables; the
# Korean executable must have looked glyphs up this way.
#   python games/haloce/hc_kodec.py <image.xiso> <map path> [ustr name substring]
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from hc_map import load
from hc_tags import Map

OFFSET = 0xA1


def font_chars(mp, font='large_ui'):
    f = next(t for t in mp.tags if t[0] == 'font' and t[2].endswith(font))
    o = mp.ptr(f[3])
    n, p = struct.unpack_from('<iI', mp.m, o + 0x7C)
    return [struct.unpack_from('<H', mp.m, mp.ptr(p) + i * 0x14)[0] for i in range(n)]


def decode(s, ch):
    out = []
    for c in s:
        k = ord(c)
        if k >= 0x100 and 0 <= k - OFFSET < len(ch):
            out.append(chr(ch[k - OFFSET]))
        else:
            out.append(c)
    return ''.join(out)


if __name__ == '__main__':
    mp = Map(load(sys.argv[1], sys.argv[2]))
    ch = font_chars(mp)
    sub = sys.argv[3] if len(sys.argv) > 3 else ''
    for g, idx, name, d in mp.tags:
        if g != 'ustr' or sub not in name:
            continue
        n, p = struct.unpack_from('<iI', mp.m, mp.ptr(d))
        strs = []
        for i in range(n):
            size, flags, off, dp = struct.unpack_from('<iIiI', mp.m, mp.ptr(p) + i * 0x14)
            strs.append(decode(mp.m[mp.ptr(dp):mp.ptr(dp) + size].decode('utf-16-le', 'replace').rstrip('\0'), ch))
        print(name.split(chr(92))[-1] + ':', ' | '.join(s.replace('\r\n', '/') for s in strs)[:300])
