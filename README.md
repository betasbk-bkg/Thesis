# Speed Over Strategy — simulation code and data

Engine, experiment runners, archived results, and analysis scripts for
"Speed Over Strategy: Why Agent Velocity Dominates Aggregation Method in Crowd-Sourced Continuous Control" (Scientific Reports, under revision).

Archived release: https://doi.org/10.5281/zenodo.22009351 (v1.1.0). The concept DOI https://doi.org/10.5281/zenodo.19413802 always resolves to the latest version.

## Layout
- `simulation_main.py` — simulation engine (trajectories, participant model, voting, aggregation, control loop). Seeding is deterministic but campaign-specific; each runner documents its own seed map (see below).
- `experiments/` — runners: `method_comparison.py` (E1 speed×method factorial, 2,160 runs), `revision_sims.py` (SIM-1..4 sensitivity, 11,340 runs), `zigzag_onepass_runner.py` (corrected zigzag metric), `sim5_policy_completion.py`.
- `data/` — archived results (all MC = 15): `paper_final_mc15.json` (unified E1e/E2e/E2f/E3d), `E2_proper_results.json`, `E3_supplement_proper.json`, `method_comparison_results.json`, sensitivity/zigzag/policy JSONs, `model_refit120_results.json`.
- `analysis/` — `s1_vstar.py` (optimal speed per condition; Table S1), `model_refit120.py` (predictive-model fit on the 120-record training set; five-fold cross-validation for both model forms; also regenerates Figure 5), `regenerate_figures.py` (Figures 1–4 and 6 from the archives; Figure 5 is produced by `model_refit120.py`).
- `legacy/` — superseded development scripts kept for provenance (see `legacy/PROVENANCE.md`).

## Script-to-result mapping
| Manuscript item | Script | Data |
|---|---|---|
| Fig. 1 | analysis/regenerate_figures.py (data from experiments/method_comparison.py) | data/method_comparison_results.json |
| Table 1 (ANOVA) | analysis/e1_anova.py | data/e1_anova_v2.json |
| Table S1 (optimal speed) | analysis/s1_vstar.py | data/s1_vstar.json |
| Table S3b (trajectory geometry) | simulation_main.py (trajectory classes) | — |
| Tables S4–S6 (sensitivity configuration, delay optima, variance decomposition) | experiments/revision_sims.py | data/revision_sims_results.json |
| Table S10 (realized adversarial fractions) | simulation_main.py (`round(N*p)` convention) | — |
| Supplementary Fig. S1 | rendered from the archived ceiling-effect data; not produced by a released script | data/paper_final_mc15.json, data/zigzag_onepass_e2f.json |
| Table S9 (post-hoc) | analysis/s9_posthoc.py | data/s9_posthoc.json |
| Table S2 (ceiling fits, circle/square), Table S7 (both residual definitions) | analysis/make_supplementary.py | data/supplementary_derived.json |
| Table S3, Fig. 5 | analysis/model_refit120.py | data/model_refit120_results.json |
| Table S8 (held-out) | analysis/model_refit120.py | data/model_refit120_results.json |
| Figs. 2–4 | analysis/regenerate_figures.py | data/E2_proper_results.json, data/E3_supplement_proper.json, data/paper_final_mc15.json |
| Eq. (3), Fig. 5, Tables S3/S8 | analysis/model_refit120.py | data/model_refit120_results.json |
| Fig. 6, Table 2 | experiments/revision_sims.py | data/revision_sims_results.json |
| Zigzag (S2) | experiments/zigzag_onepass_runner.py | data/zigzag_onepass_e2f.json |
| Policy-completion | experiments/sim5_policy_completion.py | data/sim5_2x2_results.json |

## Reproduction
`pip install -r requirements.txt` (numpy, scipy, matplotlib). Analysis scripts run from archived JSONs in seconds. Experiment runners regenerate raw results deterministically: `experiments/method_comparison.py` uses a stable per-method seed salt (fixed=1000, majority=2000, quadratic=3000; ~8 min) and stores per-run RMSE lists. `experiments/run_E2_E3_proper.py` regenerates the E2 speed grid (seed = i*997 + 10v + 100p) and the three added E3 adversarial ratios (seed = i*31 + N + 100p); spot checks reproduce the archived means bit-exactly. The three original E3 ratios (10/15/30%) in `paper_final_mc15.json` are frozen archives from the earlier characterization run. The engine is unchanged, but the seed map used by that run is not recorded and its runner is not included, so those cells are provided as archives rather than as reproducible outputs; re-simulation under the conventions documented here reproduces them only up to Monte Carlo noise. The two-way ANOVA table is regenerated from the per-run archive into `data/e1_anova_v2.json`.
