"""Supplementary derivation script.
S2: crowd-size ceiling fits RMSE(N)=a+b/sqrt(N) from current E3 archives
    (circle/square: paper_final_mc15 e2e + E3_supplement; zigzag/lemniscate: one-pass archive where available).
S7: policy-completion optimal-performance decomposition residual, plus the same-speed
    2x2 factorial residual, from data/sim5_2x2_results.json.
Output: data/supplementary_derived.json
"""
import json, numpy as np
from scipy.optimize import curve_fit
out={}
# ---- S2 ceiling fits (current data) ----
_pf=json.load(open('data/paper_final_mc15.json'))
sup=json.load(open('data/E3_supplement_proper.json'))['results']
zz=json.load(open('data/zigzag_onepass_e2f.json'))['results']   # one-pass metric
allc={}
allc.update(_pf['e2e_results'])   # circle / square
allc.update(sup)                  # added E3 adversarial ratios
allc.update(_pf['e2f_results'])   # lemniscate (and legacy zigzag, superseded below)
allc.update(zz)                   # zigzag, one-pass metric (overrides legacy)
Ns=[5,10,15,20,25,30,40,50,75,100,150,200]
def f(N,a,b): return a+b/np.sqrt(N)
fits=[]
for tj in ['circle','square','lemniscate','zigzag']:
    for tr in [0.05,0.10,0.15,0.20,0.30,0.40]:
        xs,ys=[],[]
        for N in Ns:
            k=f"{tj}_tr{tr:.2f}_N{N}"
            if k in allc: xs.append(N); ys.append(allc[k]['rmse_mean'])
        if len(xs)>=6:
            (a,b),_=curve_fit(f,np.array(xs),np.array(ys),p0=[0.8,0.5])
            ss=1-np.sum((np.array(ys)-f(np.array(xs),a,b))**2)/np.sum((np.array(ys)-np.mean(ys))**2)
            fits.append({'traj':tj,'troll':tr,'a':round(float(a),4),'b':round(float(b),4),'r2':round(float(ss),4),'n_points':len(xs)})
out['S2_ceiling_fits']=fits
# Supplementary Table S2 summary rows: R^2 and Delta-RMSE(N=5->200) averaged over p >= 15%.
s2sum=[]
for tj in ['circle','square','lemniscate','zigzag']:
    r2s=[];dl=[];dall=[]
    for tr in [0.05,0.10,0.15,0.20,0.30,0.40]:
        xs=[N for N in Ns if f"{tj}_tr{tr:.2f}_N{N}" in allc]
        if len(xs)<6: continue
        ys=np.array([allc[f"{tj}_tr{tr:.2f}_N{N}"]['rmse_mean'] for N in xs],float)
        xs=np.array(xs,float)
        (a,b),_=curve_fit(f,xs,ys,p0=[0.8,0.5])
        ss=1-np.sum((ys-f(xs,a,b))**2)/np.sum((ys-np.mean(ys))**2)
        d=100*(ys[0]-ys[-1])/ys[0]; dall.append(d)
        if tr>=0.15: r2s.append(ss); dl.append(d)
    s2sum.append({'traj':tj,'r2_p_ge_15':round(float(np.mean(r2s)),2),
                  'delta_rmse_5_to_200_pct_p_ge_15':round(float(np.mean(dl)),1),
                  'delta_rmse_full_range_pct':[round(float(min(dall)),1),round(float(max(dall)),1)]})
out['S2_table_summary']=s2sum
# ---- S7 policy-completion decomposition ----
# Cells: direction rule (vector mean vs majority) x gain law (constant V vs gamma^2 V).
# Each cell is summarised by its minimum RMSE over the speed grid (i.e. performance at that
# policy's own optimum), matching the value reported in Supplementary Table S7. The residual
# below is therefore an optimal-performance decomposition residual, not a factorial
# interaction residual: the gain law shifts each policy's optimum along the speed axis. The
# same-speed 2x2 factorial residual is computed separately and is larger.
# Residual = min(both) - [min(direction-only) + min(gain-only) - min(base)]
try:
    s5 = json.load(open('data/sim5_2x2_results.json'))
    by = {}
    for key, cell in s5.items():
        if not key.startswith('S5_'):
            continue
        parts = key.split('_')
        tr = parts[1]
        policy = '_'.join(parts[2:-1])
        by.setdefault((tr, policy), []).append(cell['rmse_mean'])
    S7 = []
    for tr in sorted({k[0] for k in by}):
        m = {p: min(by[(tr, p)]) for p in ('fixed', 'majority', 'quadratic', 'maj_quad') if (tr, p) in by}
        if len(m) < 4:
            continue
        r = m['maj_quad'] - (m['majority'] + m['quadratic'] - m['fixed'])
        S7.append({'troll': tr, 'base_fixed': round(m['fixed'], 4),
                   'direction_only_majority': round(m['majority'], 4),
                   'gain_only_quadratic': round(m['quadratic'], 4),
                   'both_maj_quad': round(m['maj_quad'], 4),
                   'decomposition_residual': round(r, 5)})
    out['S7_decomposition_residuals'] = S7
    if S7:
        out['S7_max_abs_residual'] = round(max(abs(x['decomposition_residual']) for x in S7), 5)
    # Same-speed 2x2 factorial residual, for contrast with the decomposition above.
    speeds = sorted({float(k.rsplit('_v', 1)[1]) for k in s5 if k.startswith('S5_')})
    same = []
    for tr in sorted({k.split('_')[1][2:] for k in s5 if k.startswith('S5_')}):
        for v in speeds:
            try:
                a = s5['S5_tr%s_fixed_v%s' % (tr, v)]['rmse_mean']
                b = s5['S5_tr%s_majority_v%s' % (tr, v)]['rmse_mean']
                c = s5['S5_tr%s_quadratic_v%s' % (tr, v)]['rmse_mean']
                d2 = s5['S5_tr%s_maj_quad_v%s' % (tr, v)]['rmse_mean']
            except KeyError:
                continue
            same.append({'troll': tr, 'speed': v, 'residual': round(d2 - b - c + a, 5)})
    out['S7_same_speed_factorial_residuals'] = same
    if same:
        out['S7_same_speed_max_abs_residual'] = round(max(abs(x['residual']) for x in same), 5)
except Exception as e:
    out['S7_decomposition_residuals'] = 'skip: %s' % e
json.dump(out,open('data/supplementary_derived.json','w'),indent=1)
print("saved data/supplementary_derived.json | S2 fits:", len(fits),
      "| S7 decomposition:", len(out['S7_decomposition_residuals']) if isinstance(out['S7_decomposition_residuals'], list) else out['S7_decomposition_residuals'],
      "| S2 table rows:", len(out['S2_table_summary']),
      "| S7 same-speed max:", out.get('S7_same_speed_max_abs_residual'))
