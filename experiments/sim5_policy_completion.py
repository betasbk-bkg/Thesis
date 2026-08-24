#!/usr/bin/env python3
"""
sim5_policy_completion.py — Policy-completion analysis (fourth aggregation policy)
==================================================================================
The three deployed aggregation policies span
three of the four cells of a direction-rule × gain-law grid (vector-mean/majority ×
fixed/consensus-scaled). This script measures the missing cell — majority direction
with consensus-scaled (γ²V) gain — plus the three existing policies under identical
seeds. The four cells complete the direction-rule x gain-law grid. The main
experiment retains the three deployed policies as its factor levels; this grid is
a policy-completion measurement rather than a factorial main experiment.

Runs: 4 policies × 8 speeds × 3 adversarial ratios × MC 15 = 1,440 (circle, N = 150).
Engine is not modified on disk; the fourth policy branch is injected at runtime.
Output: sim5_2x2_results.json. Runtime ~2 min.
"""
import hashlib, json, time, types
import numpy as np

src = open('simulation_main.py', encoding='utf-8').read()
old = ("        elif method == 'quadratic':\n"
       "            target_vel = cur_dir * (cur_gamma ** 2) * V")
assert old in src, "engine anchor not found"
src2 = src.replace(old, old + "\n"
       "        elif method == 'maj_quad':\n"
       "            target_vel = maj_dir * (cur_gamma ** 2) * V")
sm = types.ModuleType('sm5'); exec(compile(src2, 'sm5', 'exec'), sm.__dict__)

SEEDS = 31; MC = 15
SPEEDS = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
TRS = [0.05, 0.20, 0.40]
POLICIES = ['fixed', 'majority', 'quadratic', 'maj_quad']
off = lambda tag: int(hashlib.md5(tag.encode()).hexdigest()[:6], 16) % 100000

t0 = time.time(); out = {}
for tr in TRS:
    for m in POLICIES:
        for v in SPEEDS:
            tag = f"S5_tr{tr}_{m}_v{v}"
            rs = [sm.simulate(sm.Circle(), 150, tr, seed=i * SEEDS + off(tag),
                              method=m, speed_override=v)['rmse'] for i in range(MC)]
            out[tag] = {'rmse_mean': round(float(np.mean(rs)), 5),
                        'rmse': [round(x, 5) for x in rs]}
    print(f"tr={tr:.0%} done ({time.time()-t0:.0f}s)")

print(f"\n{'tr':>5} | " + " | ".join(f"{m:>18}" for m in POLICIES) + "   [min RMSE @ v]")
for tr in TRS:
    row = f"{tr:>5.0%} |"
    for m in POLICIES:
        pts = [(v, out[f"S5_tr{tr}_{m}_v{v}"]['rmse_mean']) for v in SPEEDS]
        vm, rm = min(pts, key=lambda x: x[1])
        row += f"  {rm:.3f} @ {vm:>3.1f}      |"
    print(row)

json.dump(out, open('data/sim5_2x2_results.json', 'w', encoding='utf-8'), indent=1)
print("\nsaved: sim5_2x2_results.json")
