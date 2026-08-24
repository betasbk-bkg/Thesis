#!/usr/bin/env python3
"""s1_vstar.py - Optimal speed v* per condition (Supplementary Table S1).

Primary estimator: the empirical minimum of RMSE over the tested speed grid.
This estimator is applied uniformly to both trajectories and to the delay sweep
(Supplementary Table S5), and it is defined whether or not an interior optimum
exists.

Secondary check (circle only): the vertex of a fitted parabola,
RMSE(v) = a0 + a1*v + a2*v^2, v_vertex = -a1/(2*a2). On the square the fitted
vertex falls far outside the tested interval, because RMSE increases
monotonically over 1.0-5.0 m/s; the square optimum is therefore reported as a
lower-bound censored value (v* <= 1.0 m/s) rather than as a fitted vertex.

Input : data/E2_proper_results.json
Output: data/s1_vstar.json
"""
import json
import numpy as np

SPEEDS = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
TROLLS = ['0.05', '0.10', '0.15', '0.20', '0.30', '0.40']
R = json.load(open('data/E2_proper_results.json'))['results']

out = {'estimator': 'empirical minimum on the tested speed grid (1.0-5.0 m/s, 0.5 m/s spacing below 4.0)',
       'rows': []}
for traj in ['circle', 'square']:
    for tr in TROLLS:
        v = np.array(SPEEDS, dtype=float)
        y = np.array([R[f'{traj}_tr{tr}_v{s}']['rmse_mean'] for s in SPEEDS])
        i = int(np.argmin(y))
        a2, a1, a0 = np.polyfit(v, y, 2)
        pred = np.polyval([a2, a1, a0], v)
        r2 = 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
        vertex = float(-a1 / (2 * a2))
        interior = v[0] < vertex < v[-1]
        out['rows'].append({
            'trajectory': traj,
            'adversarial': f'{float(tr) * 100:.0f}%',
            'v_star_grid': float(v[i]),
            'rmse_at_v_star': round(float(y[i]), 4),
            'boundary_censored': bool(i == 0),
            'parabola_vertex': round(vertex, 3),
            'parabola_r2': round(float(r2), 3),
            'vertex_inside_tested_range': bool(interior),
        })

cg = [r['v_star_grid'] for r in out['rows'] if r['trajectory'] == 'circle']
sg = [r['v_star_grid'] for r in out['rows'] if r['trajectory'] == 'square']
cv = [r['parabola_vertex'] for r in out['rows'] if r['trajectory'] == 'circle']
out['summary'] = {
    'circle_grid_min_unique': sorted(set(cg)),
    'circle_grid_min_identical_across_ratios': len(set(cg)) == 1,
    'square_grid_min_unique': sorted(set(sg)),
    'square_all_at_lower_bound': all(x == min(SPEEDS) for x in sg),
    'circle_vertex_mean': round(float(np.mean(cv)), 3),
    'circle_vertex_sd': round(float(np.std(cv, ddof=1)), 3),
    'circle_vertex_range': [round(min(cv), 3), round(max(cv), 3)],
    'square_vertex_all_outside_tested_range': all(
        not r['vertex_inside_tested_range'] for r in out['rows'] if r['trajectory'] == 'square'),
}
json.dump(out, open('data/s1_vstar.json', 'w'), indent=1)
for r in out['rows']:
    print(f"{r['trajectory']:7s} {r['adversarial']:>4s}  v*(grid)={r['v_star_grid']:.1f}  "
          f"RMSE={r['rmse_at_v_star']:.4f}  vertex={r['parabola_vertex']:>8.3f} "
          f"(R2={r['parabola_r2']:.3f}, interior={r['vertex_inside_tested_range']})")
print('\nsummary:', json.dumps(out['summary'], indent=1))
