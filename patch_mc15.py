"""
MC=15 통일 패치
1) method_comparison_results.json에서 Fixed 데이터 → E1e 대체
2) E3d를 MC=15로 재실행
3) paper_fullscale_results.json 업데이트

Usage: 
  paper_fullscale_results.json과 method_comparison_results.json을
  같은 폴더에 놓고 실행:
  python3 patch_mc15.py

Output: paper_final_mc15.json (통합 최종 결과)
"""
import numpy as np
import json
import time
from scipy.optimize import curve_fit
from scipy import stats as sp_stats

# ====================================================================
# 1) 파일 로드
# ====================================================================
print("=" * 60)
print("MC=15 통일 패치")
print("=" * 60)

with open('paper_fullscale_results.json', 'r') as f:
    full = json.load(f)

with open('method_comparison_results.json', 'r') as f:
    mcomp = json.load(f)

print(f"  paper_fullscale loaded: {full['metadata']['timestamp']}")
print(f"  method_comparison loaded: {mcomp['metadata']['timestamp']}")

# ====================================================================
# 2) E1e 대체: method_comparison의 Fixed 데이터 추출
# ====================================================================
print("\n--- E1e replacement from method_comparison (Fixed, MC=15) ---")

e1e_new = {}
mc_raw = mcomp['raw_results']

# method_comparison key format: "circle_tr0.05_v1.0_fixed"
# E1e key format:               "circle_tr0.05_v1.0"
replaced = 0
for key, val in mc_raw.items():
    if '_fixed' in key:
        e1e_key = key.replace('_fixed', '')
        e1e_new[e1e_key] = {
            'rmse_mean': val['rmse_mean'],
            'rmse_std': val['rmse_std'],
            'rmse_ci95': val['rmse_ci95'],
            'mc_runs': mcomp['config']['MC'],
        }
        replaced += 1

print(f"  Extracted {replaced} conditions from method_comparison (Fixed)")
print(f"  Original E1e had {len(full['e1e_results'])} conditions (MC=10)")
print(f"  New E1e has {len(e1e_new)} conditions (MC=15)")

# 검증: 값이 크게 안 달라지는지
print("\n  Spot check (old MC=10 vs new MC=15):")
for check_key in ['circle_tr0.20_v2.0', 'circle_tr0.40_v5.0', 'square_tr0.05_v1.0']:
    old = full['e1e_results'].get(check_key, {}).get('rmse_mean', 'N/A')
    new = e1e_new.get(check_key, {}).get('rmse_mean', 'N/A')
    if isinstance(old, float) and isinstance(new, float):
        diff = abs(old - new) / old * 100
        print(f"    {check_key}: {old:.4f} → {new:.4f} (diff {diff:.1f}%)")
    else:
        print(f"    {check_key}: {old} → {new}")

# ====================================================================
# 3) E3d 재실행 (MC=15)
# ====================================================================
print("\n--- E3d re-run with MC=15 ---")

# 엔진 (paper_fullscale.py 동일)
DT=1/60; MSPD=5.0; SMOOTH=0.2; WIN=0.3; DELAY_F=26
DUR=65.0; FRAMES=int(DUR/DT); LOOK=2.0; VOTE_INT=int(WIN/DT)
S2=np.sqrt(2)/2
DIRS=np.array([[1,0],[S2,S2],[0,1],[-S2,S2],[-1,0],[-S2,-S2],[0,-1],[S2,-S2]])
DIR_ANGLES=np.degrees(np.arctan2(DIRS[:,1],DIRS[:,0]))%360

def angle_to_dir(angles):
    a=angles%360; diffs=np.abs(DIR_ANGLES[None,:]-a[:,None])
    diffs=np.minimum(diffs,360-diffs); return np.argmin(diffs,axis=1)

class Circle:
    def __init__(s,R=10): s.R=R; s.circ=2*np.pi*R
    def closest(s,p):
        t=np.arctan2(p[1],p[0]); cp=s.R*np.array([np.cos(t),np.sin(t)])
        return cp,(t%(2*np.pi))*s.R
    def at(s,arc): t=arc/s.R; return s.R*np.array([np.cos(t),np.sin(t)])
    def start(s): return np.array([s.R,0.])

def gen_votes(ia, pa, tr, N, rng):
    nt=round(N*tr); nt=min(nt,N); rem=N-nt
    na=round(rem*0.7368); ns=round(rem*0.2105); no=rem-na-ns
    if no<0: na+=no; no=0
    angs=np.empty(na+ns+no); i=0
    angs[i:i+na]=ia+rng.uniform(-3,3,na); i+=na
    diff=ia-pa
    if diff>180: diff-=360
    if diff<-180: diff+=360
    if ns>0: angs[i:i+ns]=pa+diff*(1-rng.uniform(0.2,0.5,ns)); i+=ns
    if no>0: angs[i:i+no]=ia+rng.uniform(-30,30,no); i+=no
    v=angle_to_dir(angs[:i])
    tv=rng.integers(0,8,nt) if nt>0 else np.array([],dtype=int)
    return np.concatenate([v,tv])

def simulate(traj, N_ag, tr, seed, speed_override=None):
    rng=np.random.default_rng(seed)
    pos=traj.start(); vel=np.zeros(2); pos_hist=[pos.copy()]
    pa=0.; cd=np.array([1.,0.]); cg=0.5
    V=speed_override if speed_override is not None else MSPD
    errs=np.empty(FRAMES)
    for f in range(FRAMES):
        if f%VOTE_INT==0:
            di=max(0,len(pos_hist)-1-DELAY_F); dp=pos_hist[di]
            _,arc=traj.closest(dp); lap=traj.at(arc+LOOK)
            idir=lap-dp; n=np.linalg.norm(idir)
            if n>1e-10: idir/=n
            ia=np.degrees(np.arctan2(idir[1],idir[0]))
            votes=gen_votes(ia,pa,tr,N_ag,rng); pa=ia
            bl=DIRS[votes].mean(axis=0); cg=np.linalg.norm(bl)
            cd=bl/cg if cg>1e-10 else np.array([1.,0.])
        tv=cd*V
        vel+=SMOOTH*(tv-vel); pos=pos+vel*DT; pos_hist.append(pos.copy())
        cp,_=traj.closest(pos); errs[f]=np.linalg.norm(pos-cp)
    return float(np.sqrt(np.mean(errs**2)))

c = Circle()
MC = 15
conditions = [
    ("v=5.0_N=35_tr=25%",   35, 0.25, 5.0),
    ("v=2.0_N=35_tr=25%",   35, 0.25, 2.0),
    ("v=3.0_N=80_tr=15%",   80, 0.15, 3.0),
    ("v=1.5_N=120_tr=35%", 120, 0.35, 1.5),
    ("v=4.0_N=60_tr=10%",   60, 0.10, 4.0),
    ("v=2.5_N=45_tr=45%",   45, 0.45, 2.5),
]

e3d_new = {}
for label, N, tr, v in conditions:
    rmses = [simulate(c, N, tr, seed=i*777+N, speed_override=v) for i in range(MC)]
    e3d_new[label] = {
        'rmse_mean': round(np.mean(rmses), 4),
        'rmse_std': round(np.std(rmses), 4),
        'rmse_ci95': round(1.96*np.std(rmses)/np.sqrt(MC), 4),
        'mc_runs': MC,
    }
    old_val = full['e3d_results'].get(label, {}).get('rmse_mean', 'N/A')
    print(f"  {label}: {old_val} → {e3d_new[label]['rmse_mean']} (MC=15)")

# ====================================================================
# 4) 모델 재핏 (새 E1e 데이터 기반)
# ====================================================================
print("\n--- Model refit with MC=15 data ---")

points = []
# E1e (new, MC=15) — circle only
for key, row in e1e_new.items():
    parts = key.split('_')
    if parts[0] != 'circle': continue
    tr = float(parts[1].replace('tr',''))
    v = float(parts[2].replace('v',''))
    points.append((v, 150, tr, row['rmse_mean']))

# Existing N sweep (circle, v=5.0)
existing_n = {
    (0.05,5):0.819,(0.05,10):0.815,(0.05,25):0.807,(0.05,50):0.810,(0.05,100):0.798,(0.05,200):0.810,
    (0.20,5):0.935,(0.20,10):0.909,(0.20,25):0.833,(0.20,50):0.807,(0.20,100):0.819,(0.20,200):0.817,
    (0.40,5):1.135,(0.40,10):0.977,(0.40,25):0.903,(0.40,50):0.831,(0.40,100):0.837,(0.40,200):0.821,
}
for (tr,N),rmse in existing_n.items():
    points.append((5.0, N, tr, rmse))

# E2e new trolls (circle)
for key, row in full['e2e_results'].items():
    parts = key.split('_')
    if parts[0] != 'circle': continue
    tr = float(parts[1].replace('tr',''))
    N = int(parts[2].replace('N',''))
    points.append((5.0, N, tr, row['rmse_mean']))

data = np.array(points)
v, N, p, rmse = data[:,0], data[:,1], data[:,2], data[:,3]

def model_mul(X, a0, a1, a2, a3):
    v, N, p = X
    return (a0 + a1*v + a2*v**2) * (1 + a3*p/np.sqrt(N))

popt, _ = curve_fit(model_mul, (v,N,p), rmse, p0=[0.5,-0.2,0.06,1.0])
pred = model_mul((v,N,p), *popt)
r2 = 1 - np.sum((rmse-pred)**2)/np.sum((rmse-np.mean(rmse))**2)
vstar = -popt[1]/(2*popt[2]) if popt[2]>0 else None

print(f"  Data points: {len(data)}")
print(f"  Multiplicative: R2={r2:.4f}")
print(f"  Coeffs: {[round(x,5) for x in popt]}")
print(f"  v* = {vstar:.2f}" if vstar else "  v* = N/A")

# 5-fold CV
np.random.seed(42)
idx = np.arange(len(data)); np.random.shuffle(idx); fs=len(data)//5
fold_r2s = []
for fold in range(5):
    ti=np.concatenate([idx[:fold*fs],idx[(fold+1)*fs:]]); ei=idx[fold*fs:(fold+1)*fs]
    tr_d,te_d=data[ti],data[ei]
    po,_=curve_fit(model_mul,(tr_d[:,0],tr_d[:,1],tr_d[:,2]),tr_d[:,3],p0=[0.5,-0.2,0.06,1.0])
    pr=model_mul((te_d[:,0],te_d[:,1],te_d[:,2]),*po)
    ss_r=np.sum((te_d[:,3]-pr)**2); ss_t=np.sum((te_d[:,3]-np.mean(te_d[:,3]))**2)
    fold_r2s.append(1-ss_r/ss_t if ss_t>0 else 0)
print(f"  5-fold CV: {np.mean(fold_r2s):.4f} +/- {np.std(fold_r2s):.4f}")

# E3d prediction
print("\n  E3d prediction (MC=15):")
e3d_preds = {}
errs = []
for label, N_val, tr_val, v_val in conditions:
    predicted = model_mul((v_val, N_val, tr_val), *popt)
    actual = e3d_new[label]['rmse_mean']
    err = abs(predicted-actual)/actual*100
    errs.append(err)
    e3d_preds[label] = {'predicted':round(float(predicted),4),
                        'actual':actual, 'error_pct':round(err,1)}
    print(f"    {label}: pred={predicted:.4f} act={actual:.4f} err={err:.1f}%")
print(f"  Mean error: {np.mean(errs):.1f}%, within 15%: {sum(1 for e in errs if e<15)}/{len(errs)}")

# ====================================================================
# 5) 최종 JSON 생성
# ====================================================================
print("\n--- Building final JSON ---")

full['e1e_results'] = e1e_new
full['e3d_results'] = e3d_new
full['analysis']['model_results']['Multiplicative'] = {
    'coeffs': [float(x) for x in popt],
    'r2': float(r2),
    'mae': float(np.mean(np.abs(rmse-pred))),
}
full['analysis']['cv_results']['Multiplicative'] = {
    'r2_mean': float(np.mean(fold_r2s)),
    'r2_std': float(np.std(fold_r2s)),
    'fold_r2s': [float(x) for x in fold_r2s],
}
full['analysis']['e3d_predictions'] = e3d_preds
full['analysis']['n_data_points'] = len(data)

full['metadata']['mc_unified'] = 15
full['metadata']['patch_note'] = 'E1e replaced from method_comparison (MC=15), E3d re-run MC=15, model refit'
full['metadata']['patch_timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')

outfile = 'paper_final_mc15.json'
with open(outfile, 'w') as f:
    json.dump(full, f, indent=2, default=str)

# ====================================================================
# 6) MC 통일 확인
# ====================================================================
print("\n" + "=" * 60)
print("MC VERIFICATION")
print("=" * 60)
checks = {
    'E2e': full['e2e_results'],
    'E2f': full['e2f_results'],
    'E1e': full['e1e_results'],
    'E3d': full['e3d_results'],
}
for name, results in checks.items():
    sample = list(results.values())[0]
    mc = sample.get('mc_runs', 'unknown')
    print(f"  {name}: {len(results)} conditions, MC={mc}")

print(f"\n  Model (MC=15 data): R2={r2:.4f}, v*={vstar:.2f}")
print(f"  5-fold CV: {np.mean(fold_r2s):.4f}")
print(f"  E3d error: {np.mean(errs):.1f}%")
print(f"\n  Saved to: {outfile}")
print(f"  Done.")
