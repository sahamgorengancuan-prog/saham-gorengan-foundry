"""Vector rig for the Saham Gorengan "Bull" mascot (v3, matched to the official sahamgorengan.id art).

References (brand/reference/): hero-bull-refined, faq-bull, community-bull-phone, premium-bull-phone.
Style rules copied from them:
  * modern flat vector, NO outlines — shapes are pure fills; detail is drawn with darker same-hue lines
    (fur strands, finger creases, shirt folds);
  * bright red body with a slightly darker shadow tone, slight 3/4 view facing right;
  * charcoal-grey muzzle on the lower-right of the face, dark nostrils, smile line on the muzzle;
  * small dark eyes with a tiny glint and THICK near-black brows (V = determined, arched = friendly);
  * jagged fur fringe on the forehead, cheeks/jaw and chest;
  * dark-maroon horns with darker bands, sweeping out and up with the tips turning inward (wide U);
  * big leaf-shaped ears sticking out sideways below the horns;
  * big head on broad muscular shoulders, dark-teal shirt (open collar, sleeves rolled above the
    elbow), thick red forearms, big four-finger hands; gold/blue spark accents.

Coordinate space: MASCOT_BOX (x, y, w, h). Bottom edge is the torso cut.
"""
from __future__ import annotations

import math

RED = "#E5161F"
RED_SH = "#B9111A"
RED_DK = "#7E0B12"      # detail strokes (fur, creases)
RED_IN = "#A80F18"      # inner ear
MUZ = "#4A4B53"
MUZ_SH = "#3A3B42"
INK = "#1C1416"         # brows, eyes, nostrils, mouth
HORN = "#5A1217"
HORN_BAND = "#3E0B0F"
HORN_HI = "#70202A"
SHIRT = "#1F4C60"
SHIRT_SH = "#173B4C"
SHIRT_DK = "#11303E"
SHIRT_HI = "#27596F"
GOLD = "#F2B630"
BLUE = "#1D63E6"
WHITE = "#FFFFFF"

MASCOT_BOX = (-100, 20, 800, 680)

POSES = {
    # arm = (shoulder, elbow, wrist, hand, hand_angle_deg or None=auto)
    "idle": {"R": ((466, 548), (500, 650), (470, 740), None, None),
             "L": ((134, 548), (100, 650), (130, 740), None, None)},
    "explain": {"R": ((466, 548), (548, 500), (556, 372), "point", -6),
                "L": ((134, 548), (100, 650), (130, 740), None, None)},
    "celebrate": {"R": ((466, 548), (552, 480), (522, 336), "fist", -14),
                  "L": ((134, 548), (100, 650), (130, 740), None, None)},
    "think": {"R": ((466, 548), (448, 662), (372, 470), "fist", -44),
              "L": ((134, 548), (100, 650), (130, 740), None, None)},
    "warn": {"R": ((466, 548), (540, 612), (514, 482), "palm", 0),
             "L": ((134, 548), (100, 650), (130, 740), None, None)},
    "present": {"R": ((466, 548), (560, 608), (618, 534), "palm", 54),
                "L": ((134, 548), (100, 650), (130, 740), None, None)},
    "shrug": {"R": ((466, 548), (546, 616), (590, 560), "palm_up", 70),
              "L": ((134, 548), (54, 616), (10, 560), "palm_up", -70)},
    "wave": {"R": ((466, 548), (548, 504), (538, 374), "palm", 8),
             "L": ((134, 548), (100, 650), (130, 740), None, None)},
    "double_point": {"R": ((466, 548), (552, 522), (610, 420), "point", 40),
                     "L": ((134, 548), (48, 522), (-10, 420), "point", -40)},
}

EXPRESSIONS = ("smirk", "happy", "worried", "serious", "think", "shock")
ACCESSORIES = ("none", "glasses", "tie", "headset")


def _mirror(svg_inner: str) -> str:
    return f'<g transform="translate(600,0) scale(-1,1)">{svg_inner}</g>'


def _line(d: str, color: str = RED_DK, w: float = 4) -> str:
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'


# ---------------- head ----------------
def _horn(far: bool) -> str:
    # short, thick crescent: out from the top of the head, up, then the tip turns inward over the head
    d = ("M 250 204 C 206 206 160 190 146 150 C 132 110 150 70 186 56 C 204 48 224 48 242 56 "
         "C 216 62 198 80 196 104 C 194 132 214 160 268 176 Z")
    bands = (_line("M 160 168 Q 176 150 194 146", HORN_BAND, 8) + _line("M 146 118 Q 166 110 186 116", HORN_BAND, 8)
             + _line("M 164 76 Q 182 76 196 88", HORN_BAND, 7))
    g = f'<path d="{d}" fill="{HORN}"/>' + bands + _line("M 226 196 C 190 192 162 174 154 140", HORN_HI, 6)
    if far:  # far horn: mirrored, slightly smaller, pulled toward the face (3/4 view)
        return (f'<g transform="translate(600,0) scale(-1,1) translate(-14,-8) '
                f'translate(300 140) scale(0.9) translate(-300 -140)">{g}</g>')
    return g


def _ear(far: bool) -> str:
    if far:
        return (f'<path d="M 394 232 C 432 214 474 220 498 244 C 470 268 424 274 392 264 Z" fill="{RED}"/>'
                f'<path d="M 402 240 C 432 230 462 234 480 246 C 460 260 428 262 404 256 Z" fill="{RED_IN}"/>')
    return (f'<path d="M 214 236 C 170 216 118 222 84 252 C 120 280 176 288 218 278 Z" fill="{RED}"/>'
            f'<path d="M 204 246 C 172 236 134 238 108 254 C 136 270 176 274 206 266 Z" fill="{RED_IN}"/>')


def _head() -> str:
    head = ("M 296 158 C 350 156 388 180 398 222 C 404 252 404 290 404 318 L 424 376 "
            "C 384 432 334 454 282 448 L 262 454 L 266 440 L 244 446 L 250 430 L 226 432 L 238 418 "
            "L 214 414 L 228 402 L 204 394 L 220 384 L 198 372 L 214 362 L 194 348 L 210 340 "
            "C 196 300 192 262 200 230 C 214 184 250 160 300 158 Z")
    shade = ("M 200 232 C 194 262 196 300 210 338 L 194 348 L 214 362 L 198 372 L 220 384 L 204 394 "
             "L 228 402 L 214 414 L 238 418 L 226 432 L 250 430 C 236 400 226 360 226 310 C 226 280 214 254 200 232 Z")
    bangs = ("M 232 206 L 252 166 L 260 190 L 282 150 L 288 184 L 312 140 L 314 180 L 342 150 L 340 184 "
             "L 368 162 L 360 202 C 330 188 268 190 232 206 Z")
    strands = (_line("M 270 150 L 268 182") + _line("M 300 142 L 296 178") + _line("M 330 150 L 324 182")
               + _line("M 252 178 L 256 196") + _line("M 214 330 L 230 312") + _line("M 222 372 L 238 356")
               + _line("M 244 414 L 258 398"))
    return (f'<path d="{head}" fill="{RED}"/><path d="{shade}" fill="{RED_SH}"/>'
            f'<path d="{bangs}" fill="{RED}"/>' + strands)


def _muzzle(mouth: str) -> str:
    muz = ("M 282 348 C 290 320 334 306 380 310 C 422 314 448 338 444 370 C 440 406 406 428 360 428 "
           "C 314 428 276 408 276 376 C 276 366 278 356 282 348 Z")
    return (f'<path d="{muz}" fill="{MUZ}"/>'
            f'<path d="M 282 386 C 292 414 324 426 360 426 C 328 418 302 404 294 382 Z" fill="{MUZ_SH}"/>'
            f'<ellipse cx="326" cy="342" rx="10" ry="6" fill="{INK}" transform="rotate(-18 326 342)"/>'
            f'<ellipse cx="402" cy="338" rx="10" ry="6" fill="{INK}" transform="rotate(14 402 338)"/>'
            + f'<g transform="translate(16 2)">{mouth}</g>')


def _brows(l: str, r: str) -> str:
    return _line(l, INK, 12) + _line(r, INK, 11)


def _eye(cx, cy, kind="sharp", look=(2, 0), closed=False):
    if closed:
        return _line(f"M {cx - 13} {cy} Q {cx} {cy + 8} {cx + 13} {cy - 1}", INK, 6)
    if kind == "dot":  # friendly (faq art): round black eye with glint
        return (f'<circle cx="{cx + look[0]}" cy="{cy + look[1]}" r="9" fill="{INK}"/>'
                f'<circle cx="{cx + look[0] + 3}" cy="{cy + look[1] - 3}" r="3" fill="{WHITE}"/>')
    if kind == "wide":
        return (f'<ellipse cx="{cx}" cy="{cy}" rx="13" ry="15" fill="{WHITE}"/>'
                f'<circle cx="{cx + look[0]}" cy="{cy + look[1]}" r="6" fill="{INK}"/>')
    # sharp (hero/community/premium art): small dark almond under a heavy brow
    return (f'<path d="M {cx - 12} {cy} Q {cx} {cy - 9} {cx + 12} {cy} Q {cx} {cy + 6} {cx - 12} {cy} Z" fill="{INK}"/>'
            f'<circle cx="{cx + 3}" cy="{cy - 2}" r="2.4" fill="{WHITE}"/>')


def _face(expression: str, blink: bool) -> str:
    lx, ly, rx, ry = 262, 274, 346, 264
    extra = ""
    if expression == "happy":
        brows = _brows("M 236 252 Q 258 238 284 248", "M 326 240 Q 348 228 372 236")
        eyes = _eye(lx, ly, "dot", closed=blink) + _eye(rx, ry, "dot", closed=blink)
        mouth = (f'<path d="M 296 390 Q 344 428 396 384 Q 346 404 296 390 Z" fill="{INK}"/>'
                 f'<path d="M 304 392 Q 344 404 388 388 L 386 393 Q 346 410 306 398 Z" fill="{WHITE}"/>')
    elif expression == "worried":
        brows = _brows("M 238 262 Q 260 256 284 242", "M 324 234 Q 346 244 370 248")
        eyes = _eye(lx, ly, "wide", (0, 3), blink) + _eye(rx, ry, "wide", (0, 3), blink)
        mouth = _line("M 306 402 Q 322 392 340 402 Q 358 412 376 400", INK, 5)
        extra = '<path d="M 424 210 C 438 234 444 248 432 258 C 420 266 406 254 412 240 Z" fill="#8FD3FF"/>'
    elif expression == "serious":
        brows = _brows("M 234 256 L 286 268", "M 324 260 L 374 246")
        eyes = _eye(lx, ly + 2, closed=blink) + _eye(rx, ry + 2, closed=blink)
        mouth = _line("M 306 400 L 380 396", INK, 5)
    elif expression == "think":
        brows = _brows("M 236 260 Q 260 252 286 260", "M 324 244 Q 350 222 378 230")
        eyes = _eye(lx, ly, "dot", (4, -4), blink) + _eye(rx, ry, "dot", (4, -4), blink)
        mouth = _line("M 318 402 Q 340 394 364 404", INK, 5)
        extra = (f'<text x="470" y="190" font-family="Plus Jakarta Sans, Inter, sans-serif" font-weight="800" '
                 f'font-size="110" fill="{GOLD}">?</text>')
    elif expression == "shock":
        brows = _brows("M 236 242 Q 258 224 284 236", "M 326 230 Q 350 216 374 230")
        eyes = _eye(lx, ly, "wide", (0, 0), blink) + _eye(rx, ry, "wide", (0, 0), blink)
        mouth = f'<ellipse cx="344" cy="400" rx="15" ry="17" fill="{INK}"/>'
    else:  # smirk — determined grin of the hero/community/premium art (V brows)
        brows = _brows("M 232 246 L 288 266", "M 322 258 L 378 236")
        eyes = _eye(lx, ly + 2, closed=blink) + _eye(rx, ry + 2, closed=blink)
        mouth = (_line("M 300 394 Q 340 410 392 384", INK, 5) + _line("M 388 380 Q 398 384 398 394", INK, 5))
    return _muzzle(mouth) + eyes + brows + extra


# ---------------- body ----------------
def _torso(accessory: str) -> str:
    body = ("M 70 700 C 64 604 88 524 168 488 C 214 468 258 462 300 462 "
            "C 342 462 386 468 432 488 C 512 524 536 604 530 700 Z")
    shade_l = "M 168 488 C 108 516 72 590 70 700 L 140 700 C 138 610 146 540 168 488 Z"
    neck = "M 232 420 L 380 420 C 388 450 398 474 412 500 L 300 560 L 188 500 C 202 474 214 450 232 420 Z"
    fur = ("M 238 500 L 252 528 L 262 506 L 276 538 L 288 510 L 300 544 L 312 510 L 326 538 L 338 506 "
           "L 350 528 L 362 500 L 300 556 Z")
    lapel = "M 300 560 L 196 488 L 170 516 L 230 604 L 262 594 Z"
    parts = [f'<path d="{body}" fill="{SHIRT}"/>', f'<path d="{shade_l}" fill="{SHIRT_SH}"/>',
             f'<path d="{neck}" fill="{RED}"/>',
             f'<path d="M 232 420 L 262 420 C 256 452 250 480 246 520 L 188 500 C 202 474 214 450 232 420 Z" fill="{RED_SH}"/>',
             f'<path d="{fur}" fill="{RED_SH}"/>',
             _line("M 300 560 L 300 700", SHIRT_DK, 5), _line("M 120 620 Q 150 600 176 610", SHIRT_DK, 5),
             _line("M 470 600 Q 446 620 452 650", SHIRT_DK, 5), _line("M 360 640 Q 380 660 372 690", SHIRT_DK, 4)]
    if accessory == "tie":
        parts.append(f'<path d="M 290 540 L 310 540 L 318 568 L 306 660 L 300 670 L 294 660 L 282 568 Z" fill="{GOLD}"/>')
    for mirror in (False, True):
        lap = (f'<path d="{lapel}" fill="{SHIRT_HI}"/>'
               f'<path d="M 230 604 L 262 594 L 250 560 Z" fill="{SHIRT_SH}"/>')
        parts.append(_mirror(lap) if mirror else lap)
    return "".join(parts)


def _tube(path: str, width: float, base: str, shadow: str) -> str:
    return (f'<path d="{path}" fill="none" stroke="{shadow}" stroke-width="{width}" stroke-linecap="round" '
            f'stroke-linejoin="round"/>'
            f'<path d="{path}" fill="none" stroke="{base}" stroke-width="{width * 0.7:.1f}" stroke-linecap="round" '
            f'stroke-linejoin="round" transform="translate(-{width * 0.1:.1f},-{width * 0.1:.1f})"/>')


def _hand(kind: str) -> str:
    """Hand around origin (wrist) pointing up (-y). Flat, creases in dark red."""
    if kind == "fist":
        k = "".join(f'<circle cx="{x}" cy="-70" r="14" fill="{RED}"/>' for x in (-27, -9, 9, 27))
        return (f'<path d="M -42 -66 C -46 -40 -40 -10 -26 0 L 30 0 C 44 -10 48 -40 44 -66 Z" fill="{RED}"/>' + k
                + f'<path d="M -30 -36 C -14 -42 6 -42 18 -30 C 8 -18 -14 -18 -30 -36 Z" fill="{RED_SH}"/>'
                + _line("M -18 -76 L -18 -58", RED_DK, 3.5) + _line("M 0 -78 L 0 -58", RED_DK, 3.5)
                + _line("M 18 -76 L 18 -58", RED_DK, 3.5))
    if kind == "point":
        return (f'<rect x="-12" y="-130" width="28" height="72" rx="14" fill="{RED}"/>'
                f'<path d="M -42 -64 C -46 -38 -40 -10 -26 0 L 30 0 C 44 -10 48 -38 44 -64 Z" fill="{RED}"/>'
                + "".join(f'<circle cx="{x}" cy="-62" r="13" fill="{RED}"/>' for x in (-26, 26))
                + f'<path d="M -30 -34 C -14 -40 6 -40 18 -28 C 8 -16 -14 -16 -30 -34 Z" fill="{RED_SH}"/>'
                + _line("M 2 -120 L 2 -66", RED_SH, 6))
    if kind == "palm_up":
        fingers = "".join(f'<rect x="-11" y="-112" width="22" height="58" rx="11" fill="{RED}" transform="rotate({a})"/>'
                          for a in (-28, -9, 10, 28))
        return (fingers + f'<ellipse cx="0" cy="-44" rx="46" ry="34" fill="{RED}"/>'
                + f'<rect x="-11" y="-96" width="22" height="54" rx="11" fill="{RED}" transform="rotate(-62)"/>'
                + _line("M -24 -40 Q 0 -26 26 -40", RED_SH, 6) + _line("M -14 -72 L -10 -60", RED_DK, 3)
                + _line("M 12 -72 L 10 -60", RED_DK, 3))
    if kind == "palm":
        fingers = "".join(f'<rect x="{x}" y="{y}" width="24" height="{h}" rx="12" fill="{RED}"/>'
                          for x, y, h in ((-42, -118, 60), (-16, -130, 72), (10, -126, 68), (34, -110, 56)))
        return (fingers
                + f'<path d="M -46 -78 C -48 -40 -40 -10 -26 0 L 30 0 C 46 -10 50 -40 48 -78 Z" fill="{RED}"/>'
                + f'<path d="M -46 -42 C -74 -54 -80 -84 -64 -94 C -50 -88 -40 -66 -32 -58 Z" fill="{RED}"/>'
                + _line("M -20 -44 Q 2 -30 26 -44", RED_SH, 6) + _line("M -4 -96 L -4 -80", RED_DK, 3)
                + _line("M 22 -94 L 22 -80", RED_DK, 3))
    return ""


def _arm(spec) -> str:
    (sx, sy), (ex, ey), (wx, wy), hand, angle = spec
    t = 0.18  # rolled sleeve ends just past the elbow
    cx, cy = ex + (wx - ex) * t, ey + (wy - ey) * t
    sleeve = _tube(f"M {sx} {sy} L {ex} {ey} L {cx:.0f} {cy:.0f}", 100, SHIRT, SHIRT_SH)
    forearm = _tube(f"M {cx:.0f} {cy:.0f} L {wx} {wy}", 88, RED, RED_SH)
    ang = math.degrees(math.atan2(wy - ey, wx - ex))
    cuff = (f'<g transform="translate({cx:.0f},{cy:.0f}) rotate({ang + 90:.0f})">'
            f'<rect x="-54" y="-16" width="108" height="32" rx="14" fill="{SHIRT_HI}"/>'
            f'{_line("M -44 2 L 44 2", SHIRT_DK, 4)}</g>')
    out = forearm + sleeve + cuff
    if hand:
        if angle is None:
            angle = math.degrees(math.atan2(wx - ex, -(wy - ey)))
        out += f'<g transform="translate({wx},{wy}) rotate({angle}) scale(1.22)">{_hand(hand)}</g>'
    return out


def _accessory_face(accessory: str) -> str:
    if accessory == "glasses":
        return (f'<g fill="none" stroke="{INK}" stroke-width="7">'
                f'<rect x="230" y="252" width="62" height="44" rx="14"/><rect x="316" y="242" width="62" height="44" rx="14"/>'
                f'<path d="M 292 272 Q 304 262 316 266"/></g>')
    if accessory == "headset":
        return (f'<path d="M 190 252 C 190 118 412 118 412 252" fill="none" stroke="{INK}" stroke-width="16"/>'
                f'<rect x="170" y="236" width="40" height="64" rx="14" fill="#1E2530"/>'
                f'<rect x="392" y="236" width="40" height="64" rx="14" fill="#1E2530"/>'
                f'<path d="M 196 298 C 212 380 250 404 290 406" fill="none" stroke="{INK}" stroke-width="8"/>'
                f'<circle cx="294" cy="406" r="10" fill="{GOLD}"/>')
    return ""


def _sparks(pose: str) -> str:
    """Gold spark accents next to a raised fist/hand (signature of the official art)."""
    if pose not in ("celebrate", "wave", "explain"):
        return ""
    x, y = POSES[pose]["R"][2]
    return "".join(_line(f"M {x + a} {y + b} L {x + a + c} {y + b + d}", GOLD, 12)
                   for a, b, c, d in ((40, -124, 16, -36), (68, -100, 34, -16), (-8, -136, -2, -38)))


def mascot_group(pose: str = "explain", expression: str = "smirk", accessory: str = "none",
                 flip: bool = False, blink: bool = False) -> str:
    """Return the mascot as an SVG <g> in MASCOT_BOX coordinates."""
    if pose not in POSES:
        raise ValueError(f"unknown pose {pose!r}; choose from {sorted(POSES)}")
    if expression not in EXPRESSIONS:
        raise ValueError(f"unknown expression {expression!r}; choose from {EXPRESSIONS}")
    p = POSES[pose]
    back, front = [], []
    for side in ("L", "R"):
        spec = p[side]
        (back if spec[3] is None else front).append(_arm(spec))
    head = (_horn(True) + _ear(True) + _horn(False) + _ear(False) + _head() + _face(expression, blink)
            + _accessory_face(accessory))
    inner = ("".join(back) + _torso(accessory)
             + f'<g transform="translate(300 300) scale(1.12) translate(-300 -300) translate(0 64)">{head}</g>'
             + "".join(front) + _sparks(pose))
    return _mirror(inner) if flip else f"<g>{inner}</g>"


def mascot_svg(pose: str = "explain", expression: str = "smirk", accessory: str = "none",
               flip: bool = False, blink: bool = False, width: int | None = None) -> str:
    x, y, w, h = MASCOT_BOX
    size = f' width="{width}" height="{round(width * h / w)}"' if width else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}"{size}>'
            f'{mascot_group(pose, expression, accessory, flip, blink)}</svg>')


def place(pose: str, expression: str, x: float, y: float, height: float, accessory: str = "none",
          flip: bool = False, blink: bool = False) -> str:
    """Embed the mascot in a larger SVG. (x, y) = bottom-centre of the bust; height in px."""
    bx, by, bw, bh = MASCOT_BOX
    s = height / bh
    tx = x - (bx + bw / 2) * s
    ty = y - (by + bh) * s
    return (f'<g transform="translate({tx:.1f},{ty:.1f}) scale({s:.4f})">'
            f'{mascot_group(pose, expression, accessory, flip, blink)}</g>')
