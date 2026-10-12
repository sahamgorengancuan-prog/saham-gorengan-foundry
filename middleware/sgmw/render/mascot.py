"""Vector rig for the Saham Gorengan "Bull" mascot (v2, matched to sahamgorengan.id art).

Reference: brand/reference/hero-bull-refined.webp (official site illustration).
Identity traits copied from it: long 3/4 bull face with a charcoal-grey muzzle,
spiky forehead/cheek fur, heavy brow ridge with narrowed confident eyes, thick
maroon crescent horns, pointed horizontal ears, muscular red body with chest fur,
dark-teal shirt with open collar and sleeves rolled above the elbow, big red fists,
cel shading (base / shadow / highlight) and dark-maroon outlines.

Coordinate space: MASCOT_BOX (x, y, w, h). Bottom edge is the torso cut.
"""
from __future__ import annotations

import math

LINE = "#2B0A10"      # outline (dark maroon, like the site art)
RED = "#D8192C"       # body base
RED_SH = "#A10F1E"    # cel shadow
RED_HI = "#F0434B"    # rim highlight
RED_DK = "#6E0A14"    # deep fur shadow
MUZ = "#4B4F5E"       # charcoal muzzle
MUZ_HI = "#666C7D"
MUZ_SH = "#353845"
NOSTRIL = "#17181F"
HORN = "#4A0A12"
HORN_HI = "#7C1824"
HORN_TIP = "#24050A"
SHIRT = "#24485E"     # dark teal shirt
SHIRT_SH = "#183244"
SHIRT_HI = "#33627C"
GOLD = "#F5C431"
WHITE = "#FAFDFF"
EYE = "#FFF6E8"

MASCOT_BOX = (-100, 20, 800, 680)
SW = 5  # outline width

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
    "shrug": {"R": ((466, 548), (546, 616), (574, 532), "palm", 30),
              "L": ((134, 548), (54, 616), (26, 532), "palm", -30)},
    "wave": {"R": ((466, 548), (548, 504), (538, 374), "palm", 8),
             "L": ((134, 548), (100, 650), (130, 740), None, None)},
    "double_point": {"R": ((466, 548), (552, 522), (610, 420), "point", 40),
                     "L": ((134, 548), (48, 522), (-10, 420), "point", -40)},
}

EXPRESSIONS = ("smirk", "happy", "worried", "serious", "think", "shock")
ACCESSORIES = ("none", "glasses", "tie", "headset")


def _o(width: float = SW) -> str:
    return f'stroke="{LINE}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"'


def _mirror(svg_inner: str) -> str:
    return f'<g transform="translate(600,0) scale(-1,1)">{svg_inner}</g>'


# ---------------- head ----------------
def _horn(right: bool) -> str:
    # thick crescent: base on the forehead, sweeps out and up, tip curls inward above the head
    d = ("M 246 192 C 198 202 146 188 128 146 C 110 102 124 56 168 34 C 188 24 212 22 232 28 "
         "C 204 40 182 62 174 92 C 166 126 188 154 252 166 Z")
    hi = "M 220 186 C 168 186 136 160 134 116"
    tip = "M 232 28 C 214 32 198 40 188 50 C 200 50 212 46 224 40 Z"
    g = (f'<path d="{d}" fill="{HORN}" {_o()}/>'
         f'<path d="{hi}" fill="none" stroke="{HORN_HI}" stroke-width="8" stroke-linecap="round"/>'
         f'<path d="{tip}" fill="{HORN_TIP}"/>')
    if right:  # 3/4 view: far horn a bit smaller and higher
        return f'<g transform="translate(600,0) scale(-1,1) translate(14,-6) scale(0.95)">{g}</g>'
    return g


def _ear(right: bool) -> str:
    g = (f'<path d="M 196 246 C 160 222 120 222 92 236 C 118 262 156 276 198 274 Z" fill="{RED}" {_o()}/>'
         f'<path d="M 186 252 C 158 238 130 236 112 242 C 132 258 158 266 186 266 Z" fill="{RED_DK}"/>'
         f'<path d="M 120 240 C 140 236 160 238 176 246" fill="none" stroke="{RED_HI}" stroke-width="4" '
         f'stroke-linecap="round"/>')
    if right:
        return f'<g transform="translate(600,0) scale(-1,1) translate(8,-6)">{g}</g>'
    return g


def _head() -> str:
    # long 3/4 face: wide furry brow, cheeks with fur spikes, snout tapering to the grey muzzle
    head = ("M 300 150 C 352 150 392 168 408 206 L 418 196 L 414 228 C 420 250 420 274 410 298 "
            "L 424 306 L 404 320 C 398 344 392 360 384 376 L 216 376 C 206 360 200 344 196 320 "
            "L 176 306 L 190 298 C 180 274 180 250 186 228 L 182 196 L 194 206 C 208 168 248 150 300 150 Z")
    shade_l = ("M 196 228 C 190 260 192 292 204 318 C 210 344 216 362 226 376 L 244 376 "
               "C 230 344 222 300 228 250 C 214 244 204 236 196 228 Z")
    hi_r = "M 392 214 C 404 238 406 262 400 286"
    tuft = ("M 238 176 L 252 132 L 266 160 L 280 118 L 296 154 L 312 112 L 326 152 L 344 120 "
            "L 352 160 L 368 136 L 366 182 C 340 168 270 166 238 176 Z")
    tuft_sh = "M 252 172 L 262 150 L 272 168 L 290 140 L 300 166 L 318 138 L 328 166 L 346 146 L 350 174 Z"
    return (f'<path d="{head}" fill="{RED}" {_o()}/>'
            f'<path d="{shade_l}" fill="{RED_SH}"/>'
            f'<path d="{hi_r}" fill="none" stroke="{RED_HI}" stroke-width="6" stroke-linecap="round"/>'
            f'<path d="{tuft}" fill="{RED}" {_o(SW - 1)}/>'
            f'<path d="{tuft_sh}" fill="{RED_SH}"/>')


def _muzzle(mouth: str, teeth: bool = False) -> str:
    muz = ("M 226 366 C 228 342 256 330 306 330 C 360 330 388 342 390 366 C 392 404 368 436 310 438 "
           "C 252 438 224 404 226 366 Z")
    hi = "M 246 348 C 268 340 334 336 370 348"
    nl = "M 266 372 C 262 364 268 356 278 358 C 288 360 290 370 284 376 C 278 380 270 380 266 372 Z"
    nr = "M 336 370 C 334 360 342 354 352 357 C 360 360 360 370 354 375 C 348 380 340 378 336 370 Z"
    return (f'<path d="{muz}" fill="{MUZ}" {_o()}/>'
            f'<path d="M 232 392 C 246 426 276 436 308 436 C 276 428 250 412 240 384 Z" fill="{MUZ_SH}"/>'
            f'<path d="{hi}" fill="none" stroke="{MUZ_HI}" stroke-width="6" stroke-linecap="round"/>'
            f'<path d="{nl}" fill="{NOSTRIL}"/><path d="{nr}" fill="{NOSTRIL}"/>' + mouth)


def _brow(left_d: str, right_d: str) -> str:
    # heavy brow ridge = thick dark-red shape with outline
    return "".join(f'<path d="{d}" fill="{RED_DK}" {_o(3)}/>' for d in (left_d, right_d))


def _eye(cx, cy, w=24, h=12, look=(3, 0), lid=0.45, wide=False, closed=False, tilt=0, pupil=7):
    if closed:
        return (f'<path d="M {cx - w} {cy} Q {cx} {cy + 10} {cx + w} {cy - 2}" fill="none" stroke="{LINE}" '
                f'stroke-width="6" stroke-linecap="round"/>')
    h = h * (1.7 if wide else 1)
    eye = (f'<g transform="rotate({tilt} {cx} {cy})">'
           f'<path d="M {cx - w} {cy} Q {cx} {cy - h * 1.6} {cx + w} {cy} Q {cx} {cy + h * 1.2} {cx - w} {cy} Z" '
           f'fill="{EYE}" {_o(3.5)}/>'
           f'<circle cx="{cx + look[0]}" cy="{cy + look[1]}" r="{pupil}" fill="{NOSTRIL}"/>'
           f'<circle cx="{cx + look[0] + 2.5}" cy="{cy + look[1] - 2.5}" r="2.2" fill="{WHITE}"/>')
    if lid > 0 and not wide:
        top = cy - h * 1.6
        cut = top + (cy - top) * lid * 1.6
        eye += (f'<path d="M {cx - w - 2} {top - 6} L {cx + w + 2} {top - 6} L {cx + w + 2} {cut - 3} '
                f'Q {cx} {cut + 3} {cx - w - 2} {cut} Z" fill="{RED_SH}" {_o(3)}/>')
    return eye + "</g>"


def _face(expression: str, blink: bool) -> str:
    ml = f'fill="none" stroke="{LINE}" stroke-width="5" stroke-linecap="round"'
    extra = ""
    ey, lx, rx = 282, 252, 350
    if expression == "happy":
        brows = _brow("M 222 254 Q 252 236 282 250 L 280 258 Q 252 246 224 262 Z",
                      "M 320 248 Q 350 234 378 250 L 376 258 Q 350 244 322 256 Z")
        eyes = (_eye(lx, ey, closed=True) + _eye(rx, ey - 2, closed=True))
        mouth = (f'<path d="M 252 404 Q 304 446 362 400 Q 306 420 252 404 Z" fill="{NOSTRIL}" {_o(3)}/>'
                 f'<path d="M 262 408 Q 306 420 352 404 L 350 410 Q 306 426 264 414 Z" fill="{WHITE}"/>')
    elif expression == "worried":
        brows = _brow("M 224 266 Q 252 258 282 240 L 284 248 Q 254 266 226 274 Z",
                      "M 318 240 Q 348 258 376 264 L 374 272 Q 346 266 316 248 Z")
        eyes = _eye(lx, ey, wide=True, look=(0, 2), pupil=5, closed=blink) + \
            _eye(rx, ey, wide=True, look=(0, 2), pupil=5, closed=blink)
        mouth = f'<path d="M 270 418 Q 287 408 304 418 Q 321 428 338 416" {ml}/>'
        extra = (f'<path d="M 428 204 C 442 228 448 242 436 252 C 424 260 410 248 416 234 Z" fill="#8FD3FF" '
                 f'{_o(3)}/>')
    elif expression == "serious":
        brows = _brow("M 222 262 L 284 270 L 282 278 L 222 270 Z", "M 318 270 L 378 262 L 378 270 L 320 278 Z")
        eyes = _eye(lx, ey + 2, lid=0.55, closed=blink) + _eye(rx, ey + 2, lid=0.55, closed=blink)
        mouth = f'<path d="M 272 416 L 336 414" {ml}/>'
    elif expression == "think":
        brows = _brow("M 222 260 Q 252 252 282 260 L 280 268 Q 252 262 224 268 Z",
                      "M 320 248 Q 350 222 382 234 L 380 242 Q 350 232 322 256 Z")
        eyes = _eye(lx, ey, look=(6, -5), lid=0.25, closed=blink) + _eye(rx, ey - 2, look=(6, -5), lid=0.25,
                                                                         closed=blink)
        mouth = f'<path d="M 286 418 Q 306 410 328 420" {ml}/>'
        extra = (f'<text x="470" y="186" font-family="Plus Jakarta Sans, Inter, sans-serif" font-weight="800" '
                 f'font-size="110" fill="{GOLD}" stroke="{LINE}" stroke-width="5" paint-order="stroke">?</text>')
    elif expression == "shock":
        brows = _brow("M 222 244 Q 252 222 282 238 L 280 246 Q 252 232 224 252 Z",
                      "M 320 238 Q 350 222 380 244 L 378 252 Q 350 232 322 246 Z")
        eyes = _eye(lx, ey, wide=True, look=(0, 0), pupil=5, closed=blink) + \
            _eye(rx, ey, wide=True, look=(0, 0), pupil=5, closed=blink)
        mouth = f'<ellipse cx="306" cy="414" rx="16" ry="18" fill="{NOSTRIL}" {_o(3)}/>'
    else:  # smirk — the site's default: confident, brows angled down to the centre
        brows = _brow("M 220 252 Q 252 246 286 266 L 282 274 Q 252 258 222 262 Z",
                      "M 316 264 Q 350 242 382 248 L 380 258 Q 350 254 320 272 Z")
        eyes = _eye(lx, ey + 2, look=(5, 1), lid=0.45, tilt=6, closed=blink) + \
            _eye(rx, ey + 2, look=(5, 1), lid=0.45, tilt=-6, closed=blink)
        mouth = (f'<path d="M 262 414 Q 300 426 346 404" {ml}/>'
                 f'<path d="M 340 400 Q 350 404 352 412" {ml}/>')
    teeth = expression == "happy"
    return _muzzle(mouth, teeth) + eyes + brows + extra


# ---------------- body ----------------
def _torso(accessory: str) -> str:
    body = ("M 70 700 C 64 604 88 524 168 488 C 214 468 258 462 300 462 "
            "C 342 462 386 468 432 488 C 512 524 536 604 530 700 Z")
    shade = "M 440 494 C 506 528 534 604 530 700 L 466 700 C 468 616 458 546 440 494 Z"
    shade_l = "M 160 494 C 112 520 76 588 70 700 L 112 700 C 116 612 132 546 160 494 Z"
    neck = ("M 226 420 L 374 420 C 384 448 396 470 414 498 L 300 556 L 186 498 C 204 470 216 448 226 420 Z")
    neck_sh = "M 226 420 L 262 420 C 254 456 246 486 240 528 L 186 498 C 204 470 216 448 226 420 Z"
    chest_fur = ("M 244 512 L 258 538 L 270 516 L 284 546 L 296 518 L 308 548 L 320 518 L 334 544 "
                 "L 348 512 L 358 532 L 300 576 Z")
    lapel_l = "M 300 576 L 200 494 L 176 522 L 232 606 L 260 596 Z"
    parts = [
        f'<path d="{body}" fill="{SHIRT}" {_o()}/>',
        f'<path d="{shade}" fill="{SHIRT_SH}"/>',
        f'<path d="{shade_l}" fill="{SHIRT_SH}" opacity=".6"/>',
        f'<path d="{neck}" fill="{RED}" {_o()}/>',
        f'<path d="{neck_sh}" fill="{RED_SH}"/>',
        f'<path d="{chest_fur}" fill="{RED_SH}" {_o(3)}/>',
        f'<path d="M 300 572 L 300 700" stroke="{SHIRT_SH}" stroke-width="5"/>',
    ]
    for y in (612, 662):
        parts.append(f'<circle cx="312" cy="{y}" r="6" fill="{SHIRT_HI}" {_o(2.5)}/>')
    if accessory == "tie":
        parts.append(f'<path d="M 290 548 L 310 548 L 318 576 L 306 664 L 300 674 L 294 664 L 282 576 Z" '
                     f'fill="{GOLD}" {_o(3.5)}/>')
    for mirror in (False, True):
        lap = (f'<path d="{lapel_l}" fill="{SHIRT_HI}" {_o()}/>'
               f'<path d="M 232 606 L 260 596 L 250 562 Z" fill="{SHIRT}" opacity=".7"/>')
        parts.append(_mirror(lap) if mirror else lap)
    return "".join(parts)


def _tube(path: str, width: float, base: str, shadow: str, hi: str | None = None) -> str:
    out = (f'<path d="{path}" fill="none" stroke="{LINE}" stroke-width="{width + 2 * SW}" stroke-linecap="round" '
           f'stroke-linejoin="round"/>'
           f'<path d="{path}" fill="none" stroke="{shadow}" stroke-width="{width}" stroke-linecap="round" '
           f'stroke-linejoin="round"/>'
           f'<path d="{path}" fill="none" stroke="{base}" stroke-width="{width * 0.62}" stroke-linecap="round" '
           f'stroke-linejoin="round" transform="translate(-{width * 0.12:.1f},-{width * 0.08:.1f})"/>')
    if hi:
        out += (f'<path d="{path}" fill="none" stroke="{hi}" stroke-width="{width * 0.12:.1f}" '
                f'stroke-linecap="round" transform="translate(-{width * 0.3:.1f},-{width * 0.22:.1f})" opacity=".8"/>')
    return out


def _hand(kind: str) -> str:
    """Hand around origin (wrist) pointing up (-y)."""
    o = _o(SW - 0.5)
    if kind == "fist":
        knuckles = "".join(f'<circle cx="{x}" cy="-70" r="13" fill="{RED}" {o}/>' for x in (-27, -9, 9, 27))
        return (f'<path d="M -40 -64 C -44 -40 -40 -12 -28 -2 L 30 -2 C 42 -12 46 -40 42 -64 Z" fill="{RED}" {o}/>'
                + knuckles
                + f'<path d="M -40 -64 L 42 -64 L 42 -56 L -40 -56 Z" fill="{RED}"/>'
                + f'<path d="M -30 -34 C -16 -40 4 -40 16 -30 C 6 -20 -16 -20 -30 -34 Z" fill="{RED_SH}" {_o(3)}/>'
                + f'<path d="M 22 -60 L 22 -18 C 30 -24 36 -40 34 -60 Z" fill="{RED_SH}"/>')
    if kind == "point":
        return (f'<rect x="-12" y="-128" width="26" height="70" rx="13" fill="{RED}" {o}/>'
                f'<path d="M -40 -62 C -44 -38 -40 -12 -28 -2 L 30 -2 C 42 -12 46 -38 42 -62 Z" fill="{RED}" {o}/>'
                + "".join(f'<circle cx="{x}" cy="-62" r="12" fill="{RED}" {o}/>' for x in (-26, 26))
                + f'<path d="M -40 -62 L 42 -62 L 42 -54 L -40 -54 Z" fill="{RED}"/>'
                + f'<path d="M -30 -32 C -16 -38 4 -38 16 -28 C 6 -18 -16 -18 -30 -32 Z" fill="{RED_SH}" {_o(3)}/>'
                + f'<path d="M 4 -124 L 4 -62" stroke="{RED_SH}" stroke-width="6" stroke-linecap="round"/>')
    if kind == "palm":
        fingers = "".join(
            f'<rect x="{x}" y="{y}" width="22" height="{h}" rx="11" fill="{RED}" {o}/>'
            for x, y, h in ((-40, -118, 60), (-16, -128, 70), (8, -124, 66), (30, -108, 54)))
        return (fingers
                + f'<path d="M -44 -76 C -46 -40 -40 -12 -28 -2 L 30 -2 C 44 -12 48 -40 46 -76 Z" fill="{RED}" {o}/>'
                + f'<path d="M -44 -42 C -70 -54 -76 -82 -62 -92 C -48 -86 -40 -66 -32 -58" fill="{RED}" {o}/>'
                + f'<path d="M -18 -40 Q 2 -28 24 -40" fill="none" stroke="{RED_SH}" stroke-width="5" '
                  f'stroke-linecap="round"/>')
    return ""


def _arm(spec) -> str:
    (sx, sy), (ex, ey), (wx, wy), hand, angle = spec
    # rolled sleeve covers the upper arm and stops just past the elbow (site art)
    t = 0.18
    cx, cy = ex + (wx - ex) * t, ey + (wy - ey) * t
    sleeve = _tube(f"M {sx} {sy} L {ex} {ey} L {cx:.0f} {cy:.0f}", 96, SHIRT, SHIRT_SH, SHIRT_HI)
    forearm = _tube(f"M {cx:.0f} {cy:.0f} L {wx} {wy}", 90, RED, RED_SH, RED_HI)
    ang = math.degrees(math.atan2(wy - ey, wx - ex))
    cuff = (f'<g transform="translate({cx:.0f},{cy:.0f}) rotate({ang + 90:.0f})">'
            f'<rect x="-54" y="-15" width="108" height="30" rx="13" fill="{SHIRT_HI}" {_o()}/>'
            f'<path d="M -40 0 L 40 0" stroke="{SHIRT}" stroke-width="4"/></g>')
    out = forearm + sleeve + cuff
    if hand:
        if angle is None:
            angle = math.degrees(math.atan2(wx - ex, -(wy - ey)))
        out += f'<g transform="translate({wx},{wy}) rotate({angle}) scale(1.22)">{_hand(hand)}</g>'
    return out


def _accessory_face(accessory: str) -> str:
    if accessory == "glasses":
        return (f'<g fill="none" stroke="{LINE}" stroke-width="6">'
                f'<rect x="216" y="258" width="72" height="50" rx="16"/><rect x="314" y="254" width="72" height="50" rx="16"/>'
                f'<path d="M 288 280 Q 300 270 314 278"/></g>'
                f'<path d="M 226 266 L 244 264" stroke="{WHITE}" stroke-width="4" stroke-linecap="round" opacity=".7"/>')
    if accessory == "headset":
        return (f'<path d="M 182 250 C 182 116 418 116 418 250" fill="none" stroke="{LINE}" stroke-width="16"/>'
                f'<rect x="162" y="234" width="40" height="64" rx="14" fill="#1E2530" {_o(3)}/>'
                f'<rect x="398" y="234" width="40" height="64" rx="14" fill="#1E2530" {_o(3)}/>'
                f'<path d="M 190 296 C 206 380 236 404 262 406" fill="none" stroke="{LINE}" stroke-width="8"/>'
                f'<circle cx="266" cy="406" r="10" fill="{GOLD}" {_o(3)}/>')
    return ""


def _sparkle(pose: str) -> str:
    """Gold motion sparks next to a raised fist/hand (signature of the site art)."""
    if pose not in ("celebrate", "wave", "explain"):
        return ""
    x, y = POSES[pose]["R"][2]
    return "".join(
        f'<path d="M {x + dx} {y + dy} L {x + dx + ex} {y + dy + ey}" stroke="{GOLD}" stroke-width="9" '
        f'stroke-linecap="round"/>'
        for dx, dy, ex, ey in ((40, -120, 18, -34), (66, -96, 34, -18), (-6, -132, -4, -36)))


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
    head = (_horn(True) + _ear(True) + _ear(False) + _horn(False) + _head() + _face(expression, blink)
            + _accessory_face(accessory))
    inner = ("".join(back) + _torso(accessory)
             + f'<g transform="translate(300 300) scale(1.12) translate(-300 -300) translate(0 64)">{head}</g>'
             + "".join(front) + _sparkle(pose))
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
