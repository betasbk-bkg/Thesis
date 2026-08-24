#!/usr/bin/env python3
"""model_refit120.py — Predictive-model refit on the final unified training set.
Training set: the complete E2+E3 circle characterization data at MC=15 (n=120):
E2 speed grid (6 adversarial ratios x 8 speeds, N=150) + E3 crowd sweeps (6 ratios x 12 N, v=5.0;
3 ratios from E3_supplement_proper.json, 3 from paper_final_mc15.json e2e_results).
Outputs: refit coefficients, training/CV statistics, held-out E5 (e3d, MC=15) predictions,
and Figure 5. Supersedes the development-era 78-condition fit (see CHANGELOG)."""
import json
import numpy as np
from scipy.optimize import curve_fit

e2 = json.load(open('data/E2_proper_results.json')); e2r = e2.get('results', e2)
mc = json.load(open('data/paper_final_mc15.json'))
sup = json.load(open('data/E3_supplement_proper.json'))['results']
SP = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
NS = [5, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200]
pts = []
for tr in ['0.05', '0.10', '0.15', '0.20', '0.30', '0.40']:
    for v in SP: pts.append((v, 150, float(tr), e2r[f'circle_tr{tr}_v{v}']['rmse_mean']))
for tr in ['0.05', '0.20', '0.40']:
    for N in NS: pts.append((5.0, N, float(tr), sup[f'circle_tr{tr}_N{N}']['rmse_mean']))
for tr in ['0.10', '0.15', '0.30']:
    for N in NS: pts.append((5.0, N, float(tr), mc['e2e_results'][f'circle_tr{tr}_N{N}']['rmse_mean']))
d = np.array(pts); V, N, P, Y = d[:, 0], d[:, 1], d[:, 2], d[:, 3]
assert len(d) == 120

def mul(X, a0, a1, a2, a3):
    v, n, p = X; return (a0 + a1*v + a2*v*v) * (1 + a3*p/np.sqrt(n))
def add(X, a0, a1, a2, a3):
    v, n, p = X; return (a0 + a1*v + a2*v*v) + a3*p/np.sqrt(n)

pm, _ = curve_fit(mul, (V, N, P), Y, p0=[0.5, -0.2, 0.05, 2.0], maxfev=50000)
pa, _ = curve_fit(add, (V, N, P), Y, p0=[0.5, -0.2, 0.05, 2.0], maxfev=50000)
r2 = lambda f, p: 1 - ((Y - f((V, N, P), *p))**2).sum() / ((Y - Y.mean())**2).sum()
idx = np.arange(120); np.random.default_rng(42).shuffle(idx)
def cross_val(f):
    scores = []
    for k in range(5):
        te = idx[k*24:(k+1)*24]; tr_ = np.setdiff1d(idx, te)
        pk, _ = curve_fit(f, (V[tr_], N[tr_], P[tr_]), Y[tr_], p0=[0.5, -0.2, 0.05, 2.0], maxfev=50000)
        yh = f((V[te], N[te], P[te]), *pk)
        scores.append(1 - ((Y[te]-yh)**2).sum() / ((Y[te]-Y[te].mean())**2).sum())
    return scores
cvs = cross_val(mul)
cvs_add = cross_val(add)
import re as _re
e5 = []
for k, vv in mc['e3d_results'].items():
    m = _re.match(r'v=([\d.]+)_N=(\d+)_tr=(\d+)%', k)
    e5.append((float(m.group(1)), int(m.group(2)), float(m.group(3))/100, vv['rmse_mean']))
errs_m = [abs(mul((v, n, p), *pm)-y)/y*100 for v, n, p, y in e5]
errs_a = [abs(add((v, n, p), *pa)-y)/y*100 for v, n, p, y in e5]
tr_err = np.abs(mul((V, N, P), *pm) - Y) / Y * 100
out = {'coeff_mul': [round(float(x), 4) for x in pm], 'coeff_add': [round(float(x), 4) for x in pa],
       'r2_mul': round(float(r2(mul, pm)), 4), 'r2_add': round(float(r2(add, pa)), 4),
       'cv_mean': round(float(np.mean(cvs)), 4), 'cv_std': round(float(np.std(cvs)), 4),
       'cv_mean_add': round(float(np.mean(cvs_add)), 4), 'cv_std_add': round(float(np.std(cvs_add)), 4),
       'vstar_model': round(float(-pm[1]/(2*pm[2])), 3),
       'e5_mul_mean': round(float(np.mean(errs_m)), 1), 'e5_add_mean': round(float(np.mean(errs_a)), 1),
       'e5_mul_within15': int(sum(1 for x in errs_m if x <= 15)),
       'train_err_mean': round(float(tr_err.mean()), 1), 'train_err_median': round(float(np.median(tr_err)), 1)}
json.dump(out, open('data/model_refit120_results.json', 'w'), indent=1)
print(out)

# Regenerate Figure 5
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
yh = mul((V, N, P), *pm)
ax[0].scatter(Y, yh, s=22, alpha=0.6, label='Training (n = 120)')
e5y = [r[3] for r in e5]; e5p = [mul((v, n, p), *pm) for v, n, p, _ in e5]
ax[0].scatter(e5y, e5p, marker='*', s=140, color='#d62728', zorder=5, label='Held-out E5 (n = 6)')
lim = [0.15, 1.25]
ax[0].plot(lim, lim, 'k--', lw=1); ax[0].set_xlim(lim); ax[0].set_ylim(lim)
ax[0].set_xlabel('Actual RMSE (m)'); ax[0].set_ylabel('Predicted RMSE (m)')
ax[0].text(0.05, 0.92, f'$R^2$ = {out["r2_mul"]:.3f}', transform=ax[0].transAxes)
ax[0].legend(frameon=False, fontsize=9, loc='lower right'); ax[0].grid(alpha=0.25)
ax[1].hist(tr_err, bins=24, alpha=0.75, edgecolor='white')
for e in errs_m: ax[1].axvline(e, color='#d62728', lw=1.2, alpha=0.8)
ax[1].set_xlabel('Prediction error (%)'); ax[1].set_ylabel('Count')
ax[1].grid(alpha=0.25)
for a, lab in zip(ax, ['$\\bf{(a)}$', '$\\bf{(b)}$']): a.set_title(lab, loc='left', fontsize=11)
plt.tight_layout(); plt.savefig('figures/Fig5_refit120.png', dpi=300, bbox_inches='tight')
print('Fig5 saved')
