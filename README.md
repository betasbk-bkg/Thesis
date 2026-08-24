# Speed Over Strategy — simulation code and data

Engine, experiment runners, archived results, and analysis scripts for
"Speed Over Strategy: Why Agent Velocity Dominates Aggregation Method in Crowd-Sourced Continuous Control" (Scientific Reports, under revision).

Archived release: https://doi.org/10.5281/zenodo.19413802 — the concept DOI, which always resolves to the latest version. The version archived with the manuscript is release tag **v1.1.2**.

## Quick start

All commands are run **from the repository root**.

```bash
pip install -r requirements.txt      # numpy, scipy, matplotlib

python reproduce_all.py              # analyses + tables + figures + verification
python reproduce_all.py --gate       # additionally re-simulate three archived E1
                                     # cells and check them bit-exactly (~1 min)
```

`reproduce_all.py` runs the steps below and prints a PASS/FAIL summary. To run them
individually:

```bash
# analyses (seconds; read the archived JSONs in data/)
python analysis/e1_anova.py                        # Table 1
python analysis/s1_vstar.py                        # Table S1
python analysis/s9_posthoc.py                      # Table S9
python analysis/make_supplementary.py              # Tables S2, S7
python analysis/table_s11_range_sensitivity.py     # Table S11
python analysis/model_refit120.py                  # Tables S3, S8, Eq. (3), Figure 5

# figures
python analysis/regenerate_figures.py              # Figures 1-4, 6
python analysis/figS1_supplementary.py             # Supplementary Figure S1

# verification: recompute every derived statistic reported in the manuscript
python analysis/reproduce_reported_statistics.py
```

Raw re-simulation (optional, minutes to hours):

```bash
python experiments/method_comparison.py            # E1 factorial, 2,160 runs (~8 min)
python experiments/run_E2_E3_proper.py             # E2 grid + added E3 ratios
python experiments/revision_sims.py                # SIM-1..4 sensitivity, 11,340 runs
python experiments/zigzag_onepass_runner.py        # corrected zigzag metric
python experiments/sim5_policy_completion.py       # policy-completion 2x2
```

`simulation_main.py` is the simulation engine and is imported by the runners; running
it directly only prints this guidance. The superseded development campaign it used to
launch is kept as `legacy/development_full_runner.py` (it uses MC = 10 for part of the
grid and is **not** the configuration reported in the manuscript).

## Layout
- `simulation_main.py` — simulation engine (trajectories, participant model, voting, aggregation, control loop). Seeding is deterministic but campaign-specific; each runner documents its own seed map (see below).
- `experiments/` — runners: `method_comparison.py` (E1 speed×method factorial, 2,160 runs), `revision_sims.py` (SIM-1..4 sensitivity, 11,340 runs), `zigzag_onepass_runner.py` (corrected zigzag metric), `sim5_policy_completion.py`.
- `data/` — archived results (all MC = 15): `paper_final_mc15.json` (unified E1e/E2e/E2f/E3d), `E2_proper_results.json`, `E3_supplement_proper.json`, `method_comparison_results.json`, sensitivity/zigzag/policy JSONs, `model_refit120_results.json`.
- `analysis/` — `s1_vstar.py` (optimal speed per condition; Table S1), `model_refit120.py` (predictive-model fit on the 120-record training set; five-fold cross-validation for both model forms; also regenerates Figure 5), `regenerate_figures.py` (Figures 1–4 and 6 from the archives; Figure 5 is produced by `model_refit120.py`), `figS1_supplementary.py` (Supplementary Figure S1).
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
| Supplementary Fig. S1 | analysis/figS1_supplementary.py | data/E3_supplement_proper.json, data/paper_final_mc15.json, data/zigzag_onepass_e2f.json |
| Table S9 (post-hoc) | analysis/s9_posthoc.py | data/s9_posthoc.json |
| Table S2 (ceiling fits, all four trajectories), Table S7 (both residual definitions) | analysis/make_supplementary.py | data/supplementary_derived.json |
| All manuscript-reported derived statistics (verification) | analysis/reproduce_reported_statistics.py | all of data/ |
| Table S11 (speed-range sensitivity) | analysis/table_s11_range_sensitivity.py | data/method_comparison_results.json |
| Table S3, Fig. 5 | analysis/model_refit120.py | data/model_refit120_results.json |
| Table S8 (held-out) | analysis/model_refit120.py | data/model_refit120_results.json |
| Figs. 2–4 | analysis/regenerate_figures.py | data/E2_proper_results.json, data/E3_supplement_proper.json, data/paper_final_mc15.json |
| Eq. (3), Fig. 5, Tables S3/S8 | analysis/model_refit120.py | data/model_refit120_results.json |
| Fig. 6, Table 2 | experiments/revision_sims.py | data/revision_sims_results.json |
| Zigzag (S2) | experiments/zigzag_onepass_runner.py | data/zigzag_onepass_e2f.json |
| Policy-completion | experiments/sim5_policy_completion.py | data/sim5_2x2_results.json |

## Reproduction
`pip install -r requirements.txt` (numpy, scipy, matplotlib). Analysis scripts run from archived JSONs in seconds. Experiment runners regenerate raw results deterministically: `experiments/method_comparison.py` uses a stable per-method seed salt (fixed=1000, majority=2000, quadratic=3000; ~8 min) and stores per-run RMSE lists. `experiments/run_E2_E3_proper.py` regenerates the E2 speed grid (seed = i*997 + 10v + 100p) and the three added E3 adversarial ratios (seed = i*31 + N + 100p); spot checks reproduce the archived means bit-exactly. The three original E3 ratios (10/15/30%) in `paper_final_mc15.json` are frozen archives from the earlier characterization run. The engine is unchanged, but the seed map used by that run is not recorded and its runner is not included, so those cells are provided as archives rather than as reproducible outputs; re-simulation under the conventions documented here reproduces them only up to Monte Carlo noise. The two-way ANOVA table is regenerated from the per-run archive into `data/e1_anova_v2.json`.

## Notes on the archived data

**Legacy field name.** The engine, the runners and the archived JSON keys use the
historical name `troll_ratio` (and key fragments such as `_tr0.20`). This is the
**adversarial ratio p** of the manuscript. The name is retained deliberately: renaming
it would require rewriting every archived JSON key and would put reproducibility at
risk for no scientific gain.

**Frozen historical archives.** Three E3 adversarial ratios (10%, 15%, 30%) in
`paper_final_mc15.json` come from the earlier characterization run. Their downstream
statistics and figures reproduce from the deposited result data, but they cannot be
regenerated from their original random seeds, because the original runner and seed map
were not retained. Every other campaign in this repository regenerates from its
released runner under the documented seed map.

**Rounding basis of the reported summary statistics.** Table 1 prints eta^2 to one
decimal place, and the summary figures quoted in the Abstract (the ratio range and its
median) are formed from those printed values. Supplementary Table S11 prints the same
ratios at full archive precision, so the two differ slightly in the last digit: the
median is 6.9x on the Table 1 basis and 6.97x (7.0x) at full precision, because the two
middle cells (square 20%, circle 40%) lie close together. `analysis/reproduce_reported_statistics.py`
checks the Table 1 basis and reports the full-precision value alongside it, so both can
be reconciled from a single run.

**Tested environment.** python 3.12, numpy 2.3.5, scipy 1.16.3, matplotlib 3.10.8.
The version floors in `requirements.txt` are deliberately loose; no feature newer than
those floors is used.
