"""Recompute the derived statistics reported in the manuscript and check them
against the values printed in the paper.

Run from the repository root:

    python analysis/reproduce_reported_statistics.py

Everything is recomputed from the archived JSONs in data/ (no simulation).
Each line prints the recomputed value, the value stated in the manuscript, and
PASS/FAIL.  Exit status is non-zero if any check fails.
"""
import json, itertools, sys
import numpy as np

# ----------------------------------------------------------------- helpers
RESULTS = []


def check(label, got, expect, tol, unit=''):
    ok = abs(got - expect) <= tol
    RESULTS.append(ok)
    print('  [%s] %-52s %10.4g %s  (expected %.4g%s, tol %g)'
          % ('PASS' if ok else 'FAIL', label, got, unit, expect, unit, tol))
    return ok


def check_eq(label, got, expect):
    ok = got == expect
    RESULTS.append(ok)
    print('  [%s] %-52s %-18s (expected %s)'
          % ('PASS' if ok else 'FAIL', label, str(got), str(expect)))
    return ok


def info(label, text):
    print('  [INFO] %-52s %s' % (label, text))


SPEEDS = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
METHODS = ['fixed', 'majority', 'quadratic']
TRAJ = ['circle', 'square']
TROLL = [0.05, 0.20, 0.40]          # legacy key name; = adversarial ratio p

RAW = json.load(open('data/method_comparison_results.json'))['raw_results']


def cell(traj, tr, v, m):
    k = "%s_tr%.2f_v%s_%s" % (traj, tr, v, m)
    if k not in RAW:
        k = "%s_tr%s_v%s_%s" % (traj, tr, v, m)
    return RAW[k]


def two_way_eta2(traj, tr, speeds, methods):
    y = np.array([cell(traj, tr, v, m)['rmses'] for v in speeds for m in methods], float)
    n = y.shape[1]
    S, M = len(speeds), len(methods)
    grand = y.mean()
    cm = y.mean(axis=1).reshape(S, M)
    ss_tot = ((y - grand) ** 2).sum()
    ss_s = n * M * ((cm.mean(axis=1) - grand) ** 2).sum()
    ss_m = n * S * ((cm.mean(axis=0) - grand) ** 2).sum()
    ss_c = n * ((cm - grand) ** 2).sum()
    ss_i = ss_c - ss_s - ss_m
    ss_e = ss_tot - ss_c
    df = (S - 1, M - 1, (S - 1) * (M - 1), S * M * (n - 1))
    ms = [ss_s / df[0], ss_m / df[1], ss_i / df[2], ss_e / df[3]]
    return dict(eta=[100 * x / ss_tot for x in (ss_s, ss_m, ss_i, ss_e)],
                F=[ms[0] / ms[3], ms[1] / ms[3], ms[2] / ms[3]], df=df,
                SS=[ss_s, ss_m, ss_i, ss_e])


# ------------------------------------------------- 1. Table 1 (two-way ANOVA)
def table1():
    print('\n1. Table 1 - two-way ANOVA vs data/e1_anova_v2.json')
    arch = json.load(open('data/e1_anova_v2.json'))
    for traj, tr in itertools.product(TRAJ, TROLL):
        r = two_way_eta2(traj, tr, SPEEDS, METHODS)
        a = arch['%s_%d' % (traj, round(tr * 100))]
        tag = '%s %d%%' % (traj, round(tr * 100))
        for i, nm in enumerate(('speed', 'method', 'S x M', 'error')):
            check('%s eta2 %s' % (tag, nm), r['eta'][i], a['eta2_pct'][i], 0.05, '%')
        for i, nm in enumerate(('speed', 'method', 'S x M')):
            check('%s F %s' % (tag, nm), round(r['F'][i]), a['F'][i], 0)


# ------------------------------------------ 2. headline speed-to-method ratios
def ratios():
    print('\n2. Speed-to-method eta2 ratios')
    rs = {}
    for traj, tr in itertools.product(TRAJ, TROLL):
        e = two_way_eta2(traj, tr, SPEEDS, METHODS)['eta']
        rs[(traj, tr)] = e[0] / e[1]
    circ = [rs[('circle', t)] for t in TROLL]
    allr = list(rs.values())
    check('circle ratio min (manuscript "5-26x")', min(circ), 5.13, 0.05, 'x')
    check('circle ratio max (manuscript "5-26x")', max(circ), 26.10, 0.05, 'x')
    check('all-cell ratio min (manuscript "1.6-46x")', min(allr), 1.61, 0.02, 'x')
    check('all-cell ratio max (Table S11 value)', max(allr), 45.54, 0.05, 'x')
    info('  -> as printed in Table 1 / Abstract',
         '46x  (96.6/2.1 from the printed one-decimal eta2)')
    # Rounding basis.  The manuscript reports summary statistics computed from the
    # eta^2 values as PRINTED IN TABLE 1 (one decimal place).  The Abstract's
    # "median 6.9x" is the median of the ratios formed from those printed values.
    # Recomputing at full archive precision shifts the median slightly, because the
    # two middle cells (square 20%, circle 40%) sit close together; both bases are
    # reported here so the reader can reconcile the Abstract with Supplementary
    # Table S11, which prints the ratios at full precision.
    rnd = {}
    for traj, tr in itertools.product(TRAJ, TROLL):
        e = two_way_eta2(traj, tr, SPEEDS, METHODS)['eta']
        rnd[(traj, tr)] = round(e[0], 1) / round(e[1], 1)
    check('abstract median (Table 1 printed eta2 basis)',
          float(np.median(list(rnd.values()))), 6.943, 0.01, 'x')
    info('same median at full archive precision',
         '%.3fx  (rounds to 7.0x; Table S11 prints ratios at this precision)'
         % float(np.median(allr)))
    check_eq('every cell ratio > 1', all(r > 1 for r in allr), True)


# --------------------------------------------------- 3. Monte-Carlo precision
def mc_precision():
    print('\n3. Monte-Carlo precision over the 144 E1 cells')
    hw, cv = [], []
    for traj, tr, v, m in itertools.product(TRAJ, TROLL, SPEEDS, METHODS):
        r = np.array(cell(traj, tr, v, m)['rmses'], float)
        sd, mu = r.std(ddof=0), r.mean()
        hw.append(100 * 1.96 * sd / np.sqrt(len(r)) / mu)
        cv.append(100 * sd / mu)
    hw, cv = np.array(hw), np.array(cv)
    check_eq('number of cells', len(hw), 144)
    check('median 95% CI half-width', float(np.median(hw)), 1.4, 0.05, '%')
    check('mean 95% CI half-width', float(hw.mean()), 2.21, 0.01, '%')
    check('share of cells below 5%', float(100 * (hw < 5).mean()), 87.5, 0.1, '%')
    check('mean coefficient of variation', float(cv.mean()), 4.37, 0.01, '%')


# ------------------------------------------------ 4. method rankings / spreads
def rankings():
    print('\n4. Method rankings and spreads')
    best = ci = 0
    for traj, tr, v in itertools.product(TRAJ, TROLL, SPEEDS):
        cs = {m: np.array(cell(traj, tr, v, m)['rmses'], float) for m in METHODS}
        mu = {m: cs[m].mean() for m in METHODS}
        if min(mu, key=mu.get) != 'quadratic':
            continue
        best += 1
        def bnd(m):
            r = cs[m]; h = 1.96 * r.std(ddof=0) / np.sqrt(len(r))
            return r.mean() - h, r.mean() + h
        if all(bnd('quadratic')[1] < bnd(m)[0] for m in METHODS if m != 'quadratic'):
            ci += 1
    check_eq('Quadratic ranks best (of 48)', best, 32)
    check_eq('Quadratic best with non-overlapping CI (of 48)', ci, 31)
    for traj, exp_sp, exp_sv in (('circle', 0.11, 0.55), ('square', 0.24, 1.08)):
        sp, sv = [], []
        for tr in TROLL:
            for v in SPEEDS:
                mus = [np.mean(cell(traj, tr, v, m)['rmses']) for m in METHODS]
                sp.append(max(mus) - min(mus))
            for m in METHODS:
                mus = [np.mean(cell(traj, tr, v, m)['rmses']) for v in SPEEDS]
                sv.append(max(mus) - min(mus))
        check('%s median method spread' % traj, float(np.median(sp)), exp_sp, 0.005, ' m')
        check('%s median speed-induced variation' % traj, float(np.median(sv)), exp_sv, 0.005, ' m')


# ---------------------------------------------------- 5. Table S11 sub-ranges
def s11():
    print('\n5. Supplementary Table S11 - restricted speed sub-ranges')
    sub = []
    for traj, tr in itertools.product(TRAJ, TROLL):
        for speeds in ([1.5, 2.0, 2.5], [3.0, 3.5, 4.0]):
            e3 = two_way_eta2(traj, tr, speeds, METHODS)['eta']
            e2 = two_way_eta2(traj, tr, speeds, ['fixed', 'majority'])['eta']
            sub.append((e3[0] / e3[1], e2[0] / e2[1]))
    below = [x for x in sub if x[0] < 1]
    check_eq('sub-range combinations', len(sub), 12)
    check_eq('combinations with method effect above speed', len(below), 6)
    check('minimum ratio', min(x[0] for x in sub), 0.07, 0.005, 'x')
    check('Fixed+Majority-only min for those six', min(x[1] for x in below), 1.5, 0.05, 'x')
    check('Fixed+Majority-only max for those six', max(x[1] for x in below), 219.2, 0.5, 'x')


# ---------------------------------------------------- 6. optimal speed (S1)
def vstar():
    print('\n6. Optimal speed v*')
    d = json.load(open('data/s1_vstar.json'))['summary']
    check_eq('circle grid minimum identical across ratios',
             bool(d['circle_grid_min_identical_across_ratios']), True)
    check('circle grid minimum', float(d['circle_grid_min_unique'][0]), 2.0, 1e-9, ' m/s')
    check('circle parabola vertex mean', float(d['circle_vertex_mean']), 2.05, 0.005, ' m/s')
    check('circle parabola vertex s.d.', float(d['circle_vertex_sd']), 0.05, 0.005, ' m/s')
    check('circle vertex range low', float(d['circle_vertex_range'][0]), 1.95, 0.005, ' m/s')
    check('circle vertex range high', float(d['circle_vertex_range'][1]), 2.09, 0.005, ' m/s')
    check_eq('square minimum censored at lower bound',
             bool(d['square_all_at_lower_bound']), True)


# ------------------------------------------------------ 7. predictive model
def model():
    print('\n7. Predictive model (Fixed policy, circle)')
    m = json.load(open('data/model_refit120_results.json'))
    a0, a1, a2, a3 = m['coeff_mul']
    check('a0', a0, 0.514, 0.001)
    check('a1', a1, -0.237, 0.001)
    check('a2', a2, 0.058, 0.001)
    check('a3', a3, 2.230, 0.002)
    check('training R^2 (multiplicative)', m['r2_mul'], 0.988, 0.0005)
    check('training R^2 (additive)', m['r2_add'], 0.987, 0.0005)
    check('5-fold CV R^2 mean', m['cv_mean'], 0.9871, 0.0002)
    check('5-fold CV R^2 s.d.', m['cv_std'], 0.0048, 0.0002)
    check('v* from fitted coefficients', -a1 / (2 * a2), 2.04, 0.005, ' m/s')


# ---------------------------------------------------- 8. sensitivity campaign
def sensitivity():
    print('\n8. Sensitivity campaign (SIM-1..4)')
    d = json.load(open('data/revision_sims_results.json'))
    def ratios_from(eta_block):
        out = {}
        for k, v in eta_block.items():
            keys = list(v)
            sp = v.get('speed', v.get('eta2_speed'))
            me = v.get('method', v.get('eta2_method'))
            if sp is None or me is None:
                sp, me = v[keys[0]], v[keys[1]]
            out[k] = sp / me
        return out
    r1 = ratios_from(d['SIM1']['eta2'])
    check_eq('SIM-1 delay x adversarial cells', len(r1), 18)
    check_eq('all SIM-1 ratios above unity', all(x > 1 for x in r1.values()), True)
    n_cfg = len(d['SIM1']['eta2']) + sum(len(d['SIM%d' % i]['eta2']) for i in (2, 3, 4))
    check_eq('total parameter configurations', n_cfg, 27)
    for i, name in ((2, 'SIM-2 heading noise'), (3, 'SIM-3 smoothing'), (4, 'SIM-4 disruptor')):
        rr = ratios_from(d['SIM%d' % i]['eta2'])
        check_eq('%s: all ratios above unity' % name, all(x > 1 for x in rr.values()), True)


# ------------------------------------------------- 9. supplementary derived
def supplementary():
    print('\n9. Supplementary Tables S2 and S7')
    d = json.load(open('data/supplementary_derived.json'))
    exp = {'circle': (0.89, 20.9), 'square': (0.90, 9.2),
           'lemniscate': (0.77, 6.9), 'zigzag': (0.44, 3.2)}
    got = {r['traj']: r for r in d.get('S2_table_summary', [])}
    check_eq('Table S2 covers four trajectories', sorted(got), sorted(exp))
    for tj, (r2, dl) in exp.items():
        if tj not in got:
            RESULTS.append(False); continue
        check('S2 %s R^2 (p >= 15%%)' % tj, got[tj]['r2_p_ge_15'], r2, 0.005)
        check('S2 %s dRMSE N=5->200' % tj, got[tj]['delta_rmse_5_to_200_pct_p_ge_15'], dl, 0.05, '%')
    zz = got.get('zigzag', {}).get('delta_rmse_full_range_pct')
    if zz:
        check('S2 zigzag full-range low', zz[0], -2.7, 0.05, '%')
        check('S2 zigzag full-range high', zz[1], 4.3, 0.05, '%')
    check('S7 optimal-performance decomposition residual',
          d['S7_max_abs_residual'], 0.0084, 0.0002, ' m')
    check('S7 same-speed factorial residual (max)',
          d['S7_same_speed_max_abs_residual'], 0.0888, 0.0002, ' m')


def main():
    print('=' * 78)
    print('Reproduction of manuscript-reported derived statistics')
    print('=' * 78)
    for fn in (table1, ratios, mc_precision, rankings, s11, vstar,
               model, sensitivity, supplementary):
        try:
            fn()
        except Exception as exc:                     # keep going; report at the end
            RESULTS.append(False)
            print('  [FAIL] %s raised %s: %s' % (fn.__name__, type(exc).__name__, exc))
    n, ok = len(RESULTS), sum(RESULTS)
    print('\n' + '=' * 78)
    print('%d / %d checks passed%s' % (ok, n, '' if ok == n else '  <-- FAILURES PRESENT'))
    print('=' * 78)
    return 0 if ok == n else 1


if __name__ == '__main__':
    sys.exit(main())
