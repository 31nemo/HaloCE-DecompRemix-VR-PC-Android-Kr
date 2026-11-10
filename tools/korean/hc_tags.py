# Halo CE (Xbox) cache files: list tags of a map in an XISO; dump unicode string lists (ustr) and fonts (font)
#   python games/haloce/hc_tags.py <image.xiso> <path inside> ustr [name substring]
#   python games/haloce/hc_tags.py <image.xiso> <path inside> font
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from hc_map import load

BASE = 0x803A6000


class Map:
    def __init__(self, m):
        self.m = m
        _, _, self.toff, self.tsize = struct.unpack_from('<IIII', m, 8)
        inst, self.scen, _, count = struct.unpack_from('<IIII', m, self.toff)
        self.tags = []
        for i in range(count):
            g, p1, p2, idx, nptr, dptr = struct.unpack_from('<4s4s4sIII', m, self.ptr(inst) + i * 0x20)
            self.tags.append((g[::-1].decode('latin1'), idx, self.cstr(nptr), dptr))

    def ptr(self, a):
        return self.toff + (a - BASE)

    def cstr(self, a):
        o = self.ptr(a)
        return self.m[o:self.m.index(b'\0', o)].decode('latin1')

    def u32(self, o):
        return struct.unpack_from('<I', self.m, o)[0]


def ustr(mp, sub):
    for g, idx, name, d in mp.tags:
        if g != 'ustr' or (sub and sub not in name):
            continue
        n, p = struct.unpack_from('<iI', mp.m, mp.ptr(d))
        out = []
        for i in range(n):
            size, flags, off, dptr = struct.unpack_from('<iIiI', mp.m, mp.ptr(p) + i * 0x14)
            raw = mp.m[mp.ptr(dptr):mp.ptr(dptr) + size]
            out.append(raw.decode('utf-16-le', 'replace').rstrip('\0'))
        print(f'{name} ({n}):', ' | '.join(s.replace('\r\n', '/') for s in out)[:400])


def font(mp):
    for g, idx, name, d in mp.tags:
        if g != 'font':
            continue
        o = mp.ptr(d)
        # font: flags(4) ascending height(2) descending height(2) leading(2) leading? ... characters block near end
        # find the 'characters' reflexive by scanning reflexives whose element size gives 0x14-byte entries
        blob = mp.m[o:o + 0x9C]
        print(name, blob[:16].hex())
        # scan candidate reflexives (count, ptr, 0) inside the header
        for k in range(0, 0x9C - 12, 4):
            c, p, z = struct.unpack_from('<iII', blob, k)
            if 0 < c < 70000 and BASE <= p < BASE + mp.tsize and z == 0:
                first = mp.m[mp.ptr(p):mp.ptr(p) + 8]
                print(f'   +{k:#x}: {c} entries @ {p:#x} first {first.hex()}')


if __name__ == '__main__':
    mp = Map(load(sys.argv[1], sys.argv[2]))
    what = sys.argv[3]
    if what == 'ustr':
        ustr(mp, sys.argv[4] if len(sys.argv) > 4 else '')
    elif what == 'font':
        font(mp)
    else:
        for t in mp.tags:
            if what in t[0]:
                print(t[0], t[2])
