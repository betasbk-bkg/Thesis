#!/usr/bin/env python3
"""
regenerate_figures.py — Figures 1–6 regeneration from archived data
===================================================================
Figure generation for "Speed Over Strategy".
Figures 1-4 and 6 are regenerated from the archived datasets so that each
figure maps to this executable file (script-to-result mapping, README).
Figures are rendered WITHOUT embedded titles (captions live in the manuscript).

Requires (repo root): paper_final_mc15.json, E2_proper_results.json,
E3_supplement_proper.json, method_comparison_results.json, revision_sims_results.json.
Usage: python3 regenerate_figures.py [outdir=figures]
"""
import json, re, sys, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = sys.argv[1] if len(sys.argv) > 1 else "figures"
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.size": 11, "axes.labelsize": 12})

mc   = json.load(open("data/paper_final_mc15.json"))
e2   = json.load(open("data/E2_proper_results.json")); e2r = e2.get("results", e2)
sup  = json.load(open("data/E3_supplement_proper.json"))["results"]
raw  = json.load(open("data/method_comparison_results.json"))["raw_results"]
sims = json.load(open("data/revision_sims_results.json"))
SP8  = [1.0,1.5,2.0,2.5,3.0,3.5,4.0,5.0]
SP10 = SP8 + [6.5,8.0]
TR6  = [0.05,0.10,0.15,0.20,0.30,0.40]
def save(name): plt.tight_layout(); plt.savefig(f"{OUT}/{name}", dpi=300, bbox_inches="tight"); plt.close(); print("saved", name)

# ---------- Figure 1 (2-panel: nominal / effective-speed axis) ----------
g2 = np.array([sims["SIM4"]["results"][f"S4_uniform_quadratic_v{v}"]["gamma_sq_mean"] for v in SP8])
curves = {m: [raw[f"circle_tr0.20_v{v}_{m}"]["rmse_mean"] for v in SP8] for m in ["fixed","majority","quadratic"]}
cis    = {m: [raw[f"circle_tr0.20_v{v}_{m}"]["rmse_ci95"] for v in SP8] for m in curves}
style = {"fixed":("o","-","#1f77b4","Fixed velocity"),
         "majority":("s","-","#ff7f0e","Majority vote"),
         "quadratic":("^","-","#2ca02c","Quadratic ($\\gamma^2V$)")}
fig, axes = plt.subplots(1,2,figsize=(11,4.4))
ax = axes[0]
for m,(mk,ls,c,lab) in style.items():
    ax.errorbar(SP8,curves[m],yerr=cis[m],marker=mk,ls=ls,color=c,label=lab,capsize=2,ms=6)
    ax.axvline(SP8[int(np.argmin(curves[m]))],color=c,ls=":",alpha=0.5,lw=1.2)
ax.set_xlabel("Nominal agent speed $V$ (m/s)"); ax.set_ylabel("RMSE (m)")
ax.set_title("$\\bf{(a)}$ Nominal-speed axis",loc="left"); ax.legend(frameon=False,fontsize=9)
ax.set_ylim(0.15,1.05); ax.grid(alpha=0.25)
ax = axes[1]; xq = g2*np.array(SP8)
for m,(mk,ls,c,lab) in style.items():
    x = xq if m=="quadratic" else np.array(SP8)
    ax.errorbar(x,curves[m],yerr=cis[m],marker=mk,ls="-" if m!="quadratic" else "",color=c,label=lab,capsize=2,ms=6)
ax.plot(xq,curves["quadratic"],color="#2ca02c",alpha=0.45)
ax.set_xlabel("Effective speed (m/s): $V$ (Fixed, Majority); $\\gamma^2V$ (Quadratic)")
ax.set_ylabel("RMSE (m)"); ax.set_title("$\\bf{(b)}$ Effective-speed axis",loc="left")
ax.legend(frameon=False,fontsize=9); ax.set_ylim(0.15,1.05); ax.grid(alpha=0.25)
save("Fig1_revised.png")

# ---------- Figure 2 (eta^2 decomposition, circle) ----------
A_ = json.load(open("data/e1_anova_v2.json"))
D = {tr: tuple(A_[f"circle_{int(tr*100)}"]["eta2_pct"][:3]) for tr in (0.05,0.20,0.40)}
RT = {tr: f"{D[tr][0]/D[tr][1]:.0f}\u00d7" for tr in D}
fig, ax = plt.subplots(figsize=(7,4.4)); x = np.arange(3); w = 0.26
S=[D[t][0] for t in D]; M=[D[t][1] for t in D]; I=[D[t][2] for t in D]
ax.bar(x-w,S,w,color="#1f77b4",label="Speed ($\\eta^2$)")
ax.bar(x,  M,w,color="#ff7f0e",label="Method ($\\eta^2$)")
ax.bar(x+w,I,w,color="#2ca02c",label="Speed\u00d7Method ($\\eta^2$)")
for i,t in enumerate(D):
    for dx,val in [(-w,S[i]),(0,M[i]),(w,I[i])]: ax.text(i+dx,val+1.5,f"{val}%",ha="center",fontsize=9)
    ax.text(i-w/2,max(S[i],M[i])+9,RT[t],color="#d62728",fontsize=13,fontweight="bold",ha="center")
ax.set_xticks(x); ax.set_xticklabels(["5%","20%","40%"])
ax.set_xlabel("Adversarial ratio"); ax.set_ylabel("Variance explained ($\\eta^2$, %)")
ax.set_ylim(0,105); ax.legend(frameon=False,fontsize=9); ax.grid(axis="y",alpha=0.25)
save("Fig2_revised.png")

# ---------- Figure 3 (v* across adversarial ratios) ----------
fig, axes = plt.subplots(1,2,figsize=(11,4.4)); cmap = plt.cm.viridis(np.linspace(0,0.85,6))
for ax,traj,title in [(axes[0],"circle","$\\bf{(a)}$ Circle trajectory"),(axes[1],"square","$\\bf{(b)}$ Square trajectory")]:
    for tr,col in zip(TR6,cmap):
        ax.plot(SP8,[e2r[f"{traj}_tr{tr:.2f}_v{v}"]["rmse_mean"] for v in SP8],marker="o",ms=4,color=col,label=f"{tr:.0%}")
    ax.set_xlabel("Agent speed $V$ (m/s)"); ax.set_ylabel("RMSE (m)")
    ax.set_title(title,loc="left"); ax.grid(alpha=0.25)
axes[0].axvline(2.0,color="#d62728",ls="--",lw=1.2)
axes[0].text(2.05,axes[0].get_ylim()[1]*0.92,"$v^*\\approx2.0$",color="#d62728",fontsize=10)
axes[0].legend(frameon=False,fontsize=8,title="Adversarial",title_fontsize=8)
axes[1].text(0.05,0.06,"$v^*\\leq1.0$ m/s (monotonic)",transform=axes[1].transAxes,fontsize=10,
             color="#d62728",bbox=dict(fc="white",ec="#d62728",alpha=0.8))
save("Fig3_revised.png")

# ---------- Figure 4 (crowd-size ceiling, circle, V=5.0; content unchanged) ----------
Ns=[5,10,15,20,25,30,40,50,75,100,150,200]; allc={}
for src in (mc["e2e_results"], sup):
    for k,v in src.items():
        m=re.match(r"circle_tr([\d.]+)_N(\d+)$",k)
        if m: allc[(float(m.group(1)),int(m.group(2)))]=v["rmse_mean"]
fig, ax = plt.subplots(figsize=(7.5,4.6))
for tr,col in zip(TR6,["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#8c564b"]):
    ys=[allc[(tr,N)] for N in Ns]; ax.plot(Ns,ys,marker="o",ms=4,color=col,label=f"p = {tr:.0%}")
    if tr>=0.15:
        A=np.vstack([np.ones(len(Ns)),1/np.sqrt(Ns)]).T
        coef,_,_,_=np.linalg.lstsq(A,np.array(ys),rcond=None)
        Nf=np.linspace(5,200,100); ax.plot(Nf,coef[0]+coef[1]/np.sqrt(Nf),ls="--",color=col,alpha=0.5,lw=1)
ax.set_xlabel("Number of participants $N$"); ax.set_ylabel("RMSE (m)")
ax.legend(frameon=False,fontsize=8,ncol=2); ax.grid(alpha=0.25)
save("Fig4_revised.png")

# ---------- Figure 5: generated by analysis/model_refit120.py (single source of truth) ----------

# ---------- Figure 6 (sensitivity; new) ----------
taus=[0,6,13,26,39,52]; ms_=[round(t/60*1000) for t in taus]
fig, axes = plt.subplots(1,2,figsize=(11,4.4)); ax=axes[0]
for tr,c_,lab in [("0.05","#1f77b4","5%"),("0.2","#ff7f0e","20%"),("0.4","#d62728","40%")]:
    ax.plot(ms_,[sims["SIM1"]["eta2"][f"tau{t}_tr{tr}"]["ratio_speed_method"] for t in taus],marker="o",color=c_,label=f"adversarial {lab}")
ax.axhline(1,color="gray",ls="--",lw=1); ax.set_yscale("log")
ax.set_xlabel("State-observation delay $\\tau$ (ms)"); ax.set_ylabel("$\\eta^2_{speed}\\,/\\,\\eta^2_{method}$")
ax.set_title("$\\bf{(a)}$ Dominance ratio across delay",loc="left"); ax.legend(frameon=False,fontsize=9); ax.grid(alpha=0.25,which="both")
ax=axes[1]
for t,c_ in [(0,"#2ca02c"),(26,"#1f77b4"),(52,"#d62728")]:
    ax.plot(SP10,[sims["SIM1"]["results"][f"S1_tau{t}_tr0.2_fixed_v{v}"]["rmse_mean"] for v in SP10],marker="o",ms=4,color=c_,label=f"$\\tau$ = {round(t/60*1000)} ms")
ax.set_xlabel("Nominal agent speed $V$ (m/s)"); ax.set_ylabel("RMSE (m)")
ax.set_title("$\\bf{(b)}$ Ratio versus RMSE span",loc="left")
ax.legend(frameon=False,fontsize=9); ax.grid(alpha=0.25)
save("Fig6_sensitivity.png")

print("Figures 1-4 and 6 regenerated (Figure 5: analysis/model_refit120.py) to", OUT)
