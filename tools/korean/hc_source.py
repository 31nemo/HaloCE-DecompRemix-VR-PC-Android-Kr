# Halo CE Decomp Remix: apply the Korean-disc changes of hc_build.py --korean-maps (which patches the released
# APKs' binaries) to the upstream source of the same release, so the published build has its corresponding source
# (AGPL-3.0-or-later). Each change below is the source form of a binary patch in hc_build.py.
#   python games/haloce/hc_source.py <upstream checkout at v1.0.41>
import os, sys, shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
KR = '01.12.09.0135'


def edit(path, old, new, count=1):
    p = os.path.join(SRC, path)
    text = open(p, encoding='utf-8', newline='').read()
    if '\r\n' in text:                                   # a checkout with core.autocrlf
        old, new = old.replace('\n', '\r\n'), new.replace('\n', '\r\n')
    if text.count(old) != count:
        sys.exit(f'{path}: expected {count} of {old!r}, found {text.count(old)}')
    open(p, 'w', encoding='utf-8', newline='').write(text.replace(old, new))
    print('edited', path)


SRC = sys.argv[1]
J = 'port/android/app/src/main/java/com/halo/decomp/'

# 1. launcher: the Korean build is a supported (NTSC) one
edit(J + 'MapInfo.java',
     'build.equals("01.10.12.2276")||build.equals("01.08.15.1749")?"NTSC"',
     f'build.equals("{KR}")||build.equals("01.10.12.2276")||build.equals("01.08.15.1749")?"NTSC"')

# 2. launcher: a disc with maps_kr imports maps_kr; then KoreanFonts gives its fonts character tables
edit(J + 'XisoExtractor.java',
     '''        List<Entry> directories = walkTable(root, true);
        for (Entry entry : directories) {
            if (entry.name.equalsIgnoreCase("maps")) {''',
     '''        List<Entry> directories = walkTable(root, true);
        /* (Korean patch) the Korean disc ("Halo - Jeonjaengui Seomak") has maps (English) and maps_kr
        (Korean voice and text): take maps_kr */
        for (Entry entry : directories) {
            if (entry.name.equalsIgnoreCase("maps_kr")) {
                maps = entry;
                break;
            }
        }
        for (Entry entry : directories) {
            if (maps != null)
                break;
            if (entry.name.equalsIgnoreCase("maps")) {''')
edit(J + 'XisoExtractor.java',
     '''                throw new ExtractException("Could not move " + file.name + " into " + mapsFolder.getPath() + ".");
        }
        partial.delete();
    }''',
     '''                throw new ExtractException("Could not move " + file.name + " into " + mapsFolder.getPath() + ".");
        }
        partial.delete();
        /* (Korean patch) the Korean maps' fonts need character tables (KoreanFonts.java) */
        KoreanFonts.fixMaps(destination, progress);
    }''')
shutil.copy(os.path.join(ROOT, 'games', 'haloce', 'java', 'com', 'halo', 'decomp', 'KoreanFonts.java'),
            os.path.join(SRC, J, 'KoreanFonts.java'))
print('added', J + 'KoreanFonts.java')

# 3. engine: the Korean build in the builds table (in place of 01.08.15.1749, as the binary patch does)
edit('source/cache/cache_files.c', '{ "01.08.15.1749", "NTSC" },', f'{{ "{KR}", "NTSC" }}, /* (Korean patch) */')

# 4. engine: the Korean executable's bigger tag cache (0x167D000, rounded up)
for f in ('source/cache/physical_memory_map.c', 'source/cache/physical_memory_map.h'):
    edit(f, '#define TAG_CACHE_SIZE 0x1600000',
         '#define TAG_CACHE_SIZE 0x1680000 /* (Korean patch: the Korean maps\' 0x167D000; was 0x1600000) */')

# 5. engine: the game state moved up past the bigger tag cache
edit('port/linux/include/halo_port_capacity.h', '#define HALO_PORT_GAME_STATE_BASE_ADDRESS 0x81A00000 /* (0x80061000) */',
     '#define HALO_PORT_GAME_STATE_BASE_ADDRESS 0x81B00000 /* (0x80061000; Korean patch: was 0x81A00000) */')

# 6. high-res text off by default, under a new name (a config.toml with the old one is not used)
edit('port/linux/src/port_config.c', '{ "display.high_res_text", _config_boolean, "true",',
     '{ "display.hires_text_kr", _config_boolean, "false",')
edit('port/linux/src/text_hires.c', 'config_boolean("display.high_res_text")', 'config_boolean("display.hires_text_kr")')
edit('port/linux/src/hud_hires.c', 'config_boolean("display.high_res_text")', 'config_boolean("display.hires_text_kr")', 3)
edit('port/assets/menus/ce/main_menu.settings_select.player_setup.player_profile_edit.video_settings.graphics.xml',
     'setting="display.high_res_text"', 'setting="display.hires_text_kr"')
