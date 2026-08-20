"""Post-hoc method comparisons for Supplementary Table S9.
Welch's t per cell, Bonferroni-corrected within cell (3 comparisons),
plus pooled Fixed-vs-Majority contrast per trajectory x ratio.
Input:  data/method_comparison_results.json  Output: data/s9_posthoc.json
"""
import json, numpy as np
from scipy import stats
raw=json.load(open('data/method_comparison_results.json'))['raw_results']
SPEEDS=[1.0,1.5,2.0,2.5,3.0,3.5,4.0,5.0]
out={'cells':[],'pooled':[]}
for tj in ['circle','square']:
    for tr in [0.05,0.20,0.40]:
        for v in SPEEDS:
            g={m:np.array(raw[f"{tj}_tr{tr:.2f}_v{v:.1f}_{m}"]['rmses']) for m in ['fixed','majority','quadratic']}
            row={'traj':tj,'troll':tr,'speed':v}
            for a,b,tag in [('fixed','majority','fm'),('fixed','quadratic','fq'),('majority','quadratic','mq')]:
                t,p=stats.ttest_ind(g[a],g[b],equal_var=False)
                d=(g[a].mean()-g[b].mean())/np.sqrt((g[a].std(ddof=1)**2+g[b].std(ddof=1)**2)/2)
                row[f'p_{tag}_bonf']=min(1.0,float(p)*3); row[f'd_{tag}']=round(float(d),3)
            for m in g: row[f'{m}_mean']=round(float(g[m].mean()),4)
            out['cells'].append(row)
        F=np.concatenate([raw[f"{tj}_tr{tr:.2f}_v{v:.1f}_fixed"]['rmses'] for v in SPEEDS])
        M=np.concatenate([raw[f"{tj}_tr{tr:.2f}_v{v:.1f}_majority"]['rmses'] for v in SPEEDS])
        t,p=stats.ttest_ind(F,M,equal_var=False)
        out['pooled'].append({'traj':tj,'troll':tr,'fixed_mean':round(float(F.mean()),4),
            'majority_mean':round(float(M.mean()),4),'p_welch':float(p),'n_per_group':len(F)})
json.dump(out,open('data/s9_posthoc.json','w'),indent=1)
print("saved data/s9_posthoc.json |", len(out['cells']),"cells,",len(out['pooled']),"pooled")
