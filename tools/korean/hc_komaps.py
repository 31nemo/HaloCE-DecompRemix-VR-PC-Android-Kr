# Halo CE Korean Xbox maps (maps_kr of "Halo - Jeonjaengui Seomak (Korea) (En,Ko)", build 01.12.09.0135):
# make their Korean text drawable by the port. Their ui\large_ui and ui\small_ui fonts have no character tables
# (256 empty ones); the Korean executable found glyphs by arithmetic instead: ASCII code c -> glyph c - 0x20,
# Hangul code c (>= 0x100) -> glyph c - 0xA1 (hc_kodec.py). The port only looks glyphs up through the tables
# (font_get_character_by_ascii_code), so it drew nothing. Here each such font gets real tables, written into
# the font's own character_tables block: its count goes 256 -> 4 (codes 0x000-0x3FF, which hold every code
# used), and the 4 x 256 shorts of character indices go where entries 4.. were (3024 free bytes). Nothing
# moves, so the map stays the same size. Maps are decompressed, patched and zlib-compressed again.
# The port's high-res text must be off for these maps (hc_build.py --korean-maps).
#   python games/haloce/hc_komaps.py   -> patched_roms/quest/haloce/maps_kr/*.map (+ loading.tga)
import os, sys, struct, zlib
sys.path.insert(0, os.path.dirname(__file__))
from hc_xiso import entries, SECTOR

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ISO = os.path.join(ROOT, 'games', 'haloce', 'Halo - Jeonjaengui Seomak (Korea) (En,Ko).xiso')
OUT = os.path.join(ROOT, 'patched_roms', 'quest', 'haloce', 'maps_kr')
BASE = 0x803A6000
TABLES = 4
HANGUL_OFFSET = 0xA1


def patch_map(m):
    m = bytearray(m)
    _, _, toff, tsize = struct.unpack_from('<IIII', m, 8)
    inst, scen, _, count = struct.unpack_from('<IIII', m, toff)
    ptr = lambda a: toff + (a - BASE)
    done = []
    for i in range(count):
        g, _, _, idx, nptr, dptr = struct.unpack_from('<4s4s4sIII', m, ptr(inst) + i * 0x20)
        if g[::-1] != b'font':
            continue
        name = m[ptr(nptr):m.index(b'\0', ptr(nptr))].decode('latin1')
        f = ptr(dptr)
        tcount, taddr, _ = struct.unpack_from('<iII', m, f + 0x30)
        ccount, caddr, _ = struct.unpack_from('<iII', m, f + 0x7C)
        if tcount != 256 or any(struct.unpack_from('<i', m, ptr(taddr) + k * 12)[0] for k in range(256)):
            continue                                    # a font with tables (English): leave it
        chars = [struct.unpack_from('<H', m, ptr(caddr) + k * 0x14)[0] for k in range(ccount)]
        assert chars[:95] == list(range(0x20, 0x7F)), name
        data_addr = taddr + TABLES * 12                 # where entries 4.. were
        assert TABLES * 256 * 2 <= (256 - TABLES) * 12
        for t in range(TABLES):
            struct.pack_into('<iII', m, ptr(taddr) + t * 12, 256, data_addr + t * 512, 0)
            for lo in range(256):
                code = t * 256 + lo
                if 0x20 <= code < 0x7F:
                    index = code - 0x20
                elif code >= 0x100 and code - HANGUL_OFFSET < ccount:
                    index = code - HANGUL_OFFSET
                else:
                    index = -1
                struct.pack_into('<h', m, ptr(data_addr) + code * 2, index)
        struct.pack_into('<i', m, f + 0x30, TABLES)
        done.append(f'{name}({ccount})')
    return bytes(m), done


def main():
    os.makedirs(OUT, exist_ok=True)
    f, base, ents = entries(ISO)
    for p, s, n, d in ents:
        if d or not p.lower().startswith('maps_kr/'):
            continue
        f.seek(base + s * SECTOR)
        raw = f.read(n)
        name = p.split('/')[-1]
        if name.lower().endswith('.map'):
            m = raw[:2048] + zlib.decompress(raw[2048:])
            m, done = patch_map(m)
            raw = m[:2048] + zlib.compress(m[2048:], 9)
            print(f'{name}: {", ".join(done) or "no font changed"} ({n} -> {len(raw)} bytes)')
        open(os.path.join(OUT, name), 'wb').write(raw)
    print('->', OUT)


if __name__ == '__main__':
    main()
