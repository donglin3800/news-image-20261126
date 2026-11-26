#!/usr/bin/env python3
"""One Day, Five Stories -- Thursday, 26 November 2026.

A program that draws a single poster summing up five world-news stories
of 26 November 2026 and writes it to /output/entry.png (or
$MAKEFUN_OUTPUT_DIR/entry.png).

Pure Python 3.13 standard library. No network, no files read, no clock,
no randomness: the same run always writes the same bytes. Every pixel on
the poster -- banner, globe, five drawn icons, headlines and captions --
is produced by the drawing code below, including a small 5x7 bitmap font
defined by hand in this file.

The five stories (each checked against its first publication):
  1. The US proposes a new round of tariffs on 14 trading partners,
     China facing 20%, up to 40% if the trade truce fails (USTR
     announcement, Wednesday 25 Nov US time; published 26 Nov in
     Asia-Pacific, e.g. The Hindu BusinessLine dated 26 Nov 2026).
  2. Macy's postpones its 100th Thanksgiving Day Parade in New York to
     Saturday 28 Nov, the first weather postponement in its history
     (announced Wednesday 25 Nov; the parade itself was 26 Nov).
  3. A fuel tanker overturns on Cairo's Ring Road and the fire kills at
     least 31 people, the toll rising in 26 Nov updates (AP, CNN,
     25-26 Nov 2026).
  4. Judges in Jerusalem recommend prosecutors drop the bribery charge
     in Case 4000 against Prime Minister Netanyahu and reconsider
     Case 2000 (hearing Wednesday 25 Nov 2026; Reuters, CNN).
  5. ESA's Hera mission releases the first close images of Dimorphos:
     a stadium-sized crater flattens one face of the asteroid struck
     by NASA's DART in 2022 (ESA, Reuters, CNN, 25 Nov 2026).
"""

import os
import struct
import zlib

W, H = 1024, 1024

# Palette: deep navy night, warm paper, gold rule, five story accents.
NAVY = (13, 27, 51)
NAVY2 = (19, 38, 68)
GOLD = (212, 168, 60)
PAPER = (247, 243, 232)
PAPER2 = (238, 231, 214)
INK = (18, 24, 38)
GREY = (94, 100, 114)
WHITE = (255, 255, 255)
ACCENTS = [(196, 58, 42), (31, 120, 180), (214, 116, 28), (88, 86, 160), (46, 130, 110)]

# ---------------------------------------------------------------- PNG writer
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, pixels, w, h):
    raw = b"".join(b"\x00" + bytes(pixels[y * w * 3:(y + 1) * w * 3])
                   for y in range(h))
    png = (b"\x89PNG\r\n\x1a\n"
           + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + _chunk(b"IDAT", zlib.compress(raw, 9))
           + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c, t=1):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            for a in range(t):
                for b in range(t):
                    self.set(x0 + a, y0 + b, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            dx = int((r * r - (yy - cy) ** 2) ** 0.5) if abs(yy - cy) <= r else 0
            for xx in range(cx - dx, cx + dx + 1):
                self.set(xx, yy, c)

    def ring(self, cx, cy, r, c, t=3):
        for k in range(t):
            rr = r - k
            for a in range(0, 360, 1):
                import math
                x = cx + int(rr * math.cos(a * math.pi / 180))
                y = cy + int(rr * math.sin(a * math.pi / 180))
                self.set(x, y, c)

    def triangle(self, pts, c):
        (x0, y0), (x1, y1), (x2, y2) = pts
        ymin, ymax = min(y0, y1, y2), max(y0, y1, y2)
        for yy in range(ymin, ymax + 1):
            xs = []
            for (ax, ay), (bx, by) in (((x0, y0), (x1, y1)),
                                       ((x1, y1), (x2, y2)),
                                       ((x2, y2), (x0, y0))):
                if ay == by:
                    continue
                if min(ay, by) <= yy < max(ay, by):
                    xs.append(ax + (yy - ay) * (bx - ax) / (by - ay))
            if len(xs) >= 2:
                for xx in range(int(min(xs)), int(max(xs)) + 1):
                    self.set(xx, yy, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(cy - ry, cy + ry + 1):
            t = 1 - ((yy - cy) / ry) ** 2
            if t < 0:
                continue
            dx = int(rx * t ** 0.5)
            for xx in range(cx - dx, cx + dx + 1):
                self.set(xx, yy, c)


# ------------------------------------------------------------- bitmap font
# Each glyph is 7 rows of 5 pixels, "#" on, "." off.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(cv, x, y, s, scale, color):
    cx = x
    for ch in s.upper():
        glyph = FONT.get(ch, FONT[" "])
        for r, row in enumerate(glyph):
            for cc, bit in enumerate(row):
                if bit == "1":
                    cv.fill_rect(cx + cc * scale, y + r * scale,
                                 scale, scale, color)
        cx += 6 * scale
    return cx


def draw_centered(cv, cx, y, s, scale, color):
    draw_text(cv, cx - text_width(s, scale) // 2, y, s, scale, color)


def wrap(s, max_chars):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        nxt = (cur + " " + wd).strip()
        if len(nxt) <= max_chars:
            cur = nxt
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------- icons
# Each icon is drawn inside a 120x120 square at (x, y) on its own
# coloured tile, using only the canvas primitives above.

def icon_tariffs(cv, x, y):
    cv.fill_rect(x, y, 120, 120, (24, 48, 84))
    # three rising bars: the tariff rates climbing
    cv.fill_rect(x + 18, y + 78, 20, 30, GOLD)
    cv.fill_rect(x + 50, y + 58, 20, 50, (232, 196, 96))
    cv.fill_rect(x + 82, y + 34, 20, 74, (240, 220, 150))
    cv.line(x + 12, y + 108, x + 108, y + 108, WHITE, 2)
    cv.line(x + 14, y + 96, x + 52, y + 62, (230, 90, 70), 3)
    cv.line(x + 52, y + 62, x + 92, y + 30, (230, 90, 70), 3)
    cv.line(x + 92, y + 30, x + 84, y + 32, (230, 90, 70), 3)
    cv.line(x + 92, y + 30, x + 90, y + 38, (230, 90, 70), 3)


def icon_parade(cv, x, y):
    cv.fill_rect(x, y, 120, 120, (135, 190, 225))
    # balloon, strings, basket: a parade balloon over the city
    cv.ellipse(x + 60, y + 48, 38, 30, (196, 58, 42))
    cv.ellipse(x + 60, y + 48, 38, 30, (196, 58, 42))
    cv.fill_rect(x + 48, y + 34, 24, 8, (150, 40, 30))
    cv.line(x + 42, y + 74, x + 52, y + 96, INK, 2)
    cv.line(x + 78, y + 74, x + 68, y + 96, INK, 2)
    cv.fill_rect(x + 48, y + 96, 24, 14, (120, 84, 40))
    cv.fill_rect(x, y + 112, 120, 8, (60, 60, 70))
    cv.disc(x + 18, y + 18, 2, WHITE)
    cv.disc(x + 100, y + 26, 2, WHITE)


def icon_fire(cv, x, y):
    cv.fill_rect(x, y, 120, 120, (40, 32, 28))
    # city blocks at the bottom, flame above them
    cv.fill_rect(x + 10, y + 88, 24, 32, (70, 60, 55))
    cv.fill_rect(x + 42, y + 78, 22, 42, (70, 60, 55))
    cv.fill_rect(x + 72, y + 92, 26, 28, (70, 60, 55))
    cv.triangle([(x + 60, y + 12), (x + 34, y + 78), (x + 88, y + 78)],
                (214, 116, 28))
    cv.triangle([(x + 60, y + 34), (x + 44, y + 80), (x + 78, y + 80)],
                (240, 190, 60))
    cv.triangle([(x + 60, y + 56), (x + 52, y + 80), (x + 70, y + 80)],
                (250, 230, 140))
    cv.fill_rect(x + 16, y + 94, 4, 4, (250, 230, 140))
    cv.fill_rect(x + 48, y + 84, 4, 4, (250, 230, 140))


def icon_court(cv, x, y):
    cv.fill_rect(x, y, 120, 120, (28, 52, 96))
    # courthouse: pediment, three columns, steps
    cv.triangle([(x + 14, y + 26), (x + 106, y + 26), (x + 60, y + 6)],
                (232, 226, 208))
    cv.fill_rect(x + 14, y + 26, 92, 6, (232, 226, 208))
    for cx in (24, 52, 80):
        cv.fill_rect(x + cx, y + 34, 14, 58, (232, 226, 208))
        cv.fill_rect(x + cx - 3, y + 32, 20, 4, (232, 226, 208))
        cv.fill_rect(x + cx - 3, y + 90, 20, 4, (232, 226, 208))
    cv.fill_rect(x + 10, y + 96, 100, 5, (232, 226, 208))
    cv.fill_rect(x + 6, y + 103, 108, 5, (200, 192, 172))
    cv.disc(x + 60, y + 18, 3, GOLD)


def icon_asteroid(cv, x, y):
    cv.fill_rect(x, y, 120, 120, (10, 14, 26))
    # stars, the cratered asteroid, and the Hera spacecraft
    for sx, sy in ((14, 16), (100, 14), (108, 52), (16, 96), (104, 100),
                   (34, 10), (88, 88)):
        cv.disc(x + sx, y + sy, 2, WHITE)
    cv.disc(x + 52, y + 62, 34, (150, 148, 140))
    cv.disc(x + 44, y + 52, 12, (110, 108, 100))
    cv.disc(x + 64, y + 72, 8, (110, 108, 100))
    cv.disc(x + 58, y + 44, 5, (120, 118, 110))
    cv.fill_rect(x + 84, y + 22, 18, 8, (200, 200, 200))
    cv.fill_rect(x + 78, y + 24, 6, 4, GOLD)
    cv.line(x + 84, y + 26, x + 76, y + 40, (200, 200, 200), 2)


ICONS = [icon_tariffs, icon_parade, icon_fire, icon_court, icon_asteroid]

STORIES = [
    ("1  TRADE",
     "TARIFFS RETURN ON THANKSGIVING EVE",
     ["US PROPOSES NEW DUTIES ON 14 PARTNERS,",
      "CHINA FACES 20%, UP TO 40% IF TRUCE FAILS"]),
    ("2  NEW YORK",
     "MACY'S 100TH PARADE MOVED TO SATURDAY",
     ["FIRST WEATHER POSTPONEMENT IN ITS HISTORY,",
      "STORM GROUNDS THE BALLOONS IN NEW YORK"]),
    ("3  CAIRO",
     "CAIRO TANKER FIRE KILLS AT LEAST 31",
     ["FUEL TANKER OVERTURNS ON THE RING ROAD,",
      "BLAZE ENGULFS DOZENS OF CARS IN GIZA"]),
    ("4  JERUSALEM",
     "JUDGES URGE NETANYAHU CASE BE DROPPED",
     ["COURT DOUBTS THE BRIBERY CHARGE IN CASE 4000,",
      "PROSECUTORS ASKED TO RECONSIDER A SECOND"]),
    ("5  SPACE",
     "HERA SHOWS ASTEROID'S GIANT CRATER",
     ["DIMORPHOS FLATTENED BY THE DART IMPACT,",
      "STADIUM-SIZED CRATER, ROCK TUMBLING IN SPACE"]),
]


# ------------------------------------------------------------------ layout
def draw_globe(cv, cx, cy, r):
    cv.disc(cx, cy, r, (38, 90, 140))
    cv.ring(cx, cy, r, (120, 170, 210), 2)
    cv.disc(cx - r // 3, cy - r // 4, r // 4, (70, 150, 90))
    cv.disc(cx + r // 3, cy + r // 5, r // 5, (70, 150, 90))
    cv.disc(cx + r // 5, cy - r // 2, r // 6, (70, 150, 90))
    import math
    for dx in range(-r + 6, r - 5, 12):
        dy = int((r * r - dx * dx) ** 0.5)
        cv.line(cx + dx, cy - dy, cx + dx, cy + dy, (90, 140, 190), 1)
    cv.line(cx - r, cy, cx + r, cy, (120, 170, 210), 2)


def build():
    cv = Canvas(W, H, NAVY)
    # ---- banner
    draw_globe(cv, 92, 82, 52)
    draw_text(cv, 168, 38, "THE WORLD IN ONE DAY", 5, WHITE)
    draw_text(cv, 170, 92, "THURSDAY, 26 NOVEMBER 2026", 3, GOLD)
    cv.fill_rect(36, 148, 952, 4, GOLD)
    # ---- five story bands
    top = 168
    band_h = 158
    for i, (kicker, headline, lines) in enumerate(STORIES):
        y = top + i * band_h
        bg = PAPER if i % 2 == 0 else PAPER2
        cv.fill_rect(36, y, 952, band_h - 10, bg)
        cv.fill_rect(36, y, 10, band_h - 10, ACCENTS[i])
        ICONS[i](cv, 62, y + 14)
        tx = 206
        draw_text(cv, tx, y + 16, kicker, 2, ACCENTS[i])
        draw_text(cv, tx, y + 44, headline, 3, INK)
        yy = y + 84
        for ln in lines:
            draw_text(cv, tx, yy, ln, 2, GREY)
            yy += 26
        cv.fill_rect(tx, y + 128, 760, 2, (200, 192, 172))
    # ---- footer
    fy = top + 5 * band_h + 2
    draw_centered(cv, W // 2, fy, "SOURCES: USTR - REUTERS - AP - CNN - ESA - BBC", 2, (160, 170, 195))
    draw_centered(cv, W // 2, fy + 26, "FIVE STORIES, ONE DAY - 26 NOVEMBER 2026", 2, GOLD)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = build()
    write_png(os.path.join(out_dir, "entry.png"), cv.px, W, H)


if __name__ == "__main__":
    main()
