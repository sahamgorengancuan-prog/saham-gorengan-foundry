"""Vector rig for the Saham Gorengan "Bull" mascot.

One rig = one identity. Every card, scene and short re-uses these exact shapes,
colours and proportions, so the character never drifts between posts. Only the
pose (arms), expression (face) and accessory change per scene.

Coordinate space: the bust lives in MASCOT_BOX (x, y, w, h). Bottom edge is the
torso cut, so place the mascot with its bottom on a desk/frame edge.
"""
from __future__ import annotations

import math

OUT = "#0A1633"      # outline navy (all strokes)
RED = "#E5283C"      # body
RED_D = "#B71A2D"    # shade / eyelids / tuft
RED_L = "#F2606C"    # muzzle / inner ear
HORN = "#5E0E18"
HORN_L = "#8A1B28"
SHIRT = "#1B4C8F"
SHIRT_D = "#123B78"
COLLAR = "#2D66B5"
GOLD = "#FFCD35"
WHITE = "#FAFDFF"
BROW = "#2A0710"
DARK = "#3D0710"

MASCOT_BOX = (-100, 20, 800, 680)
STROKE = 7

POSES = {
    # arm = (shoulder, elbow, wrist, hand, hand_angle_deg or None=auto)
    "idle": {"R": ((448, 566), (482, 640), (474, 730), None, None),
             "L": ((152, 566), (118, 640), (126, 730), None, None)},
    "explain": {"R": ((448, 566), (536, 486), (544, 360), "point", -8),
                "L": ((152, 566), (118, 640), (126, 730), None, None)},
    "celebrate": {"R": ((448, 566), (532, 470), (508, 330), "fist", -12),
                  "L": ((152, 566), (118, 640), (126, 730), None, None)},
    "think": {"R": ((448, 566), (440, 660), (352, 474), "fist", -40),
              "L": ((152, 566), (118, 640), (126, 730), None, None)},
    "warn": {"R": ((448, 566), (528, 610), (506, 478), "palm", 0),
             "L": ((152, 566), (118, 640), (126, 730), None, None)},
    "present": {"R": ((448, 566), (548, 606), (606, 532), "palm", 52),
                "L": ((152, 566), (118, 640), (126, 730), None, None)},
    "shrug": {"R": ((448, 566), (532, 612), (560, 530), "palm", 30),
              "L": ((152, 566), (68, 612), (40, 530), "palm", -30)},
    "wave": {"R": ((448, 566), (536, 500), (526, 372), "palm", 8),
             "L": ((152, 566), (118, 640), (126, 730), None, None)},
    "double_point": {"R": ((448, 566), (540, 520), (596, 420), "point", 40),
                     "L": ((152, 566), (60, 520), (4, 420), "point", -40)},
}

EXPRESSIONS = ("smirk", "happy", "worried", "serious", "think", "shock")
ACCESSORIES = ("none", "glasses", "tie", "headset")


def _mirror(svg_inner: str) -> str:
    return f'<g transform="translate(600,0) scale(-1,1)">{svg_inner}</g>'


def _horn(mirror: bool = False) -> str:
    d = ("M 215 200 C 160 205 110 175 118 110 C 121 85 135 68 152 58 "
         "C 145 85 150 120 178 140 C 195 152 215 160 232 165 Z")
    hi = "M 205 190 C 160 190 128 165 130 115"
    g = (f'<path d="{d}" fill="{HORN}" stroke="{OUT}" stroke-width="{STROKE}" stroke-linejoin="round"/>'
         f'<path d="{hi}" fill="none" stroke="{HORN_L}" stroke-width="9" stroke-linecap="round"/>')
    return _mirror(g) if mirror else g


def _ear(mirror: bool = False) -> str:
    g = (f'<path d="M 176 246 C 140 228 104 234 90 252 C 108 272 146 278 178 270 Z" fill="{RED}" '
         f'stroke="{OUT}" stroke-width="{STROKE}" stroke-linejoin="round"/>'
         f'<path d="M 166 252 C 142 244 120 246 108 254 C 122 264 146 267 167 264 Z" fill="{RED_L}"/>')
    return _mirror(g) if mirror else g


def _torso(accessory: str) -> str:
    body = ("M 110 700 C 110 600 140 530 215 500 C 245 488 270 482 300 482 "
            "C 330 482 355 488 385 500 C 460 530 490 600 490 700 Z")
    shade = "M 400 505 C 462 535 490 600 490 700 L 430 700 C 432 610 420 548 400 505 Z"
    neck = "M 262 425 L 338 425 L 338 492 L 300 522 L 262 492 Z"
    collar_l = "M 300 518 L 242 482 L 226 512 L 262 552 Z"
    parts = [
        f'<path d="{body}" fill="{SHIRT}" stroke="{OUT}" stroke-width="{STROKE}" stroke-linejoin="round"/>',
        f'<path d="{shade}" fill="{SHIRT_D}"/>',
        f'<path d="M 300 525 L 300 700" stroke="{SHIRT_D}" stroke-width="6"/>',
        f'<path d="{neck}" fill="{RED_D}" stroke="{OUT}" stroke-width="{STROKE}" stroke-linejoin="round"/>',
    ]
    if accessory == "tie":
        parts.append(f'<path d="M 288 520 L 312 520 L 322 548 L 306 640 L 300 650 L 294 640 L 278 548 Z" '
                     f'fill="{GOLD}" stroke="{OUT}" stroke-width="5" stroke-linejoin="round"/>')
    else:
        for y in (565, 622, 680):
            parts.append(f'<circle cx="300" cy="{y}" r="7" fill="{GOLD}" stroke="{OUT}" stroke-width="3"/>')
    for mirror in (False, True):
        c = (f'<path d="{collar_l}" fill="{COLLAR}" stroke="{OUT}" stroke-width="{STROKE - 1}" '
             f'stroke-linejoin="round"/>')
        parts.append(_mirror(c) if mirror else c)
    return "".join(parts)


def _head() -> str:
    head = ("M 300 150 C 380 150 430 190 432 260 C 434 310 410 330 405 350 "
            "C 402 420 370 446 300 446 C 230 446 198 420 195 350 "
            "C 190 330 166 310 168 260 C 170 190 220 150 300 150 Z")
    shade = ("M 408 250 C 430 300 412 336 404 356 C 400 412 374 438 330 444 "
             "C 378 420 390 380 391 340 C 392 300 404 282 408 250 Z")
    tuft = ("M 262 170 C 264 140 284 130 294 146 C 300 124 322 124 326 146 "
            "C 334 134 348 146 340 170 Z")
    return (f'<path d="{head}" fill="{RED}" stroke="{OUT}" stroke-width="{STROKE}" stroke-linejoin="round"/>'
            f'<path d="{shade}" fill="{RED_D}" opacity=".85"/>'
            f'<path d="{tuft}" fill="{RED_D}" stroke="{OUT}" stroke-width="{STROKE - 2}" stroke-linejoin="round"/>')


def _muzzle(mouth: str) -> str:
    return (f'<ellipse cx="300" cy="390" rx="100" ry="56" fill="{RED_L}" stroke="{OUT}" stroke-width="5"/>'
            f'<ellipse cx="263" cy="378" rx="14" ry="10" fill="{DARK}" transform="rotate(-12 263 378)"/>'
            f'<ellipse cx="337" cy="378" rx="14" ry="10" fill="{DARK}" transform="rotate(12 337 378)"/>'
            + mouth)


def _eyes(look=(0, 0), lid=0.0, wide=False, closed=False, pupil_r=11) -> str:
    out = []
    ry = 24 if wide else 21
    for cx, toward in ((250, 4), (350, -4)):
        cy = 288
        if closed:
            out.append(f'<path d="M {cx-24} {cy+2} Q {cx} {cy+12} {cx+24} {cy+2}" fill="none" '
                       f'stroke="{OUT}" stroke-width="7" stroke-linecap="round"/>')
            continue
        out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="25" ry="{ry}" fill="{WHITE}" stroke="{OUT}" stroke-width="5"/>')
        px, py = cx + toward + look[0], cy + 3 + look[1]
        out.append(f'<circle cx="{px}" cy="{py}" r="{pupil_r}" fill="{OUT}"/>'
                   f'<circle cx="{px + 4}" cy="{py - 4}" r="3.2" fill="{WHITE}"/>')
        if lid > 0:
            top = cy - ry
            cut = top + 2 * ry * lid
            out.append(f'<path d="M {cx-27} {top-4} L {cx+27} {top-4} L {cx+27} {cut} '
                       f'Q {cx} {cut+6} {cx-27} {cut} Z" fill="{RED_D}" stroke="{OUT}" stroke-width="4" '
                       f'stroke-linejoin="round"/>')
    return "".join(out)


def _brows(left: str, right: str) -> str:
    return "".join(f'<path d="{d}" fill="none" stroke="{BROW}" stroke-width="13" stroke-linecap="round"/>'
                   for d in (left, right))


def _face(expression: str, blink: bool) -> str:
    mouth_line = 'fill="none" stroke="{c}" stroke-width="6" stroke-linecap="round"'.format(c=OUT)
    extra = ""
    if expression == "happy":
        brows = _brows("M 222 252 Q 250 236 278 250", "M 322 250 Q 350 236 378 252")
        eyes = (f'<path d="M 228 296 Q 250 270 272 296" fill="none" stroke="{OUT}" stroke-width="8" stroke-linecap="round"/>'
                f'<path d="M 328 296 Q 350 270 372 296" fill="none" stroke="{OUT}" stroke-width="8" stroke-linecap="round"/>')
        mouth = (f'<path d="M 262 410 Q 300 452 338 410 Z" fill="{DARK}" stroke="{OUT}" stroke-width="5" stroke-linejoin="round"/>'
                 f'<path d="M 282 428 Q 300 444 318 428 Q 300 420 282 428 Z" fill="{RED_L}"/>')
    elif expression == "worried":
        brows = _brows("M 224 260 Q 252 254 276 240", "M 324 240 Q 348 254 376 260")
        eyes = _eyes(wide=True, pupil_r=8, closed=blink)
        mouth = f'<path d="M 270 424 Q 285 412 300 424 Q 315 436 330 424" {mouth_line}/>'
        extra = (f'<path d="M 440 214 C 452 236 458 248 446 258 C 434 266 420 254 426 240 Z" fill="#8FD3FF" '
                 f'stroke="{OUT}" stroke-width="4" stroke-linejoin="round"/>')
    elif expression == "serious":
        brows = _brows("M 222 258 L 280 268", "M 320 268 L 378 258")
        eyes = _eyes(lid=0.38, closed=blink)
        mouth = f'<path d="M 276 424 L 326 424" {mouth_line}/>'
    elif expression == "think":
        brows = _brows("M 222 260 Q 250 250 278 258", "M 322 246 Q 350 224 380 236")
        eyes = _eyes(look=(6, -8), closed=blink)
        mouth = f'<path d="M 288 426 Q 304 418 320 428" {mouth_line}/>'
        extra = (f'<text x="468" y="190" font-family="Plus Jakarta Sans, Inter, sans-serif" font-weight="800" '
                 f'font-size="110" fill="{GOLD}" stroke="{OUT}" stroke-width="5" paint-order="stroke">?</text>')
    elif expression == "shock":
        brows = _brows("M 222 240 Q 250 220 278 236", "M 322 236 Q 350 220 378 240")
        eyes = _eyes(wide=True, pupil_r=7, closed=blink)
        mouth = f'<ellipse cx="300" cy="424" rx="16" ry="18" fill="{DARK}" stroke="{OUT}" stroke-width="5"/>'
    else:  # smirk: the brand default — confident, friendly
        brows = _brows("M 222 256 Q 250 240 278 258", "M 322 258 Q 350 240 378 256")
        eyes = _eyes(lid=0.3, closed=blink)
        mouth = f'<path d="M 266 420 Q 300 434 338 410" {mouth_line}/>'
    return _muzzle(mouth) + eyes + brows + extra


def _hand(kind: str) -> str:
    """Hand drawn around origin (wrist) pointing up (-y)."""
    sw = f'stroke="{OUT}" stroke-width="{STROKE - 1}" stroke-linejoin="round"'
    if kind == "fist":
        return (f'<rect x="-38" y="-70" width="76" height="66" rx="26" fill="{RED}" {sw}/>'
                f'<path d="M -20 -66 L -20 -44 M 0 -68 L 0 -44 M 20 -66 L 20 -44" stroke="{OUT}" stroke-width="4" '
                f'stroke-linecap="round"/>'
                f'<path d="M -38 -30 Q -18 -22 4 -30" fill="none" stroke="{OUT}" stroke-width="5" stroke-linecap="round"/>')
    if kind == "point":
        return (f'<rect x="-10" y="-118" width="24" height="64" rx="12" fill="{RED}" {sw}/>'
                f'<rect x="-38" y="-66" width="76" height="62" rx="26" fill="{RED}" {sw}/>'
                f'<path d="M 12 -60 L 12 -42 M 26 -56 L 26 -42" stroke="{OUT}" stroke-width="4" stroke-linecap="round"/>'
                f'<path d="M -38 -30 Q -18 -22 4 -30" fill="none" stroke="{OUT}" stroke-width="5" stroke-linecap="round"/>')
    if kind == "palm":
        fingers = "".join(
            f'<rect x="{x}" y="{y}" width="20" height="{h}" rx="10" fill="{RED}" {sw}/>'
            for x, y, h in ((-36, -112, 56), (-14, -122, 64), (8, -118, 60), (28, -104, 50)))
        return (fingers
                + f'<rect x="-40" y="-76" width="82" height="74" rx="28" fill="{RED}" {sw}/>'
                + f'<path d="M -40 -40 C -66 -52 -70 -78 -58 -86 C -46 -80 -38 -62 -30 -56" fill="{RED}" {sw}/>'
                + f'<path d="M -16 -40 Q 2 -30 22 -40" fill="none" stroke="{RED_D}" stroke-width="5" stroke-linecap="round"/>')
    return ""


def _arm(spec) -> str:
    (sx, sy), (ex, ey), (wx, wy), hand, angle = spec
    path = f"M {sx} {sy} L {ex} {ey} L {wx} {wy}"
    tube = (f'<path d="{path}" fill="none" stroke="{OUT}" stroke-width="{70 + 2 * STROKE}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{path}" fill="none" stroke="{SHIRT}" stroke-width="70" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')
    if not hand:
        return tube
    if angle is None:
        angle = math.degrees(math.atan2(wx - ex, -(wy - ey)))
    cuff = (f'<g transform="translate({wx},{wy}) rotate({angle})">'
            f'<rect x="-40" y="-14" width="80" height="26" rx="10" fill="{COLLAR}" stroke="{OUT}" stroke-width="5"/>'
            f'{_hand(hand)}</g>')
    return tube + cuff


def _accessory_face(accessory: str) -> str:
    if accessory == "glasses":
        return (f'<g fill="none" stroke="{OUT}" stroke-width="7">'
                f'<rect x="214" y="260" width="72" height="58" rx="18"/><rect x="314" y="260" width="72" height="58" rx="18"/>'
                f'<path d="M 286 284 Q 300 274 314 284"/></g>'
                f'<path d="M 222 270 L 240 268" stroke="{WHITE}" stroke-width="5" stroke-linecap="round" opacity=".7"/>')
    if accessory == "headset":
        return (f'<path d="M 170 250 C 170 120 430 120 430 250" fill="none" stroke="{OUT}" stroke-width="16"/>'
                f'<rect x="150" y="236" width="40" height="62" rx="14" fill="{OUT}"/>'
                f'<rect x="410" y="236" width="40" height="62" rx="14" fill="{OUT}"/>'
                f'<path d="M 180 296 C 200 380 240 400 262 400" fill="none" stroke="{OUT}" stroke-width="8"/>'
                f'<circle cx="266" cy="400" r="10" fill="{GOLD}" stroke="{OUT}" stroke-width="4"/>')
    return ""


def mascot_group(pose: str = "explain", expression: str = "smirk", accessory: str = "none",
                 flip: bool = False, blink: bool = False) -> str:
    """Return the mascot as an SVG <g> in MASCOT_BOX coordinates."""
    if pose not in POSES:
        raise ValueError(f"unknown pose {pose!r}; choose from {sorted(POSES)}")
    if expression not in EXPRESSIONS:
        raise ValueError(f"unknown expression {expression!r}; choose from {EXPRESSIONS}")
    p = POSES[pose]
    front_arms = []
    back_arms = []
    for side in ("L", "R"):
        spec = p[side]
        # arms that stay down sit behind the torso edge; raised arms are drawn in front of the head
        (back_arms if spec[3] is None else front_arms).append(_arm(spec))
    inner = ("".join(back_arms) + _torso(accessory) + _ear(False) + _ear(True) + _horn(False) + _horn(True)
             + _head() + _face(expression, blink) + _accessory_face(accessory) + "".join(front_arms))
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
