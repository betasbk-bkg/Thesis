"""Supplementary Table S11 - speed-range sensitivity of the speed-to-method eta^2 ratio.

Recomputes the two-way ANOVA (Speed x Method) of the E1 factorial on restricted
speed sub-ranges, from the run-level archive data/method_comparison_results.json
(144 cells x MC = 15).  The final column repeats the analysis with the
consensus-scaled policy excluded, i.e. on the two fixed-magnitude rules only.

The 1.0-5.0 rows reproduce Table 1 (circle block) and its square-block summary.

Output: data/table_s11_range_sensitivity.json  (+ CSV next to it)
"""
import json, csv, itertools
import numpy as np

RAW = json.load(open('data/method_comparison_results.json'))['raw_results']
SPEEDS_ALL = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
RANGES = [('1.0-5.0', SPEEDS_ALL), ('1.5-2.5', [1.5, 2.0, 2.5]), ('3.0-4.0', [3.0, 3.5, 4.0])]
METHODS3 = ['fixed', 'majority', 'quadratic']
METHODS2 = ['fixed', 'majority']          # fixed-magnitude rules only
TRAJ = ['circle', 'square']
TROLL = [0.05, 0.20, 0.40]                # legacy key name; = adversarial ratio p


def cell(traj, tr, v, m):
    k = "%s_tr%.2f_v%s_%s" % (traj, tr, v, m)
    if k not in RAW:
        k = "%s_tr%s_v%s_%s" % (traj, tr, v, m)
    return RAW[k]['rmses']


def two_way_eta2(traj, tr, speeds, methods):
    """Balanced two-way ANOVA on raw run-level RMSE; returns eta^2 (% of total SS)."""
    y = np.array([cell(traj, tr, v, m) for v in speeds for m in methods], dtype=float)
    n = y.shape[1]
    S, M = len(speeds), len(methods)
    grand = y.mean()
    cm = y.mean(axis=1).reshape(S, M)
    ss_tot = ((y - grand) ** 2).sum()
    ss_s = n * M * ((cm.mean(axis=1) - grand) ** 2).sum()
    ss_m = n * S * ((cm.mean(axis=0) - grand) ** 2).sum()
    ss_cells = n * ((cm - grand) ** 2).sum()
    ss_i = ss_cells - ss_s - ss_m
    ss_e = ss_tot - ss_cells
    return [100 * x / ss_tot for x in (ss_s, ss_m, ss_i, ss_e)]


def main():
    rows = []
    for traj, tr in itertools.product(TRAJ, TROLL):
        for label, speeds in RANGES:
            e3 = two_way_eta2(traj, tr, speeds, METHODS3)
            e2 = two_way_eta2(traj, tr, speeds, METHODS2)
            rows.append({
                'trajectory': traj,
                'adversarial': '%d%%' % round(tr * 100),
                'speed_range': label,
                'eta2_speed': round(e3[0], 2),
                'eta2_method': round(e3[1], 2),
                'eta2_speed_x_method': round(e3[2], 2),
                'ratio': round(e3[0] / e3[1], 2),
                'ratio_fixed_majority_only': round(e2[0] / e2[1], 1),
            })

    sub = [r for r in rows if r['speed_range'] != '1.0-5.0']
    below = [r for r in sub if r['ratio'] < 1.0]
    summary = {
        'n_subrange_combinations': len(sub),
        'n_with_method_exceeding_speed': len(below),
        'min_ratio': min(r['ratio'] for r in sub),
        'fixed_majority_only_range_for_those': [
            min(r['ratio_fixed_majority_only'] for r in below),
            max(r['ratio_fixed_majority_only'] for r in below)],
        'full_range_all_above_unity': all(
            r['ratio'] > 1 for r in rows if r['speed_range'] == '1.0-5.0'),
    }

    json.dump({'rows': rows, 'summary': summary},
              open('data/table_s11_range_sensitivity.json', 'w'), indent=1)
    with open('data/table_s11_range_sensitivity.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    hdr = ('trajectory', 'adv', 'speed range', 'eta2_S', 'eta2_M', 'eta2_SxM', 'ratio', 'F+M only')
    print('%-11s %-5s %-9s %8s %8s %9s %8s %10s' % hdr)
    for r in rows:
        print('%-11s %-5s %-9s %8.2f %8.2f %9.2f %8.2f %10.1f' % (
            r['trajectory'], r['adversarial'], r['speed_range'], r['eta2_speed'],
            r['eta2_method'], r['eta2_speed_x_method'], r['ratio'],
            r['ratio_fixed_majority_only']))
    print('\nsummary:', json.dumps(summary))
    print('saved data/table_s11_range_sensitivity.json / .csv')


if __name__ == '__main__':
    main()
