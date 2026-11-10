# Halo CE (Xbox) cache files: decompress a .map from an XISO and print its header and tag header, to compare
# builds (USA 01.10.12.2276 vs Korean 01.12.09.0135).
#   python games/haloce/hc_map.py <image.xiso> <path inside, e.g. maps_kr/ui.map> [out.map]
import sys, struct, zlib
sys.path.insert(0, __import__('os').path.dirname(__file__))
from hc_xiso import entries, SECTOR


def load(img, path):
    f, base, ents = entries(img)
    p, s, n, d = next(e for e in ents if e[0].lower() == path.lower())
    f.seek(base + s * SECTOR)
    raw = f.read(n)
    head = raw[:2048]
    body = zlib.decompress(raw[2048:])
    return head + body


def describe(m):
    (hs, ver, flen, _, toff, tsize) = struct.unpack_from('<4sIIIII', m, 0)
    print(f'version {ver} file_length {flen:#x} (decompressed {len(m):#x}) tag_data {tsize:#x} @ {toff:#x}')
    print('  build', m[0x40:0x60].split(b'\0')[0], 'name', m[0x20:0x40].split(b'\0')[0])
    th = m[toff:toff + 0x28]
    inst, scen, chk, count, vofs, vcnt, iofs, icnt, msize, sig = struct.unpack_from('<IIIIIIIIII', th)
    print(f'  tag header: instances ptr {inst:#010x} scenario {scen:#x} count {count} model data {vofs:#x}/{msize:#x} sig {sig.to_bytes(4,"little")}')
    # infer the load address: instances ptr - (instances position - tag data start)
    base = inst - 0x28
    print(f'  => tag cache base address ~ {base:#010x}')
    # each tag instance: group, parent1, parent2, index, name ptr, data ptr, 2 x long
    for i in range(min(count, 3)):
        o = toff + (inst - base) + i * 0x20
        g, p1, p2, idx, nptr, dptr = struct.unpack_from('<4s4s4sIII', m, o)
        name = m[toff + nptr - base: toff + nptr - base + 64].split(b'\0')[0] if base <= nptr < base + tsize else b'?'
        print(f'   tag {i}: {g[::-1]} index {idx:#x} name {name} data {dptr:#010x}')
    return base


if __name__ == '__main__':
    m = load(sys.argv[1], sys.argv[2])
    describe(m)
    if len(sys.argv) > 3:
        open(sys.argv[3], 'wb').write(m)
