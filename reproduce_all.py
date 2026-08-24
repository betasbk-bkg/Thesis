"""One-command reproduction driver.

    python reproduce_all.py            # analyses + tables + figures + verification
    python reproduce_all.py --no-figs  # skip figure regeneration
    python reproduce_all.py --gate     # additionally re-simulate three archived E1
                                       # cells and check them bit-exactly (~1 min)

Everything except --gate runs from the archived JSONs in data/ and takes seconds.
Exit status is non-zero if any step fails.
"""
import argparse, importlib.util, os, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))

REQUIRED_DATA = [
    'data/method_comparison_results.json',
    'data/e1_anova_v2.json',
    'data/s1_vstar.json',
    'data/s9_posthoc.json',
    'data/model_refit120_results.json',
    'data/revision_sims_results.json',
    'data/paper_final_mc15.json',
    'data/E2_proper_results.json',
    'data/E3_supplement_proper.json',
    'data/zigzag_onepass_e2f.json',
    'data/sim5_2x2_results.json',
]

ANALYSES = [
    ('Table 1 (two-way ANOVA)',            'analysis/e1_anova.py'),
    ('Table S1 (optimal speed)',           'analysis/s1_vstar.py'),
    ('Table S9 (post-hoc comparisons)',    'analysis/s9_posthoc.py'),
    ('Tables S2 / S7 (derived)',           'analysis/make_supplementary.py'),
    ('Table S11 (speed-range sensitivity)', 'analysis/table_s11_range_sensitivity.py'),
    ('Tables S3 / S8, Eq. (3), Figure 5',  'analysis/model_refit120.py'),
]

FIGURES = [
    ('Figures 1-4 and 6',    'analysis/regenerate_figures.py'),
    ('Supplementary Fig. S1', 'analysis/figS1_supplementary.py'),
]

VERIFY = ('Manuscript-reported statistics', 'analysis/reproduce_reported_statistics.py')


def banner(text):
    print('\n' + '=' * 78)
    print(text)
    print('=' * 78)


def check_environment():
    banner('0. Environment')
    ok = True
    print('  python %s' % sys.version.split()[0])
    for mod in ('numpy', 'scipy', 'matplotlib'):
        try:
            m = __import__(mod)
            print('  %-12s %s' % (mod, getattr(m, '__version__', '?')))
        except ImportError:
            print('  %-12s MISSING  (pip install -r requirements.txt)' % mod)
            ok = False
    missing = [p for p in REQUIRED_DATA if not os.path.exists(os.path.join(ROOT, p))]
    if missing:
        ok = False
        for p in missing:
            print('  missing data file: %s' % p)
    else:
        print('  all %d archived data files present' % len(REQUIRED_DATA))
    return ok


def run(label, script):
    print('\n--- %s  (%s)' % (label, script))
    res = subprocess.run([sys.executable, script], cwd=ROOT,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    tail = [ln for ln in res.stdout.strip().splitlines() if ln.strip()][-4:]
    for ln in tail:
        print('    ' + ln)
    print('    -> %s' % ('OK' if res.returncode == 0 else 'FAILED (exit %d)' % res.returncode))
    if res.returncode != 0:
        print(res.stdout[-2000:])
    return res.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-figs', action='store_true', help='skip figure regeneration')
    ap.add_argument('--gate', action='store_true',
                    help='re-simulate three archived E1 cells and compare bit-exactly')
    args = ap.parse_args()

    status = {}
    status['environment'] = check_environment()
    if not status['environment']:
        print('\nEnvironment check failed; fix the items above before continuing.')
        return 1

    banner('1. Analyses (from archived data)')
    for label, script in ANALYSES:
        status[label] = run(label, script)

    if not args.no_figs:
        banner('2. Figures')
        for label, script in FIGURES:
            status[label] = run(label, script)

    if args.gate:
        banner('3. Exact re-simulation gate')
        try:
            spec = importlib.util.spec_from_file_location(
                'revision_sims', os.path.join(ROOT, 'experiments/revision_sims.py'))
            mod = importlib.util.module_from_spec(spec)
            sys.path.insert(0, ROOT)
            spec.loader.exec_module(mod)
            status['exact E1 reproduction gate'] = bool(mod.validation_gate())
        except Exception as exc:
            print('  gate raised %s: %s' % (type(exc).__name__, exc))
            status['exact E1 reproduction gate'] = False

    banner('4. Verification against manuscript-reported values')
    status[VERIFY[0]] = run(*VERIFY)

    banner('SUMMARY')
    for k, v in status.items():
        print('  [%s] %s' % ('PASS' if v else 'FAIL', k))
    failed = [k for k, v in status.items() if not v]
    print('\n%d / %d steps passed%s' % (len(status) - len(failed), len(status),
                                        '' if not failed else '  <-- ' + ', '.join(failed)))
    return 0 if not failed else 1


if __name__ == '__main__':
    sys.exit(main())
