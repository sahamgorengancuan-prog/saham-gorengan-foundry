"""Brand prop library (flat vector, navy outline) + UI icons.

Every prop is drawn in a 200x200 box. Use prop(name, cx, cy, size) to place it.
The LLM pipeline should prefer these props over ad-hoc drawings so scenes stay
visually consistent; custom SVG is still allowed for topic-specific metaphors.
"""
from __future__ import annotations

OUT = "#0A1633"
NAVY = "#05183A"
BLUE = "#0B438E"
BLUE_L = "#8FB8FF"
GOLD = "#FFCD35"
GOLD_D = "#E0A800"
RED = "#ED2A3C"
WHITE = "#FAFDFF"
GREEN = "#48E5AD"
PINK = "#FF7182"
S = 'stroke="#0A1633" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"'

_P: dict[str, str] = {
    "chart_up": (f'<rect x="18" y="30" width="164" height="140" rx="18" fill="{WHITE}" {S}/>'
                 f'<path d="M40 70H160M40 105H160M40 140H160" stroke="#D6E2F5" stroke-width="5"/>'
                 f'<path d="M40 150 L80 118 L108 132 L156 70" fill="none" stroke="{GREEN}" stroke-width="12" '
                 f'stroke-linecap="round" stroke-linejoin="round"/>'
                 f'<path d="M134 66 L160 64 L158 90" fill="none" stroke="{GREEN}" stroke-width="12" '
                 f'stroke-linecap="round" stroke-linejoin="round"/>'),
    "chart_down": (f'<rect x="18" y="30" width="164" height="140" rx="18" fill="{WHITE}" {S}/>'
                   f'<path d="M40 70H160M40 105H160M40 140H160" stroke="#D6E2F5" stroke-width="5"/>'
                   f'<path d="M40 70 L82 104 L108 92 L156 146" fill="none" stroke="{PINK}" stroke-width="12" '
                   f'stroke-linecap="round" stroke-linejoin="round"/>'
                   f'<path d="M132 148 L158 148 L158 122" fill="none" stroke="{PINK}" stroke-width="12" '
                   f'stroke-linecap="round" stroke-linejoin="round"/>'),
    "candles": (f'<rect x="14" y="24" width="172" height="152" rx="18" fill="{BLUE}" {S}/>'
                + "".join(f'<path d="M{x} {a}V{b}" stroke="{WHITE}" stroke-width="5"/>'
                          f'<rect x="{x - 11}" y="{c}" width="22" height="{d}" rx="4" fill="{col}" {S}/>'
                          for x, a, b, c, d, col in ((50, 60, 150, 84, 46, GREEN), (88, 80, 160, 96, 40, PINK),
                                                     (126, 50, 130, 64, 46, GREEN), (162, 40, 110, 50, 40, GREEN)))),
    "coin": (f'<circle cx="100" cy="100" r="74" fill="{GOLD}" {S}/>'
             f'<circle cx="100" cy="100" r="54" fill="none" stroke="{GOLD_D}" stroke-width="7"/>'
             f'<text x="100" y="122" text-anchor="middle" font-family="Plus Jakarta Sans, sans-serif" '
             f'font-weight="800" font-size="58" fill="{OUT}">Rp</text>'),
    "money": (f'<rect x="16" y="52" width="168" height="96" rx="14" fill="#7FD1AE" {S}/>'
              f'<circle cx="100" cy="100" r="28" fill="#B9EBD4" {S}/>'
              f'<text x="100" y="112" text-anchor="middle" font-family="Plus Jakarta Sans, sans-serif" '
              f'font-weight="800" font-size="30" fill="{OUT}">Rp</text>'
              f'<path d="M36 72H58M142 128H164" stroke="{OUT}" stroke-width="6" stroke-linecap="round"/>'),
    "phone": (f'<rect x="56" y="14" width="88" height="172" rx="20" fill="{NAVY}" {S}/>'
              f'<rect x="66" y="34" width="68" height="124" rx="8" fill="{BLUE}"/>'
              f'<path d="M74 132 L92 112 L104 120 L126 90" fill="none" stroke="{GREEN}" stroke-width="7" '
              f'stroke-linecap="round" stroke-linejoin="round"/>'
              f'<circle cx="100" cy="172" r="6" fill="{BLUE_L}"/>'),
    "laptop": (f'<rect x="34" y="34" width="132" height="94" rx="10" fill="{NAVY}" {S}/>'
               f'<rect x="46" y="46" width="108" height="70" rx="4" fill="{BLUE}"/>'
               f'<path d="M58 104 L80 84 L96 94 L140 60" fill="none" stroke="{GOLD}" stroke-width="7" '
               f'stroke-linecap="round" stroke-linejoin="round"/>'
               f'<path d="M14 140 H186 L172 162 H28 Z" fill="#C9D6EA" {S}/>'),
    "magnifier": (f'<path d="M124 124 L176 176" stroke="{OUT}" stroke-width="26" stroke-linecap="round"/>'
                  f'<path d="M124 124 L172 172" stroke="{GOLD}" stroke-width="12" stroke-linecap="round"/>'
                  f'<circle cx="86" cy="86" r="58" fill="{BLUE_L}" fill-opacity=".55" {S}/>'
                  f'<path d="M58 70 Q66 52 86 48" fill="none" stroke="{WHITE}" stroke-width="8" stroke-linecap="round"/>'),
    "clock": (f'<circle cx="100" cy="104" r="76" fill="{WHITE}" {S}/>'
              f'<path d="M100 104 V58 M100 104 L132 120" stroke="{OUT}" stroke-width="9" stroke-linecap="round"/>'
              f'<circle cx="100" cy="104" r="8" fill="{RED}"/>'
              + "".join(f'<circle cx="{x}" cy="{y}" r="5" fill="{OUT}"/>'
                        for x, y in ((100, 40), (164, 104), (100, 168), (36, 104)))),
    "warning": (f'<path d="M100 22 L182 168 H18 Z" fill="{GOLD}" {S}/>'
                f'<path d="M100 72 V118" stroke="{OUT}" stroke-width="14" stroke-linecap="round"/>'
                f'<circle cx="100" cy="144" r="9" fill="{OUT}"/>'),
    "gauge": (f'<path d="M24 140 A76 76 0 0 1 176 140" fill="none" stroke="{OUT}" stroke-width="34"/>'
              f'<path d="M24 140 A76 76 0 0 1 62 74" fill="none" stroke="{GREEN}" stroke-width="22"/>'
              f'<path d="M66 72 A76 76 0 0 1 134 72" fill="none" stroke="{GOLD}" stroke-width="22"/>'
              f'<path d="M138 74 A76 76 0 0 1 176 140" fill="none" stroke="{RED}" stroke-width="22"/>'
              f'<path d="M100 140 L150 88" stroke="{OUT}" stroke-width="10" stroke-linecap="round"/>'
              f'<circle cx="100" cy="140" r="14" fill="{WHITE}" {S}/>'),
    "scale": (f'<path d="M100 36 V164 M60 170 H140" stroke="{OUT}" stroke-width="10" stroke-linecap="round"/>'
              f'<path d="M34 64 H166" stroke="{GOLD}" stroke-width="10" stroke-linecap="round"/>'
              f'<path d="M34 64 L14 116 H54 Z M166 64 L146 116 H186 Z" fill="{BLUE_L}" {S}/>'
              f'<circle cx="100" cy="36" r="12" fill="{GOLD}" {S}/>'),
    "megaphone": (f'<path d="M40 82 L130 40 V160 L40 118 Z" fill="{RED}" {S}/>'
                  f'<rect x="20" y="78" width="30" height="44" rx="8" fill="{WHITE}" {S}/>'
                  f'<path d="M60 120 L72 166 H92 L84 128" fill="{WHITE}" {S}/>'
                  f'<path d="M150 74 Q166 100 150 126 M164 60 Q188 100 164 140" fill="none" stroke="{GOLD}" '
                  f'stroke-width="8" stroke-linecap="round"/>'),
    "document": (f'<path d="M44 18 H128 L160 50 V182 H44 Z" fill="{WHITE}" {S}/>'
                 f'<path d="M128 18 V50 H160" fill="#D6E2F5" {S}/>'
                 f'<path d="M64 80 H140 M64 106 H140 M64 132 H120 M64 158 H104" stroke="{BLUE_L}" stroke-width="9" '
                 f'stroke-linecap="round"/>'),
    "building": (f'<path d="M100 18 L184 62 H16 Z" fill="{GOLD}" {S}/>'
                 f'<rect x="24" y="62" width="152" height="16" fill="{WHITE}" {S}/>'
                 + "".join(f'<rect x="{x}" y="84" width="20" height="74" fill="{WHITE}" {S}/>'
                           for x in (36, 76, 116, 150))
                 + f'<rect x="16" y="160" width="168" height="22" rx="4" fill="{BLUE_L}" {S}/>'),
    "lightbulb": (f'<path d="M100 26 C142 26 166 58 160 94 C156 120 136 132 132 152 H68 C64 132 44 120 40 94 '
                  f'C34 58 58 26 100 26 Z" fill="{GOLD}" {S}/>'
                  f'<rect x="70" y="152" width="60" height="30" rx="8" fill="{BLUE_L}" {S}/>'
                  f'<path d="M84 96 L100 120 L116 96" fill="none" stroke="{OUT}" stroke-width="6" stroke-linecap="round"/>'
                  f'<path d="M72 56 Q84 44 100 42" fill="none" stroke="{WHITE}" stroke-width="8" stroke-linecap="round"/>'),
    "wok": (f'<path d="M14 92 H186 C182 150 146 176 100 176 C54 176 18 150 14 92 Z" fill="{NAVY}" {S}/>'
            f'<path d="M186 96 L196 84" stroke="{OUT}" stroke-width="12" stroke-linecap="round"/>'
            f'<ellipse cx="66" cy="88" rx="30" ry="16" fill="{GOLD_D}" {S}/>'
            f'<rect x="96" y="66" width="56" height="28" rx="10" fill="{GOLD}" {S}/>'
            f'<path d="M60 52 Q52 36 62 22 M100 46 Q92 30 102 16 M140 52 Q132 36 142 22" fill="none" '
            f'stroke="{BLUE_L}" stroke-width="6" stroke-linecap="round"/>'),
    "rocket": (f'<path d="M100 14 C134 40 146 86 136 136 H64 C54 86 66 40 100 14 Z" fill="{WHITE}" {S}/>'
               f'<circle cx="100" cy="76" r="18" fill="{BLUE_L}" {S}/>'
               f'<path d="M64 108 L36 150 L66 140 Z M136 108 L164 150 L134 140 Z" fill="{RED}" {S}/>'
               f'<path d="M76 138 Q100 196 124 138 Z" fill="{GOLD}" {S}/>'),
    "shield": (f'<path d="M100 16 L168 42 V96 C168 140 136 170 100 184 C64 170 32 140 32 96 V42 Z" fill="{BLUE}" {S}/>'
               f'<path d="M68 100 L92 124 L136 76" fill="none" stroke="{GREEN}" stroke-width="14" '
               f'stroke-linecap="round" stroke-linejoin="round"/>'),
    "calendar": (f'<rect x="24" y="36" width="152" height="144" rx="16" fill="{WHITE}" {S}/>'
                 f'<path d="M24 52 Q24 36 40 36 H160 Q176 36 176 52 V76 H24 Z" fill="{RED}" {S}/>'
                 f'<path d="M64 22 V50 M136 22 V50" stroke="{OUT}" stroke-width="10" stroke-linecap="round"/>'
                 + "".join(f'<rect x="{x}" y="{y}" width="22" height="20" rx="4" fill="{c}"/>'
                           for x, y, c in ((48, 96, BLUE_L), (89, 96, BLUE_L), (130, 96, GOLD),
                                           (48, 134, BLUE_L), (89, 134, BLUE_L), (130, 134, BLUE_L)))),
    "target": (f'<circle cx="100" cy="100" r="78" fill="{WHITE}" {S}/>'
               f'<circle cx="100" cy="100" r="52" fill="{RED}" {S}/>'
               f'<circle cx="100" cy="100" r="24" fill="{WHITE}" {S}/>'
               f'<path d="M100 100 L170 30" stroke="{OUT}" stroke-width="8" stroke-linecap="round"/>'
               f'<path d="M150 30 H172 V52" fill="none" stroke="{GOLD}" stroke-width="10" stroke-linecap="round"/>'),
    "fire": (f'<path d="M100 14 C110 54 152 70 152 122 C152 158 128 184 100 184 C72 184 48 158 48 122 '
             f'C48 92 66 74 76 56 C80 78 88 86 96 90 C96 64 92 40 100 14 Z" fill="{RED}" {S}/>'
             f'<path d="M100 96 C106 118 126 128 126 148 C126 166 114 176 100 176 C86 176 74 166 74 148 '
             f'C74 132 86 124 92 112 C96 122 100 124 100 96 Z" fill="{GOLD}"/>'),
    "crowd": "".join(f'<circle cx="{x}" cy="{y}" r="22" fill="{c}" {S}/>'
                     f'<path d="M{x - 34} {y + 76} C{x - 34} {y + 34} {x + 34} {y + 34} {x + 34} {y + 76} Z" fill="{c}" {S}/>'
                     for x, y, c in ((52, 70, BLUE_L), (148, 70, BLUE_L), (100, 92, WHITE))),
    "arrow_up": (f'<path d="M100 18 L172 96 H128 V182 H72 V96 H28 Z" fill="{GREEN}" {S}/>'),
    "arrow_down": (f'<path d="M100 182 L172 104 H128 V18 H72 V104 H28 Z" fill="{PINK}" {S}/>'),
    "lock": (f'<path d="M62 92 V64 C62 40 80 24 100 24 C120 24 138 40 138 64 V92" fill="none" stroke="{OUT}" '
             f'stroke-width="16"/>'
             f'<rect x="38" y="88" width="124" height="96" rx="16" fill="{GOLD}" {S}/>'
             f'<circle cx="100" cy="128" r="12" fill="{OUT}"/><path d="M100 132 V156" stroke="{OUT}" '
             f'stroke-width="10" stroke-linecap="round"/>'),
    "piggy": (f'<ellipse cx="100" cy="110" rx="78" ry="60" fill="{PINK}" {S}/>'
              f'<path d="M64 56 L74 30 L92 52" fill="{PINK}" {S}/>'
              f'<ellipse cx="170" cy="110" rx="16" ry="20" fill="#FFA3AE" {S}/>'
              f'<rect x="80" y="54" width="40" height="10" rx="5" fill="{OUT}"/>'
              f'<circle cx="130" cy="94" r="7" fill="{OUT}"/>'
              f'<path d="M50 160 V184 M144 160 V184" stroke="{OUT}" stroke-width="16" stroke-linecap="round"/>'),
    "hourglass": (f'<path d="M52 20 H148 M52 180 H148" stroke="{OUT}" stroke-width="12" stroke-linecap="round"/>'
                  f'<path d="M62 24 C62 76 100 86 100 100 C100 114 62 124 62 176 H138 C138 124 100 114 100 100 '
                  f'C100 86 138 76 138 24 Z" fill="{WHITE}" {S}/>'
                  f'<path d="M78 160 Q100 132 122 160 Z M84 52 H116 L100 80 Z" fill="{GOLD}"/>'),
}

PROPS = tuple(sorted(_P))


def prop(name: str, cx: float, cy: float, size: float, rotate: float = 0) -> str:
    if name not in _P:
        raise ValueError(f"unknown prop {name!r}; available: {', '.join(PROPS)}")
    s = size / 200
    rot = f" rotate({rotate} 100 100)" if rotate else ""
    return (f'<g transform="translate({cx - size / 2:.1f},{cy - size / 2:.1f}) scale({s:.4f}){rot}">'
            f'{_P[name]}</g>')


def prop_svg(name: str, size: int = 200) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="{size}" height="{size}">'
            f'{_P[name]}</svg>')


# --- Small single-colour UI icons (24x24 grid) ---
_I = {
    "check": '<path d="M5 12.5 L10 17.5 L19 7" fill="none" stroke="{c}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>',
    "x": '<path d="M6 6 L18 18 M18 6 L6 18" stroke="{c}" stroke-width="3" stroke-linecap="round"/>',
    "bookmark": '<path d="M6 3 H18 V21 L12 16.5 L6 21 Z" fill="{c}"/>',
    "share": '<path d="M4 12 L20 4 L14 20 L11 13 Z" fill="{c}"/>',
    "link": '<path d="M10 14 L14 10 M8.5 16.5 L6.5 18.5 A3 3 0 0 1 2.5 14.5 L6 11 M15.5 7.5 L17.5 5.5 A3 3 0 0 1 21.5 9.5 L18 13" fill="none" stroke="{c}" stroke-width="2.6" stroke-linecap="round"/>',
    "arrow_right": '<path d="M4 12 H19 M13 6 L19 12 L13 18" fill="none" stroke="{c}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>',
    "telegram": '<path d="M3 11.5 L20 4.5 L17 19.5 L11.5 15.5 L9 18 L9.2 14 L17 7.5 L7.8 13 Z" fill="{c}"/>',
    "play": '<path d="M7 4.5 L19 12 L7 19.5 Z" fill="{c}"/>',
}


def icon(name: str, x: float, y: float, size: float, color: str = WHITE) -> str:
    s = size / 24
    return f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.3f})">{_I[name].format(c=color)}</g>'
