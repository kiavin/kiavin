#!/usr/bin/env python3
"""Compose the self-contained GitHub SVG with a rendered Kerr disk and SVG text."""
import base64
import math
from pathlib import Path
from xml.sax.saxutils import escape
from cinematic_type import build as build_cinematic_type

ROOT = Path(__file__).resolve().parents[1]


def spiral(phase, height, radius=218):
    points = []
    for k in range(161):
        t = k/160
        r = radius*math.exp(-1.15*t)
        angle = phase + 3.8*math.pi*t
        x = 940+r*math.cos(angle)
        y = 218+.16*r*math.sin(angle)+height*(1-t)**3
        points.append(f'{"M" if k == 0 else "L"}{x:.2f},{y:.2f}')
    return ' '.join(points)


def main():
    png = base64.b64encode((ROOT/'assets/black-hole.png').read_bytes()).decode()
    mask = base64.b64encode((ROOT/'assets/black-hole-mask.png').read_bytes()).decode()
    type_defs, type_css, type_layers = build_cinematic_type()
    skills = [
        ('VUE 3', 1.9, -135, 746, 82),
        ('PHP / YII2', -.65, -108, 1098, 87),
        ('NUXT', 2.65, -60, 723, 147),
        ('DOCKER', .4, 100, 1110, 344),
        ('PYTHON', 2.1, 125, 793, 350),
        ('POSTGRESQL', -.15, 135, 1000, 375),
        ('GIT / CI', 3.5, 70, 738, 298),
        ('LINUX', .8, -100, 1140, 138),
    ]
    motion_css, animated, static, trails = [], [], [], []
    for k, (label, phase, height, sx, sy) in enumerate(skills):
        path = spiral(phase, height, radius=200 if len(label)>8 else 218)
        motion_css.append(f'.skill-{k} {{ offset-path:path("{path}"); animation-delay:-{k*2.73:.2f}s; animation-duration:{18+k*.8:.1f}s; }}')
        animated.append(f'<text class="infall skill-{k}" text-anchor="middle" dominant-baseline="middle">{escape(label)}</text>')
        static.append(f'<text x="{sx}" y="{sy}" text-anchor="middle">{escape(label)}</text>')
        if k in [0, 3, 4]:
            trails.append(f'<path d="{path}"/>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="420" viewBox="0 0 1200 420" role="img" aria-labelledby="title desc">
  <title id="title">Kelvin — a name caught in the gravity of a black hole</title>
  <desc id="desc">The KELVIN title stretches into luminous filaments toward a relativistically ray-traced Kerr black hole. Letter contours echo, deform and shed fragments into the accretion flow. Green skills orbit inward. These cinematic typography effects are artistic; the disk is numerically ray traced.</desc>
  <style>
    .infall {{ offset-distance:0%; offset-rotate:0deg; opacity:0; }}
    .animated-skills {{ display:none; }}
    @media (prefers-reduced-motion: no-preference) {{
      .animated-skills {{ display:block; }}
      .static-skills {{ display:none; }}
      .infall {{ animation-name:accrete; animation-timing-function:linear; animation-iteration-count:infinite; }}
    }}
    @keyframes accrete {{
      0% {{ offset-distance:0%; opacity:0; transform:scale(1); fill:#64ffb2; }}
      9% {{ opacity:.95; }}
      54% {{ opacity:.9; fill:#a9ffcc; }}
      78% {{ opacity:.65; fill:#ffd2a0; transform:scale(.85,.72); }}
      96% {{ opacity:0; fill:#a54024; transform:scale(.48,.25); }}
      100% {{ offset-distance:100%; opacity:0; transform:scale(.45,.2); }}
    }}
    {''.join(motion_css)}
    {type_css}
  </style>
  <defs>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#15392c" stroke-width="1"/></pattern>
    <linearGradient id="grid-fade"><stop stop-color="#07110d" stop-opacity=".92"/><stop offset=".55" stop-color="#07110d" stop-opacity=".8"/><stop offset="1" stop-color="#07110d" stop-opacity="0"/></linearGradient>
    <clipPath id="art-field"><path d="M685 30h493v360H685z"/></clipPath>
    <mask id="shadow-occlusion" maskUnits="userSpaceOnUse" x="0" y="0" width="1200" height="420"><path d="M0 0h1200v420H0z" fill="white"/><image x="660" y="28" width="540" height="380" href="data:image/png;base64,{mask}"/></mask>
    {type_defs}
  </defs>
  <path fill="#07110d" d="M0 0h1200v420H0z"/>
  <path fill="url(#grid)" opacity=".5" d="M0 0h1200v420H0z"/>
  <path fill="url(#grid-fade)" d="M0 0h1200v420H0z"/>
  <image x="660" y="28" width="540" height="380" href="data:image/png;base64,{png}"/>
  {type_layers}
  <g clip-path="url(#art-field)" mask="url(#shadow-occlusion)">
    <g fill="none" stroke="#64ffb2" stroke-width=".65" stroke-dasharray="1 12" opacity=".16">{''.join(trails)}</g>
    <g class="static-skills" font-family="'Courier New',monospace" font-size="14" letter-spacing="1" fill="#8fffc0">{''.join(static)}</g>
    <g class="animated-skills" font-family="'Courier New',monospace" font-size="14" letter-spacing="1">{''.join(animated)}</g>
  </g>
  <g font-family="'Courier New',monospace">
    <text x="60" y="64" fill="#64ffb2" font-size="16" letter-spacing="5">KIAVIN / SYSTEM ONLINE</text>
    <text x="60" y="289" fill="#a6d6bc" font-size="25" letter-spacing="1">FULL-STACK / DEVOPS / AUTOMATION</text>
    <path d="M60 316h50" stroke="#64ffb2" stroke-width="2"/>
    <text x="60" y="348" fill="#8bb39c" font-size="20">Build useful things. Make the system work.</text>
    <text x="60" y="386" fill="#5d9476" font-size="13" letter-spacing="2">INTERFACE → API → DATA → DELIVERY</text>
  </g>
  <g fill="none" stroke="#64ffb2" stroke-width="2"><path d="M18 48V18h30m1104 0h30v30M18 372v30h30m1104 0h30v-30"/></g>
  <path d="M60 17h1080M60 403h1080" stroke="#1e4231"/>
</svg>
'''
    svg = '\n'.join(line.rstrip() for line in svg.splitlines())+'\n'
    (ROOT/'assets/hero.svg').write_text(svg)
    print('Built self-contained SVG:', len(svg.encode()), 'bytes')


if __name__ == '__main__':
    main()
