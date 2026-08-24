"""Two-way ANOVA (Speed x Method) per trajectory x adversarial ratio.
Input:  data/method_comparison_results.json (per-run RMSE lists, MC=15)
Output: data/e1_anova_v2.json  (SS, df, F, eta^2 for Table 1)
"""
import json, numpy as np
from itertools import product
SPEEDS=[1.0,1.5,2.0,2.5,3.0,3.5,4.0,5.0]; METHODS=['fixed','majority','quadratic']
raw=json.load(open('data/method_comparison_results.json'))['raw_results']
def anova(tj,tr):
    cells={(v,m):np.array(raw[f"{tj}_tr{tr:.2f}_v{v:.1f}_{m}"]['rmses']) for v,m in product(SPEEDS,METHODS)}
    n=15; allv=np.concatenate(list(cells.values())); G=allv.mean(); N=n*24
    SS_e=sum(len(c)*c.std()**2 for c in cells.values())
    SS_cell=sum(n*(c.mean()-G)**2 for c in cells.values())
    SS_s=sum(n*3*(np.mean([cells[(v,m)].mean() for m in METHODS])-G)**2 for v in SPEEDS)
    SS_m=sum(n*8*(np.mean([cells[(v,m)].mean() for v in SPEEDS])-G)**2 for m in METHODS)
    SS_i=SS_cell-SS_s-SS_m; SS_T=SS_cell+SS_e
    F=[SS_s/7/(SS_e/(N-24)), SS_m/2/(SS_e/(N-24)), SS_i/14/(SS_e/(N-24))]
    return {'SS':[round(x,3) for x in (SS_s,SS_m,SS_i,SS_e)],
            'F':[int(round(x)) for x in F],
            'eta2_pct':[round(x/SS_T*100,1) for x in (SS_s,SS_m,SS_i,SS_e)],
            'df':[7,2,14,N-24]}
out={f"{tj}_{int(tr*100)}":anova(tj,tr) for tj in ['circle','square'] for tr in [0.05,0.20,0.40]}
json.dump(out,open('data/e1_anova_v2.json','w'),indent=1)
print("saved data/e1_anova_v2.json")
for k,v in out.items(): print(k, v['eta2_pct'])
