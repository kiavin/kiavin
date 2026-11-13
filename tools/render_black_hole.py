#!/usr/bin/env python3
"""Render a thin disk by tracing Kerr null geodesics; see assets/BLACK_HOLE.md.

Requires numpy, scipy and Pillow. Units: G=M=c=1. The inverse radial
coordinate and mu=cos(theta) remove radial-infinity and polar-axis issues.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]


def isco(a):
    z1 = 1 + np.cbrt(1 - a*a) * (np.cbrt(1+a) + np.cbrt(1-a))
    z2 = np.sqrt(3*a*a + z1*z1)
    return 3 + z2 - np.sqrt((3-z1)*(3+z1+2*z2))


def trace(alpha, beta, a=.998, inclination=82, step=.002, disk=True):
    """Past-directed rays from a distant observer; first opaque disk hit wins.

    lambda=-alpha*sin(i), eta=beta^2+(alpha^2-a^2)*cos(i)^2.
    Integrate u, u', mu, mu', phi in Mino time with RK4. E and L here
    refer to the future-directed photon; phi' therefore has a minus sign.
    """
    shape = alpha.shape
    alpha, beta = alpha.ravel(), beta.ravel()
    inc = np.deg2rad(inclination)
    ell = -alpha*np.sin(inc)
    q = beta*beta + (alpha*alpha-a*a)*np.cos(inc)**2
    aa = a*a - ell*ell - q
    bb = (ell-a)**2 + q
    horizon = 1 + np.sqrt(1-a*a)
    inner = isco(a)
    u = np.full_like(alpha, 1.e-4)
    v = np.sqrt(1 + aa*u*u + 2*bb*u**3 - a*a*q*u**4)
    mu = np.full_like(alpha, np.cos(inc))
    w = beta*np.sin(inc)
    phi = np.zeros_like(alpha)
    active = np.arange(len(alpha))
    status = np.zeros(len(alpha), dtype=np.uint8)  # 1 disk; 2 captured; 3 escaped
    hit_r = np.zeros_like(alpha)
    hit_phi = np.zeros_like(alpha)
    max_radial_error = 0.
    max_polar_error = 0.

    def derivative(s, aa_, bb_, q_, ell_):
        u_, v_, mu_, w_, phi_ = s
        den = np.maximum(1-2*u_+a*a*u_*u_, 1.e-6)
        return np.array([
            v_, aa_*u_+3*bb_*u_*u_-2*a*a*q_*u_**3,
            w_, aa_*mu_-2*a*a*mu_**3,
            -ell_/np.maximum(1-mu_*mu_, 1.e-9)-a*(2*u_-a*ell_*u_*u_)/den,
        ])

    for iteration in range(6000):
        if not len(active):
            break
        j = active
        old = np.array([u[j], v[j], mu[j], w[j], phi[j]])
        ar = (aa[j], bb[j], q[j], ell[j])
        k1 = derivative(old, *ar)
        k2 = derivative(old+step*k1/2, *ar)
        k3 = derivative(old+step*k2/2, *ar)
        k4 = derivative(old+step*k3, *ar)
        new = old + step*(k1+2*k2+2*k3+k4)/6
        u[j], v[j], mu[j], w[j], phi[j] = new
        # Crossing interpolation gives a disk surface without a step-sized band.
        crosses = old[2]*new[2] < 0
        fraction = np.divide(old[2], old[2]-new[2], out=np.zeros(len(j)), where=crosses)
        u_cross = old[0] + fraction*(new[0]-old[0])
        r_cross = 1/np.maximum(u_cross, 1.e-10)
        hits = crosses & (r_cross >= inner) & (r_cross <= 20) & disk
        status[j[hits]] = 1
        hit_r[j[hits]] = r_cross[hits]
        hit_phi[j[hits]] = (old[4]+fraction*(new[4]-old[4]))[hits]
        captured = (u[j] >= 1/(horizon+.003)) & ~hits
        escaped = (u[j] <= 1.e-4) & (v[j] < 0) & ~hits
        status[j[captured]] = 2
        status[j[escaped]] = 3
        if iteration % 25 == 0:
            safe = ~(hits | captured | escaped)
            f = 1 + aa[j]*u[j]**2 + 2*bb[j]*u[j]**3 - a*a*q[j]*u[j]**4
            h = q[j] + aa[j]*mu[j]**2-a*a*mu[j]**4
            if safe.any():
                max_radial_error = max(max_radial_error, float(np.max((np.abs(v[j]**2-f)/(1+np.abs(f)))[safe])))
                max_polar_error = max(max_polar_error, float(np.max((np.abs(w[j]**2-h)/(1+np.abs(q[j])))[safe])))
        active = j[~(hits | captured | escaped)]
    return dict(shape=shape, status=status, radius=hit_r, azimuth=hit_phi,
                ell=ell, mu=mu, phi=phi,
                radial_error=max_radial_error, polar_error=max_polar_error,
                unresolved=int(len(active)))


def spectrum(temperature):
    """Three visible Planck samples, exposure-normalized, in a display RGB approximation."""
    waves = np.array([650., 530., 450.])*1.e-9
    x = .01438776877 / (np.maximum(temperature[:, None], 100)*waves)
    radiance = (550.e-9/waves)**5 / np.expm1(np.minimum(x, 80))
    # Normalizing a solar-temperature spectrum to display white is presentation,
    # not a physical change to the traced photon-frequency shifts.
    white = (550.e-9/waves)**5 / np.expm1(.01438776877/(6500*waves))
    return radiance/white


def render(width, step):
    height = round(width*380/540)
    xs = (np.arange(width)+.5)/width*40-20
    ys = (0.5-(np.arange(height)+.5)/height)*40*height/width
    alpha, beta = np.meshgrid(xs, ys)
    traced = trace(alpha, beta, step=step)
    print('Traced', width, height, 'unresolved', traced['unresolved'], flush=True)
    n = width*height
    rgb = np.zeros((n, 3))
    disk = traced['status'] == 1
    r, ph, ell = (traced[k][disk] for k in ['radius', 'azimuth', 'ell'])
    a = .998
    omega = 1/(r**1.5+a)
    ut = (r**1.5+a)/np.sqrt(r**3-3*r*r+2*a*r**1.5)
    g = 1/(ut*(1-omega*ell))
    # A zero-torque Newtonian thin-disk temperature law. Kerr transport remains
    # relativistic; the emissivity is deliberately not claimed as Novikov-Thorne.
    thermal = (isco(a)/r)**3 * np.maximum(1-np.sqrt(isco(a)/r), 0)
    peak = (6/7)**6/7
    temperature = 14000*np.maximum(thermal/peak, 0)**.25
    # Modest deterministic texture: an illustrative snapshot, not GRMHD output.
    texture = 1 + .10*np.sin(38*np.log(r)+4*ph) + .07*np.sin(91*np.log(r)-7*ph)
    rgb[disk] = spectrum(temperature*g)*texture[:, None]
    # Rays that escape sample a deterministic celestial star field. Its image is
    # lensed by the same geodesics, rather than drawing an arbitrary glowing ring.
    escape = traced['status'] == 3
    rng = np.random.default_rng(41)
    star_mu = rng.uniform(-1, 1, 5000)
    star_phi = rng.uniform(-np.pi, np.pi, 5000)
    stars = np.column_stack([np.sqrt(1-star_mu**2)*np.cos(star_phi),
                             np.sqrt(1-star_mu**2)*np.sin(star_phi), star_mu])
    m = np.clip(traced['mu'][escape], -1, 1)
    p = traced['phi'][escape]
    directions = np.column_stack([np.sqrt(1-m*m)*np.cos(p), np.sqrt(1-m*m)*np.sin(p), m])
    distances, indices = cKDTree(stars).query(directions)
    intensity = np.exp(-(distances/.0008)**2)*rng.uniform(.002, .025, 5000)[indices]
    rgb[escape] = intensity[:, None]*np.array([.75, .92, 1.])
    # Reinhard exposure and approximate display gamma; restrained optical bloom
    # is a camera effect and is kept separate from the physics of the disk.
    exposure = .72
    mapped = np.maximum(exposure*rgb, 0)
    mapped = mapped/(1+mapped)
    pixels = (np.clip(mapped, 0, 1)**(1/2.2)*255).astype(np.uint8).reshape(height, width, 3)
    im = Image.fromarray(pixels)
    glow = np.asarray(im.filter(ImageFilter.GaussianBlur(width/270)), dtype=float)*.22
    pixels = np.clip(pixels.astype(float)+glow, 0, 255).astype(np.uint8)
    rgba = np.dstack([pixels, np.full((height, width), 255, dtype=np.uint8)])
    # Match the page's dark field outside emitting pixels. Captured rays stay
    # black; the shadow is not a flat decorative circle or the horizon itself.
    background = np.array([7, 17, 13], dtype=float)
    empty = (traced['status'].reshape(height, width) == 3)
    rgba[empty, :3] = np.maximum(rgba[empty, :3], background).astype(np.uint8)
    # Soft rectangular boundary for compositing with the vector terminal grid.
    yy, xx = np.mgrid[:height, :width]
    edge = np.minimum.reduce([xx/(width*.07), (width-1-xx)/(width*.07), yy/(height*.06), (height-1-yy)/(height*.06)])
    rgba[:, :, 3] = (np.clip(edge, 0, 1)*255).astype(np.uint8)
    result = Image.fromarray(rgba)
    report = {k: traced[k] for k in ['radial_error', 'polar_error', 'unresolved']}
    report.update(width=width, height=height, spin=a, inclination=82,
                  horizon_rg=float(1+np.sqrt(1-a*a)), isco_rg=float(isco(a)),
                  min_redshift=float(g.min()), max_redshift=float(g.max()),
                  disk_pixels=int(disk.sum()), step=step)
    visibility = np.where(traced['status'].reshape(height, width) == 2, 0, 255).astype(np.uint8)
    return result, report, Image.fromarray(visibility)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--width', type=int, default=1080)
    parser.add_argument('--step', type=float, default=.002)
    parser.add_argument('--output', type=Path, default=ROOT/'assets/black-hole.png')
    args = parser.parse_args()
    image, report, visibility = render(args.width, args.step)
    image.save(args.output, optimize=True)
    visibility.save(args.output.with_name(args.output.stem+'-mask.png'), optimize=True)
    args.output.with_suffix('.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
