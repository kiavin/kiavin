#!/usr/bin/env python3
"""Analytic limits and resolution convergence checks for the header renderer."""
import numpy as np
from render_black_hole import isco, trace

assert abs(isco(0)-6) < 1.e-12
assert abs(isco(.998)-1.2369706551751842) < 1.e-12

# For Schwarzschild, b_critical = 3 sqrt(3). Rays inside are captured;
# rays outside escape. Use both signs to check reflection symmetry.
r = trace(np.array([5., 5.4, -5., -5.4]), np.zeros(4),
          a=0, inclination=90, disk=False)
assert list(r['status']) == [2, 3, 2, 3], r['status']

alpha, beta = np.meshgrid(np.linspace(-18, 18, 91), np.linspace(-12, 12, 61))
coarse = trace(alpha, beta, step=.002)
fine = trace(alpha, beta, step=.001)
same = coarse['status'] == fine['status']
hits = (coarse['status'] == 1) & (fine['status'] == 1)
radial = np.abs(coarse['radius'][hits]-fine['radius'][hits])/fine['radius'][hits]
angular = np.abs(np.angle(np.exp(1j*(coarse['azimuth'][hits]-fine['azimuth'][hits]))))
assert np.mean(same) > .998
assert np.quantile(radial, .99) < .002
assert np.quantile(angular, .99) < .03
assert fine['unresolved'] == 0
assert fine['radial_error'] < 1.e-6
assert fine['polar_error'] < 1.e-6
print('ISCO limits, Schwarzschild capture boundary, reflection symmetry and Kerr convergence passed.')
print(f'Same ray outcome: {np.mean(same):.4%}; p99 radius error: {np.quantile(radial,.99):.3g}; '
      f'p99 azimuth error: {np.quantile(angular,.99):.3g} rad.')
