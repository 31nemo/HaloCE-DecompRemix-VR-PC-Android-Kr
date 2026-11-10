package com.halo.decomp;

import java.io.*;
import java.util.zip.*;

/**
 * (vrgame Korean patch) The Korean Xbox maps (maps_kr of "Halo - Jeonjaengui Seomak", build 01.12.09.0135):
 * their ui\large_ui and ui\small_ui fonts have no character tables (256 empty ones). The Korean executable found
 * glyphs by arithmetic instead (ASCII code c -> glyph c - 0x20, Hangul code c >= 0x100 -> glyph c - 0xA1), but
 * the port looks glyphs up only through the tables, so it drew no text at all. After a disc image is imported,
 * each such font gets real tables, written into its own character_tables block: count 256 -> 4 (codes
 * 0x000-0x3FF hold every code used) and the 4 x 256 character indices where entries 4.. were. Nothing moves.
 * A map is streamed: its tag data alone (at most the 22 MB tag cache) is held in memory, the rest is inflated
 * and deflated through. Maps of other builds, or whose fonts already have tables, are left as they are.
 * Same as games/haloce/hc_komaps.py.
 */
final class KoreanFonts {
    private static final String BUILD = "01.12.09.0135";
    private static final long BASE = 0x803A6000L;
    private static final int TABLES = 4;
    private static final int HANGUL_OFFSET = 0xA1;
    private static final int HEADER = 2048;

    private KoreanFonts() {}

    /** the launcher's progress line and bar: "Korean fonts: <map> (done of total MB)", over all the maps */
    private static XisoExtractor.Progress progress;
    private static String current;
    private static long done, total, reported;

    private static void report(long add) {
        done += add;
        if (progress != null && (done - reported >= (4 << 20) || done == total)) {
            reported = done;
            progress.report("Korean fonts: " + current, done, total);
        }
    }

    /** Called by XisoExtractor.extractMaps when it has put the maps into destination/maps. */
    static void fixMaps(File destination, XisoExtractor.Progress progress) {
        File[] files = new File(destination, "maps").listFiles();
        if (files == null)
            return;
        java.util.List<File> maps = new java.util.ArrayList<>();
        long sum = 0;
        for (File file : files) {
            if (!file.getName().toLowerCase().endsWith(".map"))
                continue;
            long length = koreanMapLength(file);
            if (length > 0) {
                maps.add(file);
                sum += length;
            }
        }
        KoreanFonts.progress = progress;
        done = reported = 0;
        total = sum;
        for (File file : maps) {
            current = file.getName();
            long before = done;
            try {
                fix(file);
            } catch (Throwable error) {
                android.util.Log.w("HaloKoreanFonts", file + ": " + error);
            }
            done = before;                              // a map counts its whole length, however it ended
            report(koreanMapLength(file));
        }
        KoreanFonts.progress = null;
    }

    /** the decompressed length of a map of the Korean build, else 0 */
    private static long koreanMapLength(File file) {
        byte[] head = new byte[HEADER];
        try (InputStream in = new FileInputStream(file)) {
            readFully(in, head, 0, HEADER);
        } catch (IOException error) {
            return 0;
        }
        if (u32(head, 0) != 0x68656164 || u32(head, 4) != 5)
            return 0;
        try {
            if (!new String(head, 0x40, BUILD.length(), "US-ASCII").equals(BUILD))
                return 0;
        } catch (UnsupportedEncodingException error) {
            return 0;
        }
        return u32(head, 8) & 0xFFFFFFFFL;
    }

    private static int u32(byte[] b, int o) {
        return (b[o] & 0xFF) | (b[o + 1] & 0xFF) << 8 | (b[o + 2] & 0xFF) << 16 | (b[o + 3] & 0xFF) << 24;
    }

    private static int u16(byte[] b, int o) {
        return (b[o] & 0xFF) | (b[o + 1] & 0xFF) << 8;
    }

    private static void put32(byte[] b, int o, int v) {
        b[o] = (byte) v; b[o + 1] = (byte) (v >> 8); b[o + 2] = (byte) (v >> 16); b[o + 3] = (byte) (v >> 24);
    }

    private static void put16(byte[] b, int o, int v) {
        b[o] = (byte) v; b[o + 1] = (byte) (v >> 8);
    }

    private static void readFully(InputStream in, byte[] b, int off, int len) throws IOException {
        while (len > 0) {
            int n = in.read(b, off, len);
            if (n < 0)
                throw new EOFException();
            off += n;
            len -= n;
        }
    }

    private static void copy(InputStream in, OutputStream out, long count, byte[] buffer) throws IOException {
        while (count > 0) {
            int n = in.read(buffer, 0, (int) Math.min(buffer.length, count));
            if (n < 0)
                throw new EOFException();
            out.write(buffer, 0, n);
            count -= n;
            report(n);
        }
    }

    /** true if the map was changed */
    static boolean fix(File file) throws IOException {
        byte[] head = new byte[HEADER];
        try (InputStream in = new FileInputStream(file)) {
            readFully(in, head, 0, HEADER);
        }
        if (u32(head, 0) != 0x68656164 || u32(head, 4) != 5 || u32(head, 0x7FC) != 0x666F6F74)
            return false;
        String build = new String(head, 0x40, BUILD.length(), "US-ASCII");
        if (!build.equals(BUILD) || head[0x40 + BUILD.length()] != 0)
            return false;
        long tagOffset = u32(head, 0x10) & 0xFFFFFFFFL;
        int tagSize = u32(head, 0x14);
        if (tagOffset < HEADER || tagSize <= 0 || tagSize > 0x2000000)
            return false;

        File temporary = new File(file.getPath() + ".kr");
        boolean changed;
        byte[] buffer = new byte[1 << 16];
        try (InputStream raw = new BufferedInputStream(new FileInputStream(file), 1 << 16);
             FileOutputStream rawOut = new FileOutputStream(temporary)) {
            readFully(raw, new byte[HEADER], 0, HEADER);
            rawOut.write(head);
            InflaterInputStream in = new InflaterInputStream(raw, new Inflater(), 1 << 16);
            Deflater deflater = new Deflater(6);
            DeflaterOutputStream out = new DeflaterOutputStream(new BufferedOutputStream(rawOut, 1 << 16), deflater, 1 << 16);
            copy(in, out, tagOffset - HEADER, buffer);
            byte[] tags = new byte[tagSize];
            readFully(in, tags, 0, tagSize);
            changed = patchTags(tags);
            if (changed) {
                out.write(tags);
                report(tagSize);
                int n;
                while ((n = in.read(buffer)) > 0) {
                    out.write(buffer, 0, n);
                    report(n);
                }
                out.finish();
                out.flush();
            }
            deflater.end();
        }
        if (!changed) {
            temporary.delete();
            return false;
        }
        if (!file.delete() || !temporary.renameTo(file))
            throw new IOException("could not replace " + file);
        return true;
    }

    /** the tag data, loaded at BASE */
    private static boolean patchTags(byte[] t) {
        int instances = (int) ((u32(t, 0) & 0xFFFFFFFFL) - BASE);
        int count = u32(t, 0x0C);
        boolean changed = false;
        for (int i = 0; i < count; i++) {
            int e = instances + i * 0x20;
            if (u32(t, e) != 0x666F6E74)                 // 'font'
                continue;
            int font = (int) ((u32(t, e + 0x14) & 0xFFFFFFFFL) - BASE);
            int tableCount = u32(t, font + 0x30);
            long tableAddress = u32(t, font + 0x34) & 0xFFFFFFFFL;
            int characterCount = u32(t, font + 0x7C);
            long characterAddress = u32(t, font + 0x80) & 0xFFFFFFFFL;
            if (tableCount != 256 || characterCount < 95)
                continue;
            int tables = (int) (tableAddress - BASE);
            boolean empty = true;
            for (int k = 0; k < 256 && empty; k++)
                empty = u32(t, tables + k * 12) == 0;
            if (!empty)
                continue;
            int characters = (int) (characterAddress - BASE);
            boolean ascii = true;
            for (int k = 0; k < 95 && ascii; k++)
                ascii = u16(t, characters + k * 0x14) == 0x20 + k;
            if (!ascii)
                continue;
            long dataAddress = tableAddress + TABLES * 12;
            int data = (int) (dataAddress - BASE);
            for (int table = 0; table < TABLES; table++) {
                put32(t, tables + table * 12, 256);
                put32(t, tables + table * 12 + 4, (int) (dataAddress + table * 512));
                put32(t, tables + table * 12 + 8, 0);
                for (int low = 0; low < 256; low++) {
                    int code = table * 256 + low;
                    int index = -1;
                    if (code >= 0x20 && code < 0x7F)
                        index = code - 0x20;
                    else if (code >= 0x100 && code - HANGUL_OFFSET < characterCount)
                        index = code - HANGUL_OFFSET;
                    put16(t, data + code * 2, index);
                }
            }
            put32(t, font + 0x30, TABLES);
            changed = true;
        }
        return changed;
    }
}
