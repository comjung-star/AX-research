"""Recover sealed generation and run frozen offline inference without API calls."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    args = parser.parse_args()
    expected = 'abd3a3e52fb5dfba741482212e251187ef0cb95578379f437484c6563c77d76e'
    assert hashlib.sha256(args.archive.read_bytes()).hexdigest() == expected
    destination = ROOT / '.work-new20-runtime'
    assert not destination.exists() and not (ROOT / 'validation20-scratch').exists()
    tokenizer = ROOT / 'src/ax_research/retrieval/bm25.py'
    original = tokenizer.read_bytes()
    precision = ROOT / 'scripts/autonomous_trial2_precision.py'
    precision_original = precision.read_bytes()
    precision_normalized = precision_original.replace(b'\r\n', b'\n')
    historical = subprocess.check_output(['git', 'show', '1e9523ed2da67ec43fabc901774b1f163edc51ab:src/ax_research/retrieval/bm25.py'], cwd=ROOT)
    environment = {**os.environ, 'PYTHONPATH': os.pathsep.join([str(ROOT / 'src'), str(ROOT)]),
                   'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1'}
    lock = ROOT / '.work-trial2.lock'
    with lock.open('x'):
        try:
            destination.mkdir()
            with zipfile.ZipFile(args.archive) as archive:
                for member in archive.infolist():
                    target = (destination / member.filename).resolve()
                    assert target.is_relative_to(destination.resolve())
                    assert Path(member.filename).parts[0] in {'api', 'api_ledger.json', 'generate_status.json', 'run_policy.json'}
                archive.extractall(destination)
            tokenizer.write_bytes(historical)
            precision.write_bytes(precision_normalized)
            for stage in ('restore', 'infer'):
                subprocess.run([sys.executable, str(ROOT / 'scripts/validation20_resume.py'), stage,
                                str(args.model.resolve()), str(destination)], cwd=ROOT, env=environment, check=True)
            verification = (
                'from scripts import autonomous_trial2_precision as run; '
                'reference=run.read(run.OUT/"17_trial2_precision_predictions.json"); '
                'run.OUT=run.ROOT/".work-new20-precision-reproduction"; '
                'run.OUT.mkdir(exist_ok=False); run.infer(); '
                'assert run.read(run.OUT/"17_trial2_precision_predictions.json")==reference; '
                'print("Exact candidate mapping reproduction verified")')
            subprocess.run([sys.executable, '-c', verification],
                           cwd=ROOT, env=environment, check=True)
        finally:
            if precision.read_bytes() == precision_normalized:
                precision.write_bytes(precision_original)
            if tokenizer.read_bytes() == historical:
                tokenizer.write_bytes(original)
            elif tokenizer.read_bytes() != original:
                raise RuntimeError('Tokenizer changed concurrently; preserve it for inspection')
            lock.unlink()


if __name__ == '__main__':
    main()
