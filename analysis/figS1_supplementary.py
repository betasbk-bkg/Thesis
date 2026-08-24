#!/usr/bin/env python3
"""
figS1_supplementary.py — Supplementary Figure S1 regeneration from archived data
================================================================================
Trajectory-dependent ceiling effect: RMSE vs crowd size N at 20% adversarial
ratio for the four trajectories (V = 5.0 m/s, MC = 15; zigzag: one-pass metric).
Data: data/E3_supplement_proper.json, data/paper_final_mc15.json (e2f_results),
      data/zigzag_onepass_e2f.json
Usage: python3 analysis/figS1_supplementary.py [outdir=figures]
"""
import json, sys, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = sys.argv[1] if len(sys.argv) > 1 else "figures"
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.size": 11, "axes.labelsize": 12})

sup = json.load(open("data/E3_supplement_proper.json")); sup = sup.get("results", sup)
e2f = json.load(open("data/paper_final_mc15.json"))["e2f_results"]
zz  = json.load(open("data/zigzag_onepass_e2f.json")); zz = zz.get("results", zz)
Ns  = [5, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200]

series = {
 'Circle':            [sup[f"circle_tr0.20_N{N}"]['rmse_mean']     for N in Ns],
 'Square':            [sup[f"square_tr0.20_N{N}"]['rmse_mean']     for N in Ns],
 'Lemniscate':        [e2f[f"lemniscate_tr0.20_N{N}"]['rmse_mean'] for N in Ns],
 'Zigzag (one-pass)': [zz[f"zigzag_tr0.20_N{N}"]['rmse_mean']      for N in Ns],
}
fig, ax = plt.subplots(figsize=(7, 4.4))
for (lab, ys), c in zip(series.items(), ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']):
    ax.plot(Ns, ys, marker='o', ms=4, color=c, label=lab)
ax.set_xlabel('Number of participants $N$'); ax.set_ylabel('RMSE (m)')
ax.set_xscale('log'); ax.legend(frameon=False, fontsize=9); ax.grid(alpha=0.25)
plt.tight_layout(); plt.savefig(f"{OUT}/FigS1_ceiling.png", dpi=300, bbox_inches="tight")
print("saved FigS1_ceiling.png")
