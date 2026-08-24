"""
E2 Speed Sweep + E3 Circle/Square Supplement
Uses the ceiling_verify.py engine unmodified.

E2:  Fixed method × 8speeds × 6trolls × 2trajs, N=150
     96 conditions x MC=15 = 1,440 runs

E3s: Circle/Square adversarial ratios not covered by the main archive (0.05, 0.20, 0.40)
     12Ns × 3trolls × 2trajs × MC=15 = 1,080 runs

Output: E2_proper_results.json, E3_supplement_proper.json
"""

import numpy as np, time, json
from itertools import product

# ================================================================
# Engine (identical to ceiling_verify.py)
# ================================================================
DT = 1/60
MSPD = 5.0
SMOOTH = 0.2
WIN = 0.3
DELAY_F = 26
DUR = 65.0
FRAMES = int(DUR / DT)
LOOK = 2.0
VOTE_INT = int(WIN / DT)  # 18 frames

S2 = np.sqrt(2) / 2
DIRS = np.array([[1,0],[S2,S2],[0,1],[-S2,S2],[-1,0],[-S2,-S2],[0,-1],[S2,-S2]])
DA = np.degrees(np.arctan2(DIRS[:,1], DIRS[:,0])) % 360

def a2d(angles):
    a = angles % 360
    diffs = np.abs(DA[None,:] - a[:,None])
    diffs = np.minimum(diffs, 360 - diffs)
    return np.argmin(diffs, axis=1)

class Circle:
    def __init__(s, R=10): s.R = R; s.circ = 2*np.pi*R
    def closest(s, p):
        t = np.arctan2(p[1], p[0])
        cp = s.R * np.array([np.cos(t), np.sin(t)])
        return cp, (t % (2*np.pi)) * s.R
    def at(s, arc):
        t = arc / s.R
        return s.R * np.array([np.cos(t), np.sin(t)])
    def start(s): return np.array([s.R, 0.])

class Square:
    def __init__(s, h=10):
        s.c = np.array([[h,0],[h,h],[-h,h],[-h,-h],[h,-h],[h,0.]], dtype=float)
        s.segs = [(s.c[i], s.c[i+1]) for i in range(5)]
        s.lens = [np.linalg.norm(b-a) for a,b in s.segs]
        s.circ = sum(s.lens)
        s.cum = np.array([0] + list(np.cumsum(s.lens)))
    def closest(s, p):
        bd, bp, ba = 1e10, s.c[0], 0.
        for i,(a,b) in enumerate(s.segs):
            v = b - a; l2 = v @ v
            if l2 < 1e-10: continue
            t = np.clip((p-a) @ v / l2, 0, 1)
            pt = a + t*v; d = np.linalg.norm(p - pt)
            if d < bd: bd, bp, ba = d, pt, s.cum[i] + t*s.lens[i]
        return bp, ba
    def at(s, arc):
        arc = arc % s.circ
        for i,(a,b) in enumerate(s.segs):
            if arc <= s.cum[i+1] + 1e-9:
                t = (arc - s.cum[i]) / s.lens[i]
                return a + np.clip(t, 0, 1) * (b - a)
        return s.c[-1]
    def start(s): return s.c[0].copy()

def gen_votes(iang, pang, tr, N, rng):
    # Participant allocation identical to simulation_main.py: the adversarial
    # count is taken first and the remainder is split among the three
    # non-adversarial subtypes, so the vote total is always exactly N.
    nt = min(round(N * tr), N)
    rem = N - nt
    na = round(rem * 0.7368)
    ns = round(rem * 0.2105)
    no = rem - na - ns
    if no < 0:
        na += no
        no = 0
    angs = np.empty(na + ns + no); i = 0
    angs[i:i+na] = iang + rng.uniform(-3, 3, na); i += na
    diff = iang - pang
    if diff > 180: diff -= 360
    if diff < -180: diff += 360
    if ns > 0:
        angs[i:i+ns] = pang + diff * (1 - rng.uniform(0.2, 0.5, ns)); i += ns
    if no > 0:
        angs[i:i+no] = iang + rng.uniform(-30, 30, no); i += no
    votes = a2d(angs[:i])
    trolls = rng.integers(0, 8, nt) if nt > 0 else np.array([], dtype=int)
    return np.concatenate([votes, trolls])

def sim(traj, N_agents, tr, seed, method='fixed', speed_override=None):
    rng = np.random.default_rng(seed)
    pos = traj.start(); vel = np.zeros(2)
    pos_hist = [pos.copy()]
    pang = 0.
    cur_dir = np.array([1., 0.]); cur_gamma = 0.5
    maj_dir = DIRS[0]
    V = speed_override if speed_override is not None else MSPD
    errs = np.empty(FRAMES); gammas = np.empty(FRAMES)

    for f in range(FRAMES):
        if f % VOTE_INT == 0:
            di = max(0, len(pos_hist) - 1 - DELAY_F)
            dp = pos_hist[di]
            _, arc = traj.closest(dp)
            lap = traj.at(arc + LOOK)
            idir = lap - dp
            n = np.linalg.norm(idir)
            if n > 1e-10: idir /= n
            iang = np.degrees(np.arctan2(idir[1], idir[0]))
            votes = gen_votes(iang, pang, tr, N_agents, rng)
            pang = iang
            vecs = DIRS[votes]; bl = vecs.mean(axis=0)
            cur_gamma = np.linalg.norm(bl)
            cur_dir = bl / cur_gamma if cur_gamma > 1e-10 else np.array([1., 0.])
            counts = np.bincount(votes, minlength=8)
            maj_dir = DIRS[np.argmax(counts)]

        gammas[f] = cur_gamma

        if method == 'fixed':
            tv = cur_dir * V
        elif method == 'majority':
            tv = maj_dir * V
        elif method == 'quadratic':
            tv = cur_dir * (cur_gamma**2) * V
        else:
            tv = cur_dir * V

        vel += SMOOTH * (tv - vel)
        pos = pos + vel * DT
        pos_hist.append(pos.copy())
        cp, _ = traj.closest(pos)
        errs[f] = np.linalg.norm(pos - cp)

    return {
        'rmse': float(np.sqrt(np.mean(errs**2))),
        'gm': float(np.mean(gammas)),
        'gs': float(np.std(gammas)),
    }

# ================================================================
# Engine verification
# ================================================================
print("=== Engine verification against the archived cells ===")
c = Circle(); sq = Square()
checks = [
    ("circle  tr=5%  v=2.0 N=150", c,  150, 0.05, 2.0,  0.2413),
    ("circle  tr=5%  v=5.0 N=150", c,  150, 0.05, 5.0,  0.8019),
    ("circle  tr=20% v=2.0 N=150", c,  150, 0.20, 2.0,  0.2486),
    ("square  tr=5%  v=1.0 N=150", sq, 150, 0.05, 1.0,  0.0633),
]
for label, tj, N, tr, v, expect in checks:
    r = np.mean([sim(tj, N, tr, i*31+N, speed_override=v)['rmse'] for i in range(10)])
    ok = "✅" if abs(r - expect) < 0.03 else "⚠️ "
    print(f"  {ok} {label}: {r:.4f} (expect {expect:.4f})")

print()

# ================================================================
# E2: Speed Sweep
# Fixed × 8speeds × 6trolls × 2trajs, N=150
# ================================================================
MC = 15
SPEEDS = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
TROLLS = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40]
TRAJS  = {'circle': c, 'square': sq}
N_FIXED = 150

total_e2 = len(SPEEDS) * len(TROLLS) * len(TRAJS) * MC
print(f"=== E2: Speed Sweep ===")
print(f"96 conditions x MC={MC} = {total_e2} runs")
print()

e2_results = {}
cnt = 0; t0 = time.time()

for traj_name, traj_obj in TRAJS.items():
    for tr in TROLLS:
        for v in SPEEDS:
            key = f"{traj_name}_tr{tr:.2f}_v{v:.1f}"
            runs = [sim(traj_obj, N_FIXED, tr, seed=i*997+int(v*10)+int(tr*100),
                        speed_override=v) for i in range(MC)]
            cnt += MC
            rmses = [x['rmse'] for x in runs]
            gmeans = [x['gm'] for x in runs]
            arr = np.array(rmses)
            e2_results[key] = {
                'rmse_mean':  round(float(arr.mean()), 4),
                'rmse_std':   round(float(arr.std()),  4),
                'rmse_ci95':  round(float(1.96*arr.std()/np.sqrt(MC)), 4),
                'gamma_mean': round(float(np.mean(gmeans)), 4),
                'mc_runs':    MC,
            }
            el = time.time() - t0
            eta = el/cnt*(total_e2-cnt) if cnt > 0 else 0
            print(f"  [{cnt//MC:>3}/{total_e2//MC}] {key}: "
                  f"RMSE={arr.mean():.4f} [{eta:.0f}s left]")

with open('data/E2_proper_results.json', 'w') as f:
    json.dump({'config': {'MC': MC, 'N': N_FIXED, 'method': 'fixed',
                          'speeds': SPEEDS, 'trolls': TROLLS,
                          'trajectories': list(TRAJS.keys())},
               'results': e2_results}, f, indent=2)
print(f"\n[done] E2 -> E2_proper_results.json ({time.time()-t0:.0f}s)")

# ================================================================
# E3 Supplement: circle/square missing trolls
# Archived: 0.10, 0.15, 0.30   Added here: 0.05, 0.20, 0.40
# ================================================================
NS = [5, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200]
MISSING_TROLLS = [0.05, 0.20, 0.40]
SPEED_E3 = 5.0

total_e3 = len(NS) * len(MISSING_TROLLS) * len(TRAJS) * MC
print(f"\n=== E3 Supplement: circle/square missing trolls ===")
print(f"72 conditions x MC={MC} = {total_e3} runs")
print()

e3_results = {}
cnt = 0; t1 = time.time()

for traj_name, traj_obj in TRAJS.items():
    for tr in MISSING_TROLLS:
        for N in NS:
            key = f"{traj_name}_tr{tr:.2f}_N{N}"
            runs = [sim(traj_obj, N, tr, seed=i*31+N+int(tr*100),
                        speed_override=SPEED_E3) for i in range(MC)]
            cnt += MC
            rmses = [x['rmse'] for x in runs]
            gmeans = [x['gm'] for x in runs]
            arr = np.array(rmses)
            e3_results[key] = {
                'rmse_mean':  round(float(arr.mean()), 4),
                'rmse_std':   round(float(arr.std()),  4),
                'rmse_ci95':  round(float(1.96*arr.std()/np.sqrt(MC)), 4),
                'gamma_mean': round(float(np.mean(gmeans)), 4),
                'mc_runs':    MC,
            }
            el = time.time() - t1
            eta = el/cnt*(total_e3-cnt) if cnt > 0 else 0
            print(f"  [{cnt//MC:>3}/{total_e3//MC}] {key}: "
                  f"RMSE={arr.mean():.4f} [{eta:.0f}s left]")

with open('data/E3_supplement_proper.json', 'w') as f:
    json.dump({'config': {'MC': MC, 'speed': SPEED_E3,
                          'Ns': NS, 'new_trolls': MISSING_TROLLS,
                          'trajectories': list(TRAJS.keys())},
               'results': e3_results}, f, indent=2)
print(f"\n[done] E3 supplement -> E3_supplement_proper.json ({time.time()-t1:.0f}s)")
print("\n🎉 All done.")
