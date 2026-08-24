# Legacy scripts (provenance record — not part of the reproduction pipeline)

- `paper_fullscale.py`: development-era full-scale runner (MC=8). Its output JSON is not retained.
- `patch_mc15.py`: the 2026-02-25 unification patch that (1) replaced E1e with the MC=15 method-comparison data, (2) re-ran E3d at MC=15, producing `paper_final_mc15.json`. Its embedded model fit used a 78-condition development set that included 18 conditions from the superseded MC=8 run; that fit is superseded by `analysis/model_refit120.py`, which refits on the complete n=120 MC=15 training set. Kept for audit trail only; it does not run without the (unretained) MC=8 JSON.
