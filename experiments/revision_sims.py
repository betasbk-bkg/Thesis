#!/usr/bin/env python3
"""revision_sims.py — Sensitivity campaigns for Paper 1 (SIM-1 to SIM-4).

Run from the directory containing simulation_main.py and method_comparison_results.json:
    python3 revision_sims.py            # all campaigns (approx. 15-25 min)
    python3 revision_sims.py --only 1   # single campaign (1|2|3|4)

Output: revision_sims_results.json

SIM-1  state-observation delay tau      6 levels x 3 adversarial ratios x 10 speeds   8,100 runs
SIM-2  heading-noise scale   3 levels (k = 0.5, 1, 2) at tau baseline      1,080 runs
SIM-3  smoothing alpha       3 levels (0.1, 0.2, 0.3)                      1,080 runs
SIM-4  disruptor behavior   uniform / coherent-opposite / lagged          1,080 runs

Notes on the implementation this campaign varies:
  - The look-ahead distance LOOK = 2.0 m is held fixed at every tau; it is a
    system design parameter rather than an environment variable.
  - Participant heading noise is not a single Gaussian. gen_votes() draws a
    mixture within the non-adversarial population: accurate 70/95 (~73.7%, uniform +/-3 deg), delayed 20/95 (~21.1%, lagged heading),
    imprecise 5/95 (~5.3%, uniform +/-30 deg). SIM-2 therefore scales the actual noise
    widths by k rather than a nominal sigma:
    k in {0.5, 1, 2} -> (+/-1.5, +/-15) / (+/-3, +/-30) / (+/-6, +/-60) deg.
  - Smoothing alpha = 0.2 is the value used by the engine and reported in Methods.

Seeding: seed = i * 31 + offset, with offset a fixed per-condition hash, so every
run is reproducible.
"""

import argparse, hashlib, json, time
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import simulation_main as sm

# ------------------------------------------------------------------
# Shared configuration
# ------------------------------------------------------------------
MC        = 15
SEED_BASE = 31                      # matches the base run_condition seeding
N_FIXED   = 150
METHODS   = ['fixed', 'majority', 'quadratic']
SPEEDS_8  = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]      # main E1 speed grid
SPEEDS_10 = SPEEDS_8 + [6.5, 8.0]                          # extended for the optimum bracket; applied at every tau for a balanced design
TROLLS_3  = [0.05, 0.20, 0.40]
TAUS      = [0, 6, 13, 26, 39, 52]                          # frames (0–867 ms)

def cond_offset(tag: str) -> int:
    """Condition string -> deterministic seed offset (reproducible, independent across conditions)."""
    return int(hashlib.md5(tag.encode()).hexdigest()[:6], 16) % 100000

def run_mc(traj, troll, method, speed, tag):
    off = cond_offset(tag)
    out = [sm.simulate(traj, N_FIXED, troll, seed=i * SEED_BASE + off,
                       method=method, speed_override=speed) for i in range(MC)]
    return {
        'rmse':       [round(r['rmse'], 5) for r in out],
        'rmse_mean':  round(float(np.mean([r['rmse'] for r in out])), 5),
        'rmse_std':   round(float(np.std([r['rmse'] for r in out])), 5),
        'gamma_mean': round(float(np.mean([r['gamma_mean'] for r in out])), 4),
        'gamma_sq_mean': round(float(np.mean([r['gamma_mean']**2 + r['gamma_std']**2
                                              for r in out])), 4),  # mean squared consensus, used for the effective-speed mapping
        'speed_mean': round(float(np.mean([r['speed_mean'] for r in out])), 4),
        'seed_offset': off,
    }

def eta2_two_way(cell):
    """cell[(method, speed)] = [rmse per MC replicate] -> two-way ANOVA eta^2 (same df structure as Table 1)."""
    ms = sorted({k[0] for k in cell}); vs = sorted({k[1] for k in cell})
    allv = np.array([x for v in cell.values() for x in v]); gm = allv.mean()
    SS_T = ((allv - gm) ** 2).sum()
    SS_M = sum(len(vs) * MC * (np.mean([x for v in vs for x in cell[(m, v)]]) - gm) ** 2 for m in ms)
    SS_V = sum(len(ms) * MC * (np.mean([x for m in ms for x in cell[(m, v)]]) - gm) ** 2 for v in vs)
    SS_C = sum(MC * (np.mean(cell[(m, v)]) - gm) ** 2 for m in ms for v in vs)
    SS_I = SS_C - SS_M - SS_V
    return {'eta2_speed': round(SS_V / SS_T, 4), 'eta2_method': round(SS_M / SS_T, 4),
            'eta2_inter': round(SS_I / SS_T, 4),
            'ratio_speed_method': round((SS_V / SS_T) / max(SS_M / SS_T, 1e-12), 2)}

# ------------------------------------------------------------------
# Verification gate: spot-check reproduction of the archived E1 cells before running
# ------------------------------------------------------------------
def validation_gate():
    """Exact reproduction check against the archived E1 factorial.

    Uses the E1 seed formula of experiments/method_comparison.py
        seed = i*31 + int(v*100) + {fixed:1000, majority:2000, quadratic:3000}[method]
    so the recomputed run-level RMSE list must match the archive bit-exactly,
    not merely within Monte-Carlo tolerance.
    """
    print("=" * 60, "\n[GATE] exact reproduction of archived E1 cells")
    ref = json.load(open('data/method_comparison_results.json'))['raw_results']
    salt = {'fixed': 1000, 'majority': 2000, 'quadratic': 3000}
    checks = [('circle', 0.20, 'fixed', 2.0), ('circle', 0.20, 'quadratic', 3.5),
              ('circle', 0.05, 'majority', 2.0)]
    ok = True
    for traj_name, tr, m, v in checks:
        key = f"{traj_name}_tr{tr:.2f}_v{v}_{m}"
        if key not in ref:
            key = f"{traj_name}_tr{tr}_v{v}_{m}"
        stored = ref.get(key)
        if stored is None:
            print(f"  [warn] key not found: {key}"); ok = False; continue
        mine = [sm.simulate(sm.Circle(), N_FIXED, tr,
                            seed=i * 31 + int(v * 100) + salt[m],
                            method=m, speed_override=v)['rmse'] for i in range(MC)]
        theirs = stored['rmses']
        dmax = max(abs(a - b) for a, b in zip(mine, theirs))
        flag = "EXACT" if dmax <= 1e-6 else "MISMATCH"
        if flag != "EXACT":
            ok = False
        print(f"  {key}: run-level max|diff| = {dmax:.2e} [{flag}]")
    print(f"  [GATE] {'PASS - exact reproduction' if ok else 'FAIL - see mismatches above'}")
    print("=" * 60)
    return ok


# ------------------------------------------------------------------
# SIM-1: state-observation delay tau sensitivity
# ------------------------------------------------------------------
def sim1():
    print("\n[SIM-1] tau sensitivity: 6 tau x 3 methods x 10 speeds x 3 adversarial ratios x MC15 = 8,100 runs")
    res = {'config': {'taus': TAUS, 'speeds': SPEEDS_10, 'trolls': TROLLS_3,
                      'N': N_FIXED, 'MC': MC, 'traj': 'circle',
                      'note_LOOK': 'LOOK = 2.0 m held fixed at every tau (system design parameter)'},
           'results': {}, 'eta2': {}}
    t0 = time.time()
    orig_tau = sm.DELAY_F
    for tau in TAUS:
        sm.DELAY_F = tau
        for tr in TROLLS_3:
            cell = {}
            for m in METHODS:
                for v in SPEEDS_10:
                    tag = f"S1_tau{tau}_tr{tr}_{m}_v{v}"
                    r = run_mc(sm.Circle(), tr, m, v, tag)
                    res['results'][tag] = r
                    cell[(m, v)] = r['rmse']
            res['eta2'][f"tau{tau}_tr{tr}"] = eta2_two_way(cell)
            e = res['eta2'][f"tau{tau}_tr{tr}"]
            print(f"  τ={tau:2d} tr={tr:.2f}: η²_speed={e['eta2_speed']:.1%} "
                  f"η²_method={e['eta2_method']:.1%} ratio={e['ratio_speed_method']:.1f}x "
                  f"({time.time()-t0:.0f}s)")
    sm.DELAY_F = orig_tau
    return res

# ------------------------------------------------------------------
# SIM-2: heading-noise width scale k
# ------------------------------------------------------------------
def make_scaled_gen_votes(k, orig):
    """Scale the actual noise widths: accurate +/-3k deg, imprecise +/-30k deg. The delayed-subtype lag structure is unchanged."""
    def gv(ideal_angle, prev_angle, troll_ratio, N_agents, rng):
        n_troll = min(round(N_agents * troll_ratio), N_agents)
        remaining = N_agents - n_troll
        n_acc = round(remaining * 0.7368); n_slow = round(remaining * 0.2105)
        n_oth = remaining - n_acc - n_slow
        if n_oth < 0: n_acc += n_oth; n_oth = 0
        angles = np.empty(n_acc + n_slow + n_oth); idx = 0
        angles[idx:idx+n_acc] = ideal_angle + rng.uniform(-3*k, 3*k, n_acc); idx += n_acc
        diff = ideal_angle - prev_angle
        if diff > 180: diff -= 360
        if diff < -180: diff += 360
        if n_slow > 0:
            lag = rng.uniform(0.2, 0.5, n_slow)
            angles[idx:idx+n_slow] = prev_angle + diff * (1 - lag); idx += n_slow
        if n_oth > 0:
            angles[idx:idx+n_oth] = ideal_angle + rng.uniform(-30*k, 30*k, n_oth); idx += n_oth
        ntv = sm.angle_to_dir(angles[:idx])
        tv = rng.integers(0, 8, n_troll) if n_troll > 0 else np.array([], dtype=int)
        return np.concatenate([ntv, tv])
    return gv

def sim2():
    print("\n[SIM-2] noise width scale k in {0.5,1,2} x 3 methods x 8 speeds x 20% adversarial x MC15 = 1,080 runs")
    orig = sm.gen_votes
    res = {'config': {'k': [0.5, 1.0, 2.0], 'speeds': SPEEDS_8, 'troll': 0.20,
                      'basis': 'actual noise widths: accurate +/-3k deg, imprecise +/-30k deg (uniform); delayed-subtype lag unchanged'},
           'results': {}, 'eta2': {}}
    for k in [0.5, 1.0, 2.0]:
        sm.gen_votes = orig if k == 1.0 else make_scaled_gen_votes(k, orig)
        cell = {}
        for m in METHODS:
            for v in SPEEDS_8:
                tag = f"S2_k{k}_{m}_v{v}"
                r = run_mc(sm.Circle(), 0.20, m, v, tag)
                res['results'][tag] = r; cell[(m, v)] = r['rmse']
        res['eta2'][f"k{k}"] = eta2_two_way(cell)
        e = res['eta2'][f"k{k}"]
        print(f"  k={k}: η²_speed={e['eta2_speed']:.1%} η²_method={e['eta2_method']:.1%} "
              f"ratio={e['ratio_speed_method']:.1f}x")
    sm.gen_votes = orig
    return res

# ------------------------------------------------------------------
# SIM-3: velocity-smoothing alpha sensitivity
# ------------------------------------------------------------------
def sim3():
    print("\n[SIM-3] α∈{0.1,0.2,0.3} × 3 methods × 8 speeds × tr20% × MC15 = 1,080 runs")
    orig = sm.SMOOTH
    res = {'config': {'alpha': [0.1, 0.2, 0.3], 'speeds': SPEEDS_8, 'troll': 0.20,
                      'note': 'engine baseline alpha = 0.2; the sweep brackets it at 0.1 and 0.3'},
           'results': {}, 'eta2': {}}
    for a in [0.1, 0.2, 0.3]:
        sm.SMOOTH = a
        cell = {}
        for m in METHODS:
            for v in SPEEDS_8:
                tag = f"S3_a{a}_{m}_v{v}"
                r = run_mc(sm.Circle(), 0.20, m, v, tag)
                res['results'][tag] = r; cell[(m, v)] = r['rmse']
        res['eta2'][f"a{a}"] = eta2_two_way(cell)
        e = res['eta2'][f"a{a}"]
        print(f"  α={a}: η²_speed={e['eta2_speed']:.1%} η²_method={e['eta2_method']:.1%} "
              f"ratio={e['ratio_speed_method']:.1f}x")
    sm.SMOOTH = orig
    return res

# ------------------------------------------------------------------
# SIM-4: disruptor behavior variants
# ------------------------------------------------------------------
def make_troll_variant(mode, orig):
    """uniform (baseline) | opposite (ideal heading + 180 deg, +/-30 deg, quantised) | stale (previous ideal heading)"""
    def gv(ideal_angle, prev_angle, troll_ratio, N_agents, rng):
        votes = orig(ideal_angle, prev_angle, troll_ratio, N_agents, rng)
        n_troll = min(round(N_agents * troll_ratio), N_agents)
        if n_troll == 0 or mode == 'uniform':
            return votes
        if mode == 'opposite':
            ang = ideal_angle + 180 + rng.uniform(-30, 30, n_troll)
            votes[-n_troll:] = sm.angle_to_dir(ang)
        elif mode == 'stale':
            ang = np.full(n_troll, prev_angle) + rng.uniform(-15, 15, n_troll)
            votes[-n_troll:] = sm.angle_to_dir(ang)
        return votes
    return gv

def sim4():
    print("\n[SIM-4] disruptor variants {uniform, opposite, stale} x 3 methods x 8 speeds x 20% adversarial x MC15 = 1,080 runs")
    orig = sm.gen_votes
    res = {'config': {'variants': ['uniform', 'opposite', 'stale'], 'speeds': SPEEDS_8, 'troll': 0.20,
                      'note': 'disruptor variants are described in Methods and generated by this script'},
           'results': {}, 'eta2': {}}
    for mode in ['uniform', 'opposite', 'stale']:
        sm.gen_votes = make_troll_variant(mode, orig)
        cell = {}
        for m in METHODS:
            for v in SPEEDS_8:
                tag = f"S4_{mode}_{m}_v{v}"
                r = run_mc(sm.Circle(), 0.20, m, v, tag)
                res['results'][tag] = r; cell[(m, v)] = r['rmse']
        res['eta2'][mode] = eta2_two_way(cell)
        e = res['eta2'][mode]
        print(f"  {mode:8s}: η²_speed={e['eta2_speed']:.1%} η²_method={e['eta2_method']:.1%} "
              f"ratio={e['ratio_speed_method']:.1f}x")
    sm.gen_votes = orig
    return res

# ------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', type=int, choices=[1, 2, 3, 4], default=None)
    ap.add_argument('--skip-gate', action='store_true')
    args = ap.parse_args()

    if not args.skip_gate:
        validation_gate()

    out = {'meta': {'created': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'seed_scheme': f'seed = i*{SEED_BASE} + md5(cond_tag)%100000',
                    'engine': 'simulation_main.py, unmodified; SIM-specific parameters are applied at run time'}}
    t0 = time.time()
    sims = {1: sim1, 2: sim2, 3: sim3, 4: sim4}
    for i, fn in sims.items():
        if args.only in (None, i):
            out[f'SIM{i}'] = fn()
    fname = 'data/revision_sims_results.json'
    json.dump(out, open(fname, 'w'), indent=1)
    print(f"\nTotal {time.time()-t0:.0f}s -> saved {fname}")

if __name__ == '__main__':
    main()
