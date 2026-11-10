# Halo CE Decomp Remix (moistman42069/HaloCE-DecompRemix-VR-PC-Android, 1.0.41): accept the Korean Xbox disc
# "Halo - Jeonjaengui Seomak (Korea) (En,Ko)". Its maps are cache v5 like the USA ones but of build
# 01.12.09.0135, which the port does not list, and the disc has maps/ (English) and maps_kr/ (Korean).
#   1. MapInfo.<init> (launcher): build 01.12.09.0135 -> region "NTSC" (GameDataLibrary refuses "unknown").
#   2. XisoExtractor.extract (launcher): a disc with maps_kr/ imports maps_kr (before maps/). The method keeps
#      "maps" in v15 and later uses it as the destination folder name, so v15 is set back to "maps" before
#      leaving the added loop (else the maps land in maps_kr/ and the launcher says maps/ui.map is missing).
#   3. halo_guest.elf (engine, cache_file_builds[] in source/cache/cache_files.c): the third entry
#      01.08.15.1749 -> 01.12.09.0135, so the Korean maps are a supported build (multiplayer menus too).
# Rebuilds with apktool, zipaligns and signs with the local key (tools/android/vrgame.keystore).
#   python games/haloce/hc_build.py [quest|android ...]   -> patched_roms/quest/haloce/HaloCE-<Quest|Android>-1.0.41-kr.apk
import os, sys, shutil, subprocess, struct

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'games', 'haloce')
OUT = os.path.join(ROOT, 'patched_roms', 'quest', 'haloce')
WORK = os.path.join(OUT, 'work')
TOOLS = os.path.join(ROOT, 'tools', 'android')
BT = os.path.join(TOOLS, 'android-14')
JAVA_BIN = r'C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot\bin'
KEY = os.path.join(TOOLS, 'vrgame.keystore')
APKS = {'quest': 'HaloCE-Quest-1.0.41.apk', 'android': 'HaloCE-Android-1.0.41.apk'}
KR_BUILD = '01.12.09.0135'
# --korean-maps: import maps_kr and draw the maps' bitmap fonts (2. and 6. below). NOT WORKING YET: the Korean maps'
# large_ui/small_ui fonts have empty character tables (all 256 hold 0 entries; the English maps' have 5 full
# ones) and their strings use codes (입력 = 0x176 0x194) that the Korean executable maps to the font's characters
# in a way not found yet, so the port's font_get_character_by_ascii_code finds no glyph and draws nothing.
# Default: the disc's English maps/ (normal fonts) with the port's high-res text; 1., 3., 4., 5. still apply
# (the English maps are of the Korean build too).
KOREAN_MAPS = False

MAPINFO_OLD = '''    :cond_0
    const-string v0, "01.10.12.2276"
'''
MAPINFO_NEW = '''    :cond_0
    const-string v0, "%s"

    invoke-virtual {p1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_2

    const-string v0, "01.10.12.2276"
''' % KR_BUILD

XISO_OLD = '''    invoke-interface {v9}, Ljava/util/List;->iterator()Ljava/util/Iterator;

    move-result-object v4

    :goto_7
'''
XISO_NEW = '''    invoke-interface {v9}, Ljava/util/List;->iterator()Ljava/util/Iterator;

    move-result-object v4

    :kr_loop
    invoke-interface {v4}, Ljava/util/Iterator;->hasNext()Z

    move-result v5

    if-eqz v5, :kr_done

    invoke-interface {v4}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    move-result-object v5

    check-cast v5, Lcom/halo/decomp/XisoExtractor$Entry;

    iget-object v7, v5, Lcom/halo/decomp/XisoExtractor$Entry;->name:Ljava/lang/String;

    const-string v15, "maps_kr"

    invoke-virtual {v7, v15}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    move-result v7

    if-eqz v7, :kr_loop

    move-object v1, v5

    const-string v15, "maps"

    goto :goto_8

    :kr_done
    invoke-interface {v9}, Ljava/util/List;->iterator()Ljava/util/Iterator;

    move-result-object v4

    :goto_7
'''

ELF_OLD = b'\x0001.08.15.1749\x00'                      # the only occurrence (the builds table)
ELF_NEW = b'\x00' + KR_BUILD.encode() + b'\x00'

# 4. halo_guest.elf TAG_CACHE_SIZE 0x1600000 -> 0x1680000. The Korean executable has a bigger tag cache
#    (0x167D000: its maps place each structure bsp to end at 0x803A6000 + 0x167D000), so the port refused
#    them ("a structure bsp is damaged: ... would load to ..., outside the tag cache"). 0x1680000 is the
#    nearest size a single movz can hold. Every `mov wN, #0x1600000` of the tag cache (allocation at 0x3A6000,
#    protection, header/bsp checks, 0xCD fill, tag validation); NOT 0x88360360, the texture cache (same value).
#    The Quest and Android APKs carry different engine builds, so each has its own list (found with hc_const.py;
#    the texture site is the one in the bitmap checker: "is %dx%dx%d, past the device's ...").
TAG_CACHE_SITES = {
    'quest': [0x88084c48, 0x880850b4, 0x880850d8, 0x88085400, 0x88085c68, 0x880860e4, 0x8808614c,
              0x880861cc, 0x8808c1f0, 0x8808c2d0, 0x88362910],          # texture: 0x88360360
    'android': [0x88084c48, 0x880850b4, 0x880850d8, 0x88085400, 0x88085c60, 0x880860d4, 0x8808613c,
                0x880861bc, 0x8808c1e0, 0x8808c2c0, 0x88363000],        # texture: 0x88360a50
}


# 5. The port keeps the game state right after the tag cache, at 0x81A00000 (HALO_PORT_GAME_STATE_BASE_ADDRESS;
#    the Xbox had it at 0x80061000), so a 0x1680000 tag cache (to 0x81A26000) overlapped it: the tag cache
#    allocation failed and the game died in memset(NULL) ("assert cseries.c #279: buffer"). Move the game state
#    up by 1 MB to 0x81B00000: its allocation (physical 0x1A00000), the check of the address it got, and the
#    memory-watch registration. (va, old movz imm16, new imm16), all `movz wN, #imm, lsl #16`.
GAME_STATE_SITES = {
    'quest': [(0x8808c1a8, 0x01A0, 0x01B0), (0x8808c1c0, 0x81A0, 0x81B0), (0x8821b02c, 0x81A0, 0x81B0)],
    'android': [(0x8808c198, 0x01A0, 0x01B0), (0x8808c1b0, 0x81A0, 0x81B0), (0x882184ac, 0x81A0, 0x81B0)],
}


# 6. High-res text off by default. The port draws ui\large_ui, ui\small_ui and ui\interstate with Overpass
#    (port/linux/src/text_hires.c) wherever Overpass has the code; the Korean maps' strings are codes that only
#    their own bitmap fonts map to Hangul (e.g. 입력 = U+0176 U+0194), so Korean text came out as Latin letters
#    or nothing. display.high_res_text = false draws the maps' bitmap fonts. Its default in the settings table
#    ("true") -> "false", and the setting renamed (same length) so a config.toml written by an earlier run, which
#    holds "true", is not used; the in-game menu's HIGH-RES TEXT spinner uses the new name too.
HIRES_OLD, HIRES_NEW = b'display.high_res_text', b'display.hires_text_kr'


def patch_high_res_text(path):
    data = bytearray(open(path, 'rb').read())
    table_name = data.find(HIRES_OLD + b'\0HALO_HIGH_RES_TEXT\0')
    assert table_name > 0
    name_va = elf_o2v(data, table_name)
    entry = None
    for o in range(0, len(data) - 12, 4):
        if struct.unpack_from('<I', data, o)[0] == name_va:
            entry = o
            break
    assert entry is not None
    true_va, = struct.unpack_from('<I', data, entry + 8)
    t = elf_v2o(data, true_va)
    assert data[t:t + 11] == b'true\0false\0', data[t:t + 11]
    struct.pack_into('<I', data, entry + 8, true_va + 5)
    n = data.count(HIRES_OLD)
    assert n == 4, n
    data = data.replace(HIRES_OLD, HIRES_NEW)
    open(path, 'wb').write(data)
    print(f'patched halo_guest.elf high-res text: default false, renamed ({n} places)')


def elf_o2v(data, o):
    phoff, = struct.unpack_from('<Q', data, 0x20)
    phentsize, phnum = struct.unpack_from('<HH', data, 0x36)
    for i in range(phnum):
        p = phoff + i * phentsize
        typ, = struct.unpack_from('<I', data, p)
        off, vaddr, _, filesz = struct.unpack_from('<QQQQ', data, p + 8)
        if typ == 1 and off <= o < off + filesz:
            return o - off + vaddr
    raise ValueError(hex(o))


def patch_movz_hi(path, sites, label):
    data = bytearray(open(path, 'rb').read())
    for va, old, new in sites:
        o = elf_v2o(data, va)
        w, = struct.unpack_from('<I', data, o)
        if w & ~31 != 0x52A00000 | old << 5:
            sys.exit(f'halo_guest.elf {va:#x}: unexpected {w:#010x}')
        struct.pack_into('<I', data, o, 0x52A00000 | new << 5 | (w & 31))
    open(path, 'wb').write(data)
    print(f'patched halo_guest.elf {label} at {len(sites)} sites')


def elf_v2o(data, v):
    phoff, = struct.unpack_from('<Q', data, 0x20)
    phentsize, phnum = struct.unpack_from('<HH', data, 0x36)
    for i in range(phnum):
        p = phoff + i * phentsize
        typ, = struct.unpack_from('<I', data, p)
        off, vaddr, _, filesz = struct.unpack_from('<QQQQ', data, p + 8)
        if typ == 1 and vaddr <= v < vaddr + filesz:
            return v - vaddr + off
    raise ValueError(hex(v))


def patch_tag_cache_size(path, kind):
    data = bytearray(open(path, 'rb').read())
    for va in TAG_CACHE_SITES[kind]:
        o = elf_v2o(data, va)
        w, = struct.unpack_from('<I', data, o)
        if w & ~31 != 0x52A02C00:                # movz wN, #0x160, lsl #16
            sys.exit(f'halo_guest.elf {va:#x}: unexpected {w:#010x}')
        struct.pack_into('<I', data, o, 0x52A02D00 | (w & 31))   # movz wN, #0x168, lsl #16
    open(path, 'wb').write(data)
    print(f'patched halo_guest.elf TAG_CACHE_SIZE at {len(TAG_CACHE_SITES[kind])} sites')


def run(args, **kw):
    env = dict(os.environ, PATH=JAVA_BIN + os.pathsep + os.environ['PATH'])
    subprocess.run(args, check=True, env=env, **kw)


def replace_once(path, old, new, mode=''):
    if mode:
        data = open(path, 'rb').read()
    else:
        data = open(path, encoding='utf-8', newline='').read()
        if '\r\n' in data:                      # apktool on Windows writes CRLF
            old, new = old.replace('\n', '\r\n'), new.replace('\n', '\r\n')
    if data.count(old) != 1:
        sys.exit(f'{path}: expected one match, found {data.count(old)}')
    data = data.replace(old, new)
    if mode:
        open(path, 'wb').write(data)
    else:
        open(path, 'w', encoding='utf-8', newline='').write(data)
    print('patched', os.path.relpath(path, WORK))


# 7. (--korean-maps) KoreanFonts.java (games/haloce/java): after a disc image is imported, give the Korean
#    maps' fonts real character tables (see hc_komaps.py), so the imported maps_kr show their Korean text.
#    Compiled with javac + d8 into classes10.dex; XisoExtractor.extractMaps calls KoreanFonts.fixMaps(destination,
#    progress) just before it returns.
JAVA_SRC = os.path.join(SRC, 'java')
XISO_CALL = (
    '    move-object/from16 v0, p1\n\n'
    '    move-object/from16 v1, p2\n\n'
    '    invoke-static {v0, v1}, Lcom/halo/decomp/KoreanFonts;->fixMaps(Ljava/io/File;Lcom/halo/decomp/XisoExtractor$Progress;)V\n\n'
    '    return-void\n')


def korean_fonts_dex():
    """KoreanFonts.java -> dex (classes.dex in a temporary folder); the stubs only compile it"""
    cls = os.path.join(WORK, 'java-classes')
    dex = os.path.join(WORK, 'java-dex')
    for d in (cls, dex):
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
    run([os.path.join(JAVA_BIN, 'javac'), '--release', '8', '-nowarn', '-d', cls,
         os.path.join(JAVA_SRC, 'com', 'halo', 'decomp', 'KoreanFonts.java'),
         os.path.join(JAVA_SRC, 'stub', 'com', 'halo', 'decomp', 'XisoExtractor.java'),
         os.path.join(JAVA_SRC, 'stub', 'android', 'util', 'Log.java')])
    run([os.path.join(BT, 'd8.bat'), '--min-api', '28', '--no-desugaring', '--output', dex,
         os.path.join(cls, 'com', 'halo', 'decomp', 'KoreanFonts.class')])
    return open(os.path.join(dex, 'classes.dex'), 'rb').read()


def add_xiso_call(smali_dir):
    path = os.path.join(smali_dir, 'XisoExtractor.smali')
    text = open(path, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in text else '\n'
    start = text.index('.method static extractMaps(')
    end = text.index('.end method', start)
    body = text[start:end]
    assert body.count('return-void') == 1
    body = body.replace('    return-void' + nl, XISO_CALL.replace('\n', nl))
    open(path, 'w', encoding='utf-8', newline='').write(text[:start] + body + text[end:])
    print('patched XisoExtractor.extractMaps: calls KoreanFonts.fixMaps')


def build(kind):
    src = os.path.join(SRC, APKS[kind])
    work = os.path.join(WORK, kind)
    shutil.rmtree(work, ignore_errors=True)
    run([os.path.join(JAVA_BIN, 'java'), '-jar', os.path.join(TOOLS, 'apktool.jar'), 'd', '-f', '-r', '-o', work, src])
    smali = None
    for d in os.listdir(work):
        p = os.path.join(work, d, 'com', 'halo', 'decomp', 'MapInfo.smali')
        if d.startswith('smali') and os.path.exists(p):
            smali = os.path.join(work, d, 'com', 'halo', 'decomp')
    replace_once(os.path.join(smali, 'MapInfo.smali'), MAPINFO_OLD, MAPINFO_NEW)
    if KOREAN_MAPS:
        replace_once(os.path.join(smali, 'XisoExtractor.smali'), XISO_OLD, XISO_NEW)
        add_xiso_call(smali)
    replace_once(os.path.join(work, 'assets', 'halo_guest.elf'), ELF_OLD, ELF_NEW, 'b')
    patch_tag_cache_size(os.path.join(work, 'assets', 'halo_guest.elf'), kind)
    patch_movz_hi(os.path.join(work, 'assets', 'halo_guest.elf'), GAME_STATE_SITES[kind], 'game state 0x81A00000 -> 0x81B00000')
    if KOREAN_MAPS:
        patch_high_res_text(os.path.join(work, 'assets', 'halo_guest.elf'))

    unsigned = os.path.join(OUT, f'{kind}-unsigned.apk')
    aligned = os.path.join(OUT, f'{kind}-aligned.apk')
    final = os.path.join(OUT, APKS[kind].replace('.apk', '-kr.apk'))
    run([os.path.join(JAVA_BIN, 'java'), '-jar', os.path.join(TOOLS, 'apktool.jar'), 'b', '-o', unsigned, work])
    if KOREAN_MAPS:
        import zipfile
        with zipfile.ZipFile(unsigned, 'a') as z:
            assert 'classes10.dex' not in z.namelist()
            z.writestr(zipfile.ZipInfo('classes10.dex'), korean_fonts_dex())
        print('added classes10.dex (KoreanFonts)')
    for f in (aligned, final):
        if os.path.exists(f):
            os.remove(f)
    run([os.path.join(BT, 'zipalign.exe'), '-p', '-f', '4', unsigned, aligned])
    run([os.path.join(BT, 'apksigner.bat'), 'sign', '--ks', KEY, '--ks-pass', 'pass:vrgame', '--out', final, aligned])
    run([os.path.join(BT, 'apksigner.bat'), 'verify', final])
    os.remove(unsigned); os.remove(aligned)
    print('->', final, os.path.getsize(final))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    args = sys.argv[1:]
    if '--korean-maps' in args:
        KOREAN_MAPS = True
        args.remove('--korean-maps')
    for k in args or ['quest', 'android']:
        build(k)
