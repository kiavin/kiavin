"""Original polygon lettering and cinematic tidal deformation for the SVG header.

This is an art-directed title effect, separate from the Kerr disk renderer.
All letter outlines are drawn here; no external fonts, scripts or assets load.
"""
import math
import random


GLYPHS = [
    ('K', 125, [(0,0),(29,0),(29,62),(86,0),(120,0),(54,78),(125,160),(89,160),(29,95),(29,160),(0,160)]),
    ('E', 112, [(0,0),(112,0),(112,28),(30,28),(30,65),(98,65),(98,93),(30,93),(30,132),(112,132),(112,160),(0,160)]),
    ('L', 108, [(0,0),(30,0),(30,132),(108,132),(108,160),(0,160)]),
    ('V', 135, [(0,0),(33,0),(68,119),(102,0),(135,0),(85,160),(50,160)]),
    ('I', 78, [(0,0),(78,0),(78,27),(54,27),(54,133),(78,133),(78,160),(0,160),(0,133),(24,133),(24,27),(0,27)]),
    ('N', 126, [(0,160),(0,0),(30,0),(96,111),(96,0),(126,0),(126,160),(96,160),(30,50),(30,160)]),
]


def outline(points, offset):
    """Subdivide straight edges so the nonlinear warp bends their contours."""
    samples = []
    for start, end in zip(points, points[1:]+points[:1]):
        count = max(1, math.ceil(math.dist(start,end)/5))
        for k in range(count):
            t = k/count
            samples.append((60+(offset+start[0]+(end[0]-start[0])*t)*.73,
                            108+(start[1]+(end[1]-start[1])*t)*.86))
    return samples


def deform(x, y, strength=1):
    t = max(0, min(1, (x-60)/547))
    pull = (.48+.17*(strength-1))*t*t
    return (x+145*strength*t**3 + 9*t*t*math.sin((y-110)/140*math.pi),
            y+(218-y)*pull + 10*t*math.sin(math.pi*t))


def path(points, strength):
    coords = [deform(x,y,strength) for x,y in points]
    return ' '.join(f'{"M" if i==0 else "L"}{x:.2f},{y:.2f}' for i,(x,y) in enumerate(coords))+' Z'


def build():
    defs, css = [], []
    offset = 0
    ids = []
    for k,(letter,width,points) in enumerate(GLYPHS):
        points = outline(points,offset)
        steady, peak = path(points,1.3), path(points,1.9)
        identity = f'tidal-{k}'
        ids.append(identity)
        defs.append(f'<path id="{identity}" class="tidal-letter letter-{k}" d="{steady}"/>')
        css.append(f'''@keyframes tide-{k} {{
          0%,100% {{ d:path("{steady}"); }}
          44%,58% {{ d:path("{peak}"); }}
        }}
        @media (prefers-reduced-motion:no-preference) {{
          .letter-{k} {{ animation:tide-{k} 20s cubic-bezier(.35,0,.25,1) {-7-k*.16:.2f}s infinite; }}
        }}''')
        offset += width+13

    def word(attributes):
        return '<g '+attributes+'>'+''.join(f'<use href="#{i}"/>' for i in ids)+'</g>'

    defs.append('<clipPath id="title-face">'+''.join(f'<use href="#{i}"/>' for i in ids)+'</clipPath>')

    # Contour echoes are stretched toward the disk, never a second solid word.
    echoes = []
    for k in range(1,7):
        sx = 1+k*.027
        sy = 1-k*.023
        echoes.append(word(f'transform="translate({k*4:.1f} {218*(1-sy):.2f}) scale({sx:.3f} {sy:.3f})" fill="none" stroke="url(#echo-spectrum)" stroke-width=".8" opacity="{.18/(1+k*.3):.3f}"'))

    # Light streamlines bridge the title and the luminous approaching disk.
    rng = random.Random(79)
    streams, chips_css, chips = [], [], []
    for k in range(47):
        x = rng.uniform(405,690)
        y = rng.uniform(126,245)
        start_x, start_y = deform(x,y,1.22)
        target_y = 216+rng.uniform(-8,8)
        # Bow out above/below the word before falling into the projected disk.
        curve = (y-200)*1.25
        d = f'M{start_x:.2f},{start_y:.2f} C{start_x+100:.2f},{start_y+curve:.2f} 816,{target_y+curve*.45:.2f} 927,{target_y:.2f}'
        streams.append(f'<path d="{d}" stroke-width="{rng.uniform(.35,1.1):.2f}" opacity="{rng.uniform(.07,.25):.2f}"/>')
        if k%3==0:
            duration = rng.uniform(7,12)
            delay = -rng.uniform(0,duration)
            chips_css.append(f'.shard-{k} {{ offset-path:path("{d}"); animation-duration:{duration:.2f}s; animation-delay:{delay:.2f}s; }}')
            chips.append(f'<path class="type-shard shard-{k}" d="M-6,-1.1H3L7,0L3,1.1H-6Z"/>')

    # An intentionally warped drafting grid connects the once-independent halves.
    grid = []
    for y in [92,119,146,173,200,227,254]:
        points=[]
        for x in range(48,965,8):
            r=math.hypot(950-x,218-y)
            pull=min(.72, 27000/(r*r+25000))
            px=x+(950-x)*pull*.25
            py=y+(218-y)*pull
            points.append((px,py))
        grid.append(' '.join(f'{"M" if i==0 else "L"}{x:.1f},{v:.1f}' for i,(x,v) in enumerate(points)))
    for x in range(70,870,45):
        points=[]
        for y in range(90,266,6):
            r=math.hypot(950-x,218-y)
            pull=min(.72,27000/(r*r+25000))
            points.append((x+(950-x)*pull*.25, y+(218-y)*pull))
        grid.append(' '.join(f'{"M" if i==0 else "L"}{x:.1f},{v:.1f}' for i,(x,v) in enumerate(points)))

    defs.extend(['''
      <linearGradient id="title-spectrum" gradientUnits="userSpaceOnUse" x1="60" y1="130" x2="900" y2="218">
        <stop stop-color="#effff8"/><stop offset=".45" stop-color="#d9ffef"/><stop offset=".68" stop-color="#79ffc1"/><stop offset=".86" stop-color="#fff0cd"/><stop offset="1" stop-color="#c47740"/>
      </linearGradient>
      <linearGradient id="echo-spectrum" gradientUnits="userSpaceOnUse" x1="90" y1="150" x2="930" y2="218">
        <stop stop-color="#70ffbf" stop-opacity="0"/><stop offset=".32" stop-color="#70ffbf"/><stop offset=".7" stop-color="#bdffde"/><stop offset="1" stop-color="#ffcb96"/>
      </linearGradient>
      <linearGradient id="filament-spectrum" gradientUnits="userSpaceOnUse" x1="400" y1="160" x2="940" y2="218">
        <stop stop-color="#63ffa9" stop-opacity="0"/><stop offset=".3" stop-color="#8affc4"/><stop offset=".7" stop-color="#e8ffe7"/><stop offset="1" stop-color="#ffd3a1"/>
      </linearGradient>
      <linearGradient id="surface-engraving" gradientUnits="userSpaceOnUse" x1="60" y1="0" x2="880" y2="0"><stop stop-color="#073021" stop-opacity=".02"/><stop offset=".6" stop-color="#073021" stop-opacity=".06"/><stop offset="1" stop-color="#073021" stop-opacity=".28"/></linearGradient>
      <radialGradient id="cinema-flare"><stop stop-color="#fffbe2" stop-opacity=".8"/><stop offset=".2" stop-color="#d8ffd5" stop-opacity=".32"/><stop offset="1" stop-color="#6dffa9" stop-opacity="0"/></radialGradient>
      <filter id="title-bloom" x="-15%" y="-70%" width="150%" height="240%" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="5"/></filter>
      <filter id="stream-bloom" x="-20%" y="-80%" width="150%" height="260%" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="2"/></filter>
      <clipPath id="title-field"><path d="M40 88H947V267H40Z"/></clipPath>
    '''])
    css.extend(chips_css)
    css.append('''
      .type-shard { offset-distance:28%; offset-rotate:auto; opacity:0; fill:#b8ffcf; }
      @media (prefers-reduced-motion:no-preference) {
        .type-shard { animation-name:shear-infall; animation-timing-function:linear; animation-iteration-count:infinite; }
        .title-streams { animation:stream-breathe 20s ease-in-out -7s infinite; }
      }
      @keyframes shear-infall {
        0% { offset-distance:0%; opacity:0; transform:scale(.4); fill:#78ffb6; }
        18% { opacity:.65; }
        64% { opacity:.85; fill:#e5ffe3; transform:scale(1.1,.7); }
        100% { offset-distance:100%; opacity:0; fill:#ffa76b; transform:scale(.25,.1); }
      }
      @keyframes stream-breathe { 0%,100% { opacity:.5; } 44%,58% { opacity:1; } }
    ''')
    grid_layer = '<g fill="none" stroke="#60dca0" stroke-width=".6" opacity=".09">'+''.join(f'<path d="{d}"/>' for d in grid)+'</g>'
    stream_layer = '<g class="title-streams" fill="none" stroke="url(#filament-spectrum)">'+''.join(streams)+'</g>'
    engraving = '<g clip-path="url(#title-face)" stroke="url(#surface-engraving)" stroke-width=".65">'+''.join(f'<path d="M54 {y}H930"/>' for y in range(110,249,3))+'</g>'
    layers = f'''<g clip-path="url(#title-field)" mask="url(#shadow-occlusion)" aria-label="KELVIN">
      {grid_layer}
      {''.join(echoes)}
      <ellipse cx="840" cy="216" rx="520" ry="7" fill="url(#cinema-flare)"/>
      {word('fill="url(#title-spectrum)" opacity=".28" filter="url(#title-bloom)"')}
      {word('transform="translate(2 3)" fill="#0b3528" stroke="#326e50" stroke-width=".7"')}
      {word('fill="url(#title-spectrum)" stroke="#eaffee" stroke-width=".45" stroke-opacity=".65"')}
      {engraving}
      <g filter="url(#stream-bloom)" opacity=".45">{stream_layer}</g>
      {stream_layer}
      {''.join(chips)}
    </g>'''
    return '\n'.join(defs), '\n'.join(css), layers
