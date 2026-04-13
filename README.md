# Speed Over Strategy: Simulation Code

This repository contains the simulation code and aggregated experimental data supporting the findings of:

> **"Speed Over Strategy: Why Agent Velocity Dominates Aggregation Method in Crowd-Sourced Continuous Control"**  
> BongKeun Song  
> Friedrich-Alexander-Universität Erlangen-Nürnberg (FAU)  
> *Submitted to Scientific Reports*

Archived on Zenodo: [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19413803.svg)](https://doi.org/10.5281/zenodo.19413803)

---

## Overview

This code implements a discrete-time simulation of crowd-sourced trajectory tracking, in which N participants collectively control a shared agent via 8-direction voting. The study examines the relative contributions of agent speed and aggregation method to tracking error across 8,010 simulation runs.

---

## Repository Structure

```
├── simulation_main.py              # Main simulation engine (all experiments)
├── method_comparison.py            # E1: Aggregation method comparison (ANOVA)
├── patch_mc15.py                   # MC=15 patch applied to all experiments
├── requirements.txt                # Python dependencies
│
├── paper_final_mc15.json           # PRIMARY DATA FILE — all experiments unified
├── method_comparison_results.json  # E1 raw results (ANOVA source data)
├── E2_proper_results.json          # E2 speed sweep results (v* estimation)
├── E3_supplement_proper.json       # E3 N-sweep supplement (lemniscate/zigzag)
└── precise_anova_analysis.json     # ANOVA η² decomposition results
```

---

## File Descriptions

### Code

| File | Description |
|------|-------------|
| `simulation_main.py` | Core simulation engine. Implements Circle, Square, Lemniscate, Zigzag trajectory classes; `simulate()` function; all 5 experiments (E1–E5). |
| `method_comparison.py` | E1 experiment: Aggregation method comparison (Fixed / Majority / Quadratic) across speed × troll conditions. Outputs ANOVA results. |
| `patch_mc15.py` | Applies MC=15 Monte Carlo runs uniformly across all experiments. Run this after `simulation_main.py` to ensure consistency. |
| `requirements.txt` | Python dependencies (`numpy`, `scipy`, `matplotlib`). |

### Data Files

| File | Experiment | Contents |
|------|-----------|----------|
| `paper_final_mc15.json` | **All** | Primary data file. Contains `e1e_results` (E1 training data, 48 conditions), `e2e_results` (E2 N-sweep circle/square, 72 conditions), `e2f_results` (E2 N-sweep lemniscate/zigzag, 144 conditions), `e3d_results` (E5 OOS validation, 6 conditions), `ceiling_fits` (asymptotic fit parameters), `analysis` (model coefficients, CV results). |
| `method_comparison_results.json` | E1 | Raw RMSE results for all 144 conditions (2 trajectories × 3 troll ratios × 8 speeds × 3 methods, N=150, MC=15). Source data for Table 1, Figure 1, Figure 2. |
| `E2_proper_results.json` | E2 | Speed sweep results: 96 conditions (circle + square, 6 troll ratios × 8 speeds, N=150, MC=15). Source data for Figure 3. |
| `E3_supplement_proper.json` | E3 | N-sweep supplement: 72 conditions (lemniscate + zigzag, 6 troll ratios × 12 N values, v=5.0 m/s, MC=15). Part of Figure 4 and Supplementary Figure S1. |
| `precise_anova_analysis.json` | E1 | ANOVA η² decomposition: speed, method, and interaction variance components for circle and square trajectories at 3 troll levels. Source data for Figure 2 and Table 1. |

---

## Key Simulation Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `DT` | 1/60 s ≈ 16.7 ms | Simulation frame rate (60 fps) |
| `WIN` | 0.3 s (18 frames) | Voting interval |
| `DELAY_F` | 26 frames ≈ 433 ms | System delay (end-to-end latency) |
| `DUR` | 65 s | Simulation duration |
| `MSPD` | 5.0 m/s | Maximum agent speed |
| `MC` | 15 | Monte Carlo repetitions per condition |
| Directions | 8 | Discrete voting directions (0°, 45°, ..., 315°) |
| Accurate agents | 70% of non-troll | ±3° noise |
| Slow agents | 20% of non-troll | Lagged direction |
| Troll agents | troll_ratio × N | Uniform random direction |

---

## Reproducing Results

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run full simulation suite
```bash
python simulation_main.py
```
Estimated runtime: ~30 minutes (8,010 runs × MC=15)

### Run E1 only (method comparison)
```bash
python method_comparison.py
```

### Apply MC=15 patch
```bash
python patch_mc15.py
```

---

## Data Format

All JSON result files follow this structure per condition:

```json
{
  "circle_tr0.20_v2.0": {
    "rmse_mean": 0.2493,
    "rmse_std":  0.0031,
    "rmse_ci95": 0.0016,
    "gamma_mean": 0.8012,
    "mc_runs": 15
  }
}
```

Key naming convention: `{trajectory}_{troll_ratio}_{speed_or_N}`

---

## License

MIT License. See `LICENSE` for details.
