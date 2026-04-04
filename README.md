# Speed Over Strategy: Simulation Code

This repository contains the simulation code supporting the findings of:

**"Speed Over Strategy: Why Agent Velocity Dominates Aggregation Method in Crowd-Sourced Continuous Control"**

BongKeun Song  
Friedrich-Alexander-Universität Erlangen-Nürnberg (FAU)  
*Submitted to Scientific Reports*

---

## Overview

This code implements a discrete-time simulation of crowd-sourced trajectory tracking, in which N participants collectively control a shared agent via 8-direction voting. The study examines the relative contributions of agent speed and aggregation method to tracking error.

---

## Repository Structure

```
simulation_main.py   # Main simulation engine (E1–E5)
method_comparison.py # Aggregation method comparison utilities
patch_mc15.py        # Monte Carlo replication patch (MC=15)
README.md
requirements.txt
```

---

## Requirements

```
numpy
scipy
```

Install:
```bash
pip install numpy scipy
```

---

## Usage

Run all experiments:
```bash
python3 simulation_main.py
```

Output: `results.json` containing all experimental data.

---

## Experiments

| ID | Description | Runs |
|----|-------------|------|
| E1 | Speed × Method ANOVA (circle, square) | 2,160 |
| E2 | Speed Sweep across adversarial ratios | 1,440 |
| E3 | Crowd-Size Sweep — ceiling effect | 4,320 |
| E4 | Multiplicative model fitting | (uses E2+E3) |
| E5 | Out-of-sample generalization | 90 |
| **Total** | | **8,010** |

---

## Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| DT | 1/60 s | Simulation time step |
| DELAY_F | 26 frames | Input delay ≈ 433 ms |
| MC | 15 | Monte Carlo replications per condition |
| Trajectories | Circle, Square, Lemniscate, Zigzag | Reference paths |

---

## Citation

If you use this code, please cite:

```
Song, B. (2026). Speed Over Strategy: Why Agent Velocity Dominates 
Aggregation Method in Crowd-Sourced Continuous Control. 
Scientific Reports. [DOI pending]
```

---

## License

MIT License. See LICENSE file.

---

## Contact

BongKeun Song — betasbk@gmail.com  
Friedrich-Alexander-Universität Erlangen-Nürnberg
