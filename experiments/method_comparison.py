"""
========================================================================
Method Comparison Experiment
Experiment E1: speed x method factorial (variance decomposition).

Engine: identical to paper_fullscale.py (ceiling_verify.py compatible)
MC = 15 replications per condition (used throughout the paper)

Design:
  Manipulated: method (fixed, majority, quadratic)
            speed (1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0)
  Controlled: N = 150 fixed, participant subtype ratios fixed
  Environment: adversarial ratio (0.05, 0.20, 0.40), trajectory (circle, square)
  Measured: RMSE, gamma, realised speed

  Total: 3 × 8 × 3 × 2 × 15 = 2,160 sims
  Estimated: ~20 min

Statistics:
  1) Welch's t-test on method pairs (Fixed vs Majority, etc.)
  2) One-way ANOVA across the three methods
  3) Effect size (Cohen's d)
  4) Speed contribution vs Method contribution (eta-squared)

Usage: python3 method_comparison.py
Output: method_comparison_results.json
========================================================================
"""
import numpy as np
import time
import json
from scipy.optimize import curve_fit
from scipy import stats as sp_stats

# ====================================================================
# ENGINE (identical to paper_fullscale.py)
# ====================================================================
DT        = 1/60
MSPD      = 5.0
SMOOTH    = 0.2
WIN       = 0.3
DELAY_F   = 26
DUR       = 65.0
FRAMES    = int(DUR / DT)
LOOK      = 2.0
VOTE_INT  = int(WIN / DT)

S2 = np.sqrt(2) / 2
DIRS = np.array([
    [1, 0], [S2, S2], [0, 1], [-S2, S2],
    [-1, 0], [-S2, -S2], [0, -1], [S2, -S2]
])
DIR_ANGLES = np.degrees(np.arctan2(DIRS[:, 1], DIRS[:, 0])) % 360

def angle_to_dir(angles):
    a = angles % 360
    diffs = np.abs(DIR_ANGLES[None, :] - a[:, None])
    diffs = np.minimum(diffs, 360 - diffs)
    return np.argmin(diffs, axis=1)

class Circle:
    def __init__(self, R=10):
        self.R = R; self.circ = 2 * np.pi * R; self.name = 'circle'
    def closest(self, p):
        t = np.arctan2(p[1], p[0])
        cp = self.R * np.array([np.cos(t), np.sin(t)])
        return cp, (t % (2 * np.pi)) * self.R
    def at(self, arc):
        t = arc / self.R
        return self.R * np.array([np.cos(t), np.sin(t)])
    def start(self): return np.array([self.R, 0.])

class Square:
    def __init__(self, h=10):
        self.name = 'square'
        self.c = np.array([[h,0],[h,h],[-h,h],[-h,-h],[h,-h],[h,0.]], dtype=float)
        self.segs = [(self.c[i], self.c[i+1]) for i in range(5)]
        self.lens = [np.linalg.norm(b-a) for a,b in self.segs]
        self.circ = sum(self.lens)
        self.cum = np.array([0] + list(np.cumsum(self.lens)))
    def closest(self, p):
        bd, bp, ba = 1e10, self.c[0], 0.
        for i, (a, b) in enumerate(self.segs):
            v = b - a; l2 = v @ v
            if l2 < 1e-10: continue
            t = np.clip((p-a) @ v / l2, 0, 1)
            pt = a + t*v; d = np.linalg.norm(p - pt)
            if d < bd: bd, bp, ba = d, pt, self.cum[i] + t*self.lens[i]
        return bp, ba
    def at(self, arc):
        arc = arc % self.circ
        for i, (a, b) in enumerate(self.segs):
            if arc <= self.cum[i+1] + 1e-9:
                t = (arc - self.cum[i]) / self.lens[i]
                return a + np.clip(t, 0, 1) * (b - a)
        return self.c[-1]
    def start(self): return self.c[0].copy()

def gen_votes(ideal_angle, prev_angle, troll_ratio, N_agents, rng):
    n_troll = round(N_agents * troll_ratio)
    n_troll = min(n_troll, N_agents)
    remaining = N_agents - n_troll
    n_accurate = round(remaining * 0.7368)
    n_slow     = round(remaining * 0.2105)
    n_other    = remaining - n_accurate - n_slow
    if n_other < 0:
        n_accurate += n_other; n_other = 0

    angles = np.empty(n_accurate + n_slow + n_other); idx = 0
    angles[idx:idx+n_accurate] = ideal_angle + rng.uniform(-3, 3, n_accurate); idx += n_accurate
    diff = ideal_angle - prev_angle
    if diff > 180: diff -= 360
    if diff < -180: diff += 360
    if n_slow > 0:
        angles[idx:idx+n_slow] = prev_angle + diff * (1 - rng.uniform(0.2, 0.5, n_slow)); idx += n_slow
    if n_other > 0:
        angles[idx:idx+n_other] = ideal_angle + rng.uniform(-30, 30, n_other); idx += n_other
    non_troll_votes = angle_to_dir(angles[:idx])
    troll_votes = rng.integers(0, 8, n_troll) if n_troll > 0 else np.array([], dtype=int)
    return np.concatenate([non_troll_votes, troll_votes])

def simulate(traj, N_agents, troll_ratio, seed,
             method='fixed', speed_override=None):
    rng = np.random.default_rng(seed)
    pos = traj.start(); vel = np.zeros(2)
    pos_hist = [pos.copy()]
    prev_angle = 0.0; cur_dir = np.array([1., 0.])
    cur_gamma = 0.5; maj_dir = DIRS[0]
    V = speed_override if speed_override is not None else MSPD
    errors = np.empty(FRAMES); gammas = np.empty(FRAMES)

    for f in range(FRAMES):
        if f % VOTE_INT == 0:
            delay_idx = max(0, len(pos_hist) - 1 - DELAY_F)
            delayed_pos = pos_hist[delay_idx]
            _, arc = traj.closest(delayed_pos)
            look_pt = traj.at(arc + LOOK)
            ideal_dir = look_pt - delayed_pos
            norm = np.linalg.norm(ideal_dir)
            if norm > 1e-10: ideal_dir /= norm
            ideal_angle = np.degrees(np.arctan2(ideal_dir[1], ideal_dir[0]))
            votes = gen_votes(ideal_angle, prev_angle, troll_ratio, N_agents, rng)
            prev_angle = ideal_angle
            vote_vectors = DIRS[votes]
            blend = vote_vectors.mean(axis=0)
            cur_gamma = np.linalg.norm(blend)
            cur_dir = blend / cur_gamma if cur_gamma > 1e-10 else np.array([1., 0.])
            counts = np.bincount(votes, minlength=8)
            maj_dir = DIRS[np.argmax(counts)]

        gammas[f] = cur_gamma
        if method == 'fixed':
            tv = cur_dir * V
        elif method == 'majority':
            tv = maj_dir * V
        elif method == 'quadratic':
            tv = cur_dir * (cur_gamma ** 2) * V
        else:
            tv = cur_dir * V

        vel += SMOOTH * (tv - vel)
        pos = pos + vel * DT
        pos_hist.append(pos.copy())
        cp, _ = traj.closest(pos)
        errors[f] = np.linalg.norm(pos - cp)

    return {
        'rmse': float(np.sqrt(np.mean(errors**2))),
        'gamma_mean': float(np.mean(gammas)),
    }


# ====================================================================
# EXPERIMENT: METHOD COMPARISON
# ====================================================================
def main():
    t_start = time.time()

    MC = 15
    N_FIXED = 150
    methods = ['fixed', 'majority', 'quadratic']
    speeds = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
    trolls = [0.05, 0.20, 0.40]
    trajs = {'circle': Circle(), 'square': Square()}

    total = len(methods) * len(speeds) * len(trolls) * len(trajs) * MC
    print("=" * 65)
    print(f"METHOD COMPARISON EXPERIMENT")
    print(f"  {len(methods)} methods x {len(speeds)} speeds x {len(trolls)} trolls "
          f"x {len(trajs)} trajs x MC={MC}")
    print(f"  Total: {total} sims")
    print("=" * 65)

    # --- Run simulations ---
    raw = {}  # key: "traj_trX.XX_vX.X_method" → list of MC rmse values
    cnt = 0
    t0 = time.time()

    for tn, tj in trajs.items():
        for tr in trolls:
            for v in speeds:
                for m in methods:
                    rmses = []
                    for i in range(MC):
                        seed = i * 31 + int(v * 100) + {'fixed': 1000, 'majority': 2000, 'quadratic': 3000}[m]  # stable method salt (v1.1.0: replaced hash(m), which is not reproducible across processes)
                        r = simulate(tj, N_FIXED, tr, seed,
                                     method=m, speed_override=v)
                        rmses.append(r['rmse'])
                        cnt += 1

                    key = f"{tn}_tr{tr:.2f}_v{v:.1f}_{m}"
                    raw[key] = {
                        'rmses': rmses,
                        'rmse_mean': round(np.mean(rmses), 4),
                        'rmse_std': round(np.std(rmses), 4),
                        'rmse_ci95': round(1.96 * np.std(rmses) / np.sqrt(MC), 4),
                    }

                    if cnt % (MC * 6) == 0:
                        elapsed = time.time() - t0
                        eta = elapsed / cnt * (total - cnt)
                        print(f"  [{cnt:>5}/{total}] {tn} tr={tr:.0%} v={v:.1f} {m:10s}: "
                              f"RMSE={raw[key]['rmse_mean']:.4f} [{eta:.0f}s left]")

    print(f"\n  Simulations done: {time.time()-t0:.0f}s")

    # ================================================================
    # STATISTICAL ANALYSIS
    # ================================================================
    print("\n" + "=" * 65)
    print("STATISTICAL ANALYSIS")
    print("=" * 65)

    # ------------------------------------------------------------------
    # 1) Pairwise comparison: Same speed, same troll, same traj
    #    -> is there a difference between methods?
    # ------------------------------------------------------------------
    print("\n--- 1. Pairwise Method Comparison (Welch's t-test) ---")
    print(f"  H0: the two methods have equal mean RMSE at the same speed")
    print(f"  {'Condition':<30} {'F_mean':>7} {'M_mean':>7} {'Q_mean':>7} "
          f"{'F-M_p':>7} {'F-Q_p':>7} {'M-Q_p':>7} {'sig':>4}")
    print(f"  {'-'*82}")

    pair_results = []
    sig_count = 0
    total_pairs = 0

    for tn in trajs:
        for tr in trolls:
            for v in speeds:
                f_key = f"{tn}_tr{tr:.2f}_v{v:.1f}_fixed"
                m_key = f"{tn}_tr{tr:.2f}_v{v:.1f}_majority"
                q_key = f"{tn}_tr{tr:.2f}_v{v:.1f}_quadratic"

                f_data = raw[f_key]['rmses']
                m_data = raw[m_key]['rmses']
                q_data = raw[q_key]['rmses']

                # Welch's t-tests
                _, p_fm = sp_stats.ttest_ind(f_data, m_data, equal_var=False)
                _, p_fq = sp_stats.ttest_ind(f_data, q_data, equal_var=False)
                _, p_mq = sp_stats.ttest_ind(m_data, q_data, equal_var=False)

                # Cohen's d (Fixed vs Majority)
                pooled_std = np.sqrt((np.var(f_data) + np.var(m_data)) / 2)
                d_fm = abs(np.mean(f_data) - np.mean(m_data)) / pooled_std if pooled_std > 0 else 0

                any_sig = p_fm < 0.05 or p_fq < 0.05 or p_mq < 0.05
                if any_sig:
                    sig_count += 1
                total_pairs += 1

                sig_mark = "*" if any_sig else ""
                label = f"{tn} tr={tr:.0%} v={v:.1f}"
                print(f"  {label:<30} {np.mean(f_data):>7.4f} {np.mean(m_data):>7.4f} "
                      f"{np.mean(q_data):>7.4f} {p_fm:>7.3f} {p_fq:>7.3f} {p_mq:>7.3f} {sig_mark:>4}")

                pair_results.append({
                    'traj': tn, 'troll': tr, 'speed': v,
                    'fixed_mean': round(np.mean(f_data), 4),
                    'majority_mean': round(np.mean(m_data), 4),
                    'quadratic_mean': round(np.mean(q_data), 4),
                    'p_fm': round(p_fm, 4),
                    'p_fq': round(p_fq, 4),
                    'p_mq': round(p_mq, 4),
                    'cohens_d_fm': round(d_fm, 4),
                    'any_significant': any_sig,
                })

    print(f"\n  Significant pairs: {sig_count}/{total_pairs} "
          f"({sig_count/total_pairs*100:.1f}%)")
    print(f"  Expected by chance (alpha=0.05): {total_pairs*0.05:.0f}")

    # ------------------------------------------------------------------
    # 2) Two-way ANOVA: Speed × Method → RMSE
    #    -> contribution of Speed vs Method
    # ------------------------------------------------------------------
    print("\n--- 2. Speed vs Method Contribution (eta-squared) ---")

    for tn in trajs:
        for tr in trolls:
            all_rmse = []
            all_speed = []
            all_method = []

            for v in speeds:
                for m in methods:
                    key = f"{tn}_tr{tr:.2f}_v{v:.1f}_{m}"
                    for rmse_val in raw[key]['rmses']:
                        all_rmse.append(rmse_val)
                        all_speed.append(v)
                        all_method.append(m)

            all_rmse = np.array(all_rmse)
            all_speed = np.array(all_speed)
            all_method = np.array(all_method)

            grand_mean = np.mean(all_rmse)
            ss_total = np.sum((all_rmse - grand_mean)**2)

            # SS_speed
            ss_speed = 0
            for v in speeds:
                mask = all_speed == v
                group_mean = np.mean(all_rmse[mask])
                ss_speed += np.sum(mask) * (group_mean - grand_mean)**2

            # SS_method
            ss_method = 0
            for m in methods:
                mask = all_method == m
                group_mean = np.mean(all_rmse[mask])
                ss_method += np.sum(mask) * (group_mean - grand_mean)**2

            eta_speed = ss_speed / ss_total if ss_total > 0 else 0
            eta_method = ss_method / ss_total if ss_total > 0 else 0
            ratio = eta_speed / eta_method if eta_method > 0 else float('inf')

            print(f"  {tn} tr={tr:.0%}:")
            print(f"    eta2_speed  = {eta_speed:.4f} ({eta_speed*100:.1f}%)")
            print(f"    eta2_method = {eta_method:.4f} ({eta_method*100:.1f}%)")
            print(f"    ratio = {ratio:.1f}x")

    # ------------------------------------------------------------------
    # 3) Method ranking at each speed: who wins?
    # ------------------------------------------------------------------
    print("\n--- 3. Method Rankings (who wins at each speed?) ---")

    wins = {'fixed': 0, 'majority': 0, 'quadratic': 0, 'tie': 0}
    rankings = []

    for tn in trajs:
        for tr in trolls:
            print(f"\n  {tn} tr={tr:.0%}:")
            for v in speeds:
                means = {}
                for m in methods:
                    key = f"{tn}_tr{tr:.2f}_v{v:.1f}_{m}"
                    means[m] = raw[key]['rmse_mean']

                best = min(means, key=means.get)
                worst = max(means, key=means.get)
                spread = (means[worst] - means[best]) / means[best] * 100

                # Is best significantly better than 2nd?
                sorted_m = sorted(means.items(), key=lambda x: x[1])
                _, p_12 = sp_stats.ttest_ind(
                    raw[f"{tn}_tr{tr:.2f}_v{v:.1f}_{sorted_m[0][0]}"]['rmses'],
                    raw[f"{tn}_tr{tr:.2f}_v{v:.1f}_{sorted_m[1][0]}"]['rmses'],
                    equal_var=False
                )

                if p_12 < 0.05:
                    wins[best] += 1
                    winner = best
                else:
                    wins['tie'] += 1
                    winner = 'tie'

                rankings.append({
                    'traj': tn, 'troll': tr, 'speed': v,
                    'winner': winner, 'spread_pct': round(spread, 2),
                    'p_value': round(p_12, 4),
                })

                bar = '|' + '#' * min(int(spread), 40)
                print(f"    v={v:.1f}: {best:10s} wins (spread={spread:>5.1f}%) "
                      f"p={p_12:.3f} {bar}")

    print(f"\n  Win summary:")
    total_comp = sum(wins.values())
    for m in ['fixed', 'majority', 'quadratic', 'tie']:
        pct = wins[m] / total_comp * 100
        print(f"    {m:12s}: {wins[m]:>3}/{total_comp} ({pct:.1f}%)")

    # ------------------------------------------------------------------
    # 4) Speed dominance: RMSE range by speed vs by method
    # ------------------------------------------------------------------
    print("\n--- 4. Speed Dominance Quantification ---")

    for tn in trajs:
        for tr in trolls:
            # RMSE range across speeds (method fixed)
            speed_range = []
            for m in methods:
                rmse_by_speed = []
                for v in speeds:
                    key = f"{tn}_tr{tr:.2f}_v{v:.1f}_{m}"
                    rmse_by_speed.append(raw[key]['rmse_mean'])
                speed_range.append(max(rmse_by_speed) - min(rmse_by_speed))

            # RMSE range across methods (speed fixed)
            method_range = []
            for v in speeds:
                rmse_by_method = []
                for m in methods:
                    key = f"{tn}_tr{tr:.2f}_v{v:.1f}_{m}"
                    rmse_by_method.append(raw[key]['rmse_mean'])
                method_range.append(max(rmse_by_method) - min(rmse_by_method))

            avg_speed_range = np.mean(speed_range)
            avg_method_range = np.mean(method_range)
            dominance = avg_speed_range / avg_method_range if avg_method_range > 0 else float('inf')

            print(f"  {tn} tr={tr:.0%}:")
            print(f"    Avg RMSE range by speed:  {avg_speed_range:.4f}")
            print(f"    Avg RMSE range by method: {avg_method_range:.4f}")
            print(f"    Speed/Method ratio: {dominance:.1f}x")

    # ================================================================
    # SAVE RESULTS
    # ================================================================
    # Compress raw (don't save individual MC values, too large)
    raw_compact = {}
    for key, val in raw.items():
        raw_compact[key] = {
            'rmse_mean': val['rmse_mean'],
            'rmse_std': val['rmse_std'],
            'rmse_ci95': val['rmse_ci95'],
        }

    output = {
        'raw_results': raw,  # v1.1.0: run-level rmses preserved
        'pairwise_tests': pair_results,
        'rankings': rankings,
        'win_summary': wins,
        'config': {
            'MC': MC, 'N_fixed': N_FIXED,
            'methods': methods, 'speeds': speeds,
            'trolls': trolls, 'trajectories': list(trajs.keys()),
        },
        'metadata': {
            'total_sims': total,
            'total_time_sec': round(time.time() - t_start),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        }
    }

    outfile = 'data/method_comparison_results.json'
    with open(outfile, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    # ================================================================
    # FINAL SUMMARY
    # ================================================================
    print("\n" + "=" * 65)
    print("FINAL SUMMARY")
    print("=" * 65)

    print(f"  Total sims: {total}")
    print(f"  Total time: {time.time()-t_start:.0f}s")
    print(f"\n  Key findings:")
    print(f"    Significant method pairs: {sig_count}/{total_pairs} "
          f"({sig_count/total_pairs*100:.1f}%)")
    print(f"    Expected by chance: ~{total_pairs*0.05:.0f} (5%)")

    sig_excess = sig_count > total_pairs * 0.10
    if not sig_excess:
        print(f"    → Method differences are WITHIN chance level")
        print(f"    → SUPPORTS Claim 1: Speed > Method")
    else:
        print(f"    → More significant pairs than expected")
        print(f"    → Method differences may exist at some conditions")

    print(f"\n    Win distribution: {wins}")
    if wins['tie'] > total_comp * 0.5:
        print(f"    → Majority of comparisons are TIES")
        print(f"    → SUPPORTS: Methods are interchangeable")

    print(f"\n  Saved to: {outfile}")


if __name__ == '__main__':
    main()
