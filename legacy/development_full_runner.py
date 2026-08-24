"""Superseded development campaign runner (kept for provenance).

This is the entry point that simulation_main.py used to expose via __main__.
It runs a development-era campaign in which parts of the grid used MC = 10,
which is NOT the configuration reported in the manuscript (MC = 15 throughout).
Do not use it to reproduce the paper; see README.md / reproduce_all.py.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simulation_main as sm

if __name__ == '__main__':
    sm.main()
