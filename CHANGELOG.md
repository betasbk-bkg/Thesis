# Changelog

## v1.1.2

- `analysis/regenerate_figures.py`: axis label `Number of agents N` -> `Number of participants N` (Fig. 4);
  Fig. 6b panel title neutralised (`Speed leverage collapses as delay vanishes` -> `Ratio versus RMSE span`);
  panel labels `(a)`/`(b)` set in bold per journal figure guidance.
- `analysis/model_refit120.py`: panel labels `(a)`/`(b)` set in bold (Fig. 5).
- `analysis/figS1_supplementary.py`: added. Supplementary Figure S1 is now produced by a released script
  (previously rendered ad hoc from the archived ceiling-effect data); axis label uses `participants`.
- `figures/`: Fig. 1, 3, 4, 5, 6 and FigS1_ceiling.png regenerated. Fig. 2 unchanged (pixel-identical).
- `README.md`: script-to-result mapping updated; the Supplementary Fig. S1 exception removed.
- No data files changed; no reported statistic changes.

### Reproduction packaging (added before release)
- `analysis/table_s11_range_sensitivity.py` — regenerates Supplementary Table S11 (restricted speed sub-ranges) from the run-level E1 archive; all 18 rows reproduce exactly.
- `analysis/reproduce_reported_statistics.py` — recomputes every derived statistic reported in the manuscript and checks it against the printed value (99 checks).
- `reproduce_all.py` — single-command driver: environment check, analyses, tables, figures, verification, PASS/FAIL summary.
- `analysis/make_supplementary.py` — Table S2 ceiling fits extended from circle/square to all four trajectories (lemniscate from the E2f archive, zigzag from the one-pass archive) and a `S2_table_summary` block matching Supplementary Table S2.
- `experiments/revision_sims.py` — `validation_gate()` now uses the exact E1 seed formula and checks run-level RMSE bit-exactly instead of comparing a differently seeded run within Monte-Carlo tolerance.
- `simulation_main.py` — running the engine directly no longer launches the development-era campaign; that runner moved to `legacy/development_full_runner.py`.
- `analysis/reproduce_reported_statistics.py` — expected values are labelled `expected` rather than `paper`, and the Abstract's median is checked on its actual basis (the eta^2 values as printed in Table 1) with the full-precision value reported alongside for reconciliation with Supplementary Table S11.
- `README.md` — rounding-basis note for the reported summary statistics; copy-pasteable command block, script-to-result rows for Table S11 and the verification script, and notes on the legacy `troll_ratio` field name, the frozen historical E3 archives and the tested environment.

## v1.1.1 (2026-08) — Documentation release
- README: corrected the script mapping for Supplementary Figure S1, which is rendered from the
  archived ceiling-effect data and is not produced by `analysis/regenerate_figures.py`.
- Delay terminology standardised to "state-observation delay" in figure labels and comments,
  matching the manuscript.
- `analysis/regenerate_figures.py`: default output directory is now `figures/`, matching the
  repository layout and `analysis/model_refit120.py`.
- No change to the engine, the archived data, or any reported result.

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
