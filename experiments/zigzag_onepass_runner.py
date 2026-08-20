#!/usr/bin/env python3
"""
zigzag_onepass_runner.py — Corrected zigzag benchmark (one-pass metric), full E3 rerun
======================================================================================
Companion runner for the one-pass zigzag benchmark.

Rationale: the zigzag path is an open polyline whose look-ahead target wraps to the
start upon completion while the error metric remains open-path; at V = 5 m/s the agent
completes one traversal in ~14–21 s and spends the remaining horizon trapped near the
terminal segments (occupancy check: 100% of late-half time in the last two of ten
segments). Tracking error for zigzag is therefore redefined as the RMSE over the FIRST
COMPLETE TRAVERSAL (frames until the projected arc first reaches L − 0.5 m), restoring
validity without altering the trajectory geometry. Closed paths are unaffected.

Runs: 6 adversarial ratios × 12 crowd sizes × MC 15 = 1,080 runs (fixed method, V = 5).
Seeds: deterministic, seed = i*31 + N (matching the archived e2f convention).
Output: zigzag_onepass_e2f.json (+ printed ceiling fits a + b/sqrt(N) per ratio).
Requires: simulation_main.py in the working directory (engine is NOT modified on disk;
the per-frame error/arc logging is injected at runtime).

Estimated runtime: 4-6 min.
The full-horizon values are retained in the archive for comparison.
"""
import json, time, types
import numpy as np

src = open('simulation_main.py', encoding='utf-8').read()
anchor = "        closest_point, _ = traj.closest(pos)"
assert anchor in src, "engine anchor not found — check simulation_main.py version"
src2 = ("_LOG = []\n" + src.replace(
    anchor,
    "        closest_point, _ca = traj.closest(pos)\n"
    "        _LOG.append((float(np.linalg.norm(pos - closest_point)), float(_ca)))", 1))
sm = types.ModuleType('sm_onepass'); exec(compile(src2, 'sm_onepass', 'exec'), sm.__dict__)
L = sm.Zigzag().circ

def one_pass_rmse(N, tr, seed, V=5.0):
    sm._LOG.clear()
    sm.simulate(sm.Zigzag(), N, tr, seed=seed, method='fixed', speed_override=V)
    arr = np.array(sm._LOG)
    done = np.where(arr[:, 1] >= L - 0.5)[0]
    cut = done[0] + 1 if len(done) else len(arr)   # no completion → full horizon (flagged)
    return float(np.sqrt((arr[:cut, 0] ** 2).mean())), bool(len(done))

Ns = [5, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200]
TRS = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40]
MC = 15

t0 = time.time(); out = {}; incomplete = 0
for tr in TRS:
    for N in Ns:
        vals = []
        for i in range(MC):
            v, done = one_pass_rmse(N, tr, seed=i * 31 + N)
            vals.append(v); incomplete += (not done)
        out[f"zigzag_tr{tr:.2f}_N{N}"] = {
            'rmse_mean': round(float(np.mean(vals)), 4),
            'rmse_std':  round(float(np.std(vals)), 4),
            'rmse': [round(v, 4) for v in vals],
        }
    print(f"tr={tr:.0%} done ({time.time()-t0:.0f}s)")
print(f"total {len(out)*MC} runs, incomplete-traversal runs: {incomplete} (expect 0 at V=5)")

print(f"\n{'tr':>5} {'a':>8} {'b':>8} {'N=5':>7} {'N=200':>7} {'attainable':>10}")
fits = {}
for tr in TRS:
    ys = np.array([out[f"zigzag_tr{tr:.2f}_N{N}"]['rmse_mean'] for N in Ns])
    A = np.vstack([np.ones(len(Ns)), 1 / np.sqrt(Ns)]).T
    (a, b), *_ = np.linalg.lstsq(A, ys, rcond=None)
    fits[f"{tr:.2f}"] = {'a': round(float(a), 4), 'b': round(float(b), 4)}
    att = (ys[0] - a) / ys[0] * 100
    print(f"{tr:>5.0%} {a:>8.3f} {b:>8.3f} {ys[0]:>7.3f} {ys[-1]:>7.3f} {att:>9.1f}%")

json.dump({'meta': {'metric': 'one-pass RMSE (first traversal, arc >= L-0.5)',
                    'seed': 'i*31+N', 'V': 5.0, 'MC': MC, 'metric': 'one-pass'},
           'results': out, 'ceiling_fits': fits},
          open('data/zigzag_onepass_e2f.json', 'w', encoding='utf-8'), indent=1)
print("\nsaved: zigzag_onepass_e2f.json")
