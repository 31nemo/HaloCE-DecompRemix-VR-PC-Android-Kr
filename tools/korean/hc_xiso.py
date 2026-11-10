# Halo CE (Xbox) disc images: list / extract XISO (XDVDFS) contents.
#   python games/haloce/hc_xiso.py list <image.xiso>
#   python games/haloce/hc_xiso.py extract <image.xiso> <path inside image> <out file>
#   python games/haloce/hc_xiso.py header <image.xiso> <path inside>   # Halo cache header of a .map
import os, sys, struct

SECTOR = 2048
MAGIC = b'MICROSOFT*XBOX*MEDIA'


def find_base(f):
    for base in (0, 0x18300000, 0x30600000, 0x0FD90000):     # plain xiso, redump game partition offsets
        f.seek(base + 32 * SECTOR)
        if f.read(20) == MAGIC:
            return base
    raise SystemExit('no XDVDFS volume descriptor')


def walk(f, base, sector, size, prefix=''):
    f.seek(base + sector * SECTOR)
    table = f.read(size)
    out = []

    def node(off):
        if off * 4 + 14 > len(table):
            return
        l, r, start, fsize, attr, nlen = struct.unpack_from('<HHIIBB', table, off * 4)
        if l == 0xFFFF:
            return
        name = table[off * 4 + 14: off * 4 + 14 + nlen].decode('latin1')
        if l:
            node(l)
        path = prefix + name
        if attr & 0x10:
            out.append((path + '/', start, fsize, True))
            if fsize:
                out.extend(walk(f, base, start, fsize, path + '/'))
        else:
            out.append((path, start, fsize, False))
        if r:
            node(r)
    node(0)
    return out


def entries(img):
    f = open(img, 'rb')
    base = find_base(f)
    f.seek(base + 32 * SECTOR + 20)
    root, rsize = struct.unpack('<II', f.read(8))
    return f, base, walk(f, base, root, rsize)


def main():
    cmd, img = sys.argv[1], sys.argv[2]
    f, base, ents = entries(img)
    if cmd == 'list':
        print(f'# base {base:#x}')
        for p, s, n, d in ents:
            print(f'{n:>12} {p}')
    elif cmd in ('extract', 'header'):
        want = sys.argv[3].replace('\\', '/').lower()
        p, s, n, d = next(e for e in ents if e[0].lower() == want)
        f.seek(base + s * SECTOR)
        if cmd == 'header':
            h = f.read(2048)
            head, ver, size = struct.unpack_from('<4sII', h, 0)
            print(p, n, 'head', head, 'version', ver, 'size', size,
                  'name', h[0x20:0x40].split(b'\0')[0], 'build', h[0x40:0x60].split(b'\0')[0],
                  'type', struct.unpack_from('<I', h, 0x60)[0], 'foot', h[0x7FC:0x800])
        else:
            with open(sys.argv[4], 'wb') as o:
                left = n
                while left:
                    b = f.read(min(left, 1 << 22))
                    o.write(b)
                    left -= len(b)
            print('->', sys.argv[4], n)


if __name__ == '__main__':
    main()
