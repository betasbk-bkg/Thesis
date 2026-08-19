# Changelog

## v1.1.0 (2026-08) — Major-revision release
- Added sensitivity campaign `experiments/revision_sims.py` (SIM-1..4: delay, noise, smoothing, disruptor models; 11,340 runs) and `experiments/sim5_policy_completion.py` (policy-completion metric, 1,440 runs).
- Zigzag metric corrected to first-complete-traversal RMSE (`experiments/zigzag_onepass_runner.py`); full-horizon values retained in data for comparison.
- Model refit on the complete n=120 MC=15 training set (`analysis/model_refit120.py`): coefficients (0.5138, −0.2370, 0.0581, 2.2300), R²=0.988, 5-fold CV 0.987±0.005 (seed 42), held-out E5 4.4% (6/6 within 15%). Supersedes the 78-condition development fit (see `legacy/PROVENANCE.md`).
- `analysis/regenerate_figures.py` regenerates Figures 1–4 and 6 from the archived JSONs (Figure 5 is produced by `analysis/model_refit120.py`).
- Restored the E2/E3 generation runner `experiments/run_E2_E3_proper.py` (bit-exact against the archived E2 grid and the three added E3 ratios).
- `method_comparison.py` v1.1.0: replaced process-dependent `hash(m)` seeding with a stable per-method salt and re-ran E1 (2,160 runs); Table 1, Figures 1–2 and Supplementary Table S9 regenerated from the new archive. Headline ranges are unchanged (speed 46–97% vs. method 2–29%; dominance 1.6–46×).

### Implementation-consistency pass (2026-08-18)
- `experiments/run_E2_E3_proper.py` now uses the same participant allocation as `simulation_main.py`
  (the adversarial count is taken first and the remainder is split among the three non-adversarial
  subtypes), so the vote total is always exactly N. The previous formula could exceed N by one at
  N = 5, p = 30%; that combination is not among the adversarial ratios this runner generates, and
  the archived E2 and added-E3 cells reproduce unchanged after the correction.
- Stale comment in `simulation_main.py` corrected: subtype counts are integer-rounded, so realized
  ratios differ from nominal at small N (tabulated in Supplementary Table S10).
- README: seed description made campaign-specific; figure/table mapping corrected
  (Figure 1 is produced by `analysis/regenerate_figures.py`).

### Final revision pass (2026-08-18)
- Added `analysis/s1_vstar.py`, the generator for Supplementary Table S1. The optimal speed is
  computed as the empirical minimum of RMSE on the tested speed grid, the same estimator used for
  the delay sweep (Table S5), and the parabola vertex is reported alongside it as a secondary check.
  The vertex rule is undefined on the square, where RMSE increases monotonically over the tested
  interval, so the square optimum is reported as a lower-bound censored value.
- `analysis/model_refit120.py` now cross-validates both the additive and the multiplicative form, so
  every figure in Supplementary Table S3 is produced by the released script (the additive 5-fold CV
  standard deviation is 0.0057).
- Source comments and JSON metadata standardised in English throughout.
- Script-to-result mapping updated for the renumbered main-text tables (Table 4 -> Table 2).

### Release verification (2026-08-16)
Fresh extraction into a clean directory: `model_refit120.py` reproduces all statistics and the Figure 5 PNG; `regenerate_figures.py` produces Figures 1–4 and 6; full-grid regeneration with `run_E2_E3_proper.py` matches the archived means bit-exactly for all 96 E2 cells and all 72 added E3 cells (168/168).

## v1.0.0 (2026-02)
- Initial archive: engine, E1–E5 archives unified at MC=15 (`data/paper_final_mc15.json`).
