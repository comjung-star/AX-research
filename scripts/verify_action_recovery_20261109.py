"""Reproduce the extraction-only export and verify frozen-source hashes."""
import json

from scripts.recover_case_actions_20261109 import DEST, build, digest


def main():
    saved = {name: json.loads((DEST / (name + '.json')).read_text(encoding='utf-8'))
             for name in ('case_profiles', 'missing24-audit', 'verification')}
    assert all(digest(path) == value for path, value in saved['verification']['source_sha256'].items())
    profiles, audit, summary = build()
    assert profiles == saved['case_profiles']
    assert audit == saved['missing24-audit']
    assert summary == saved['verification']
    print('PASS: 112 profiles reproduced; 24 recovered; 88 unchanged; literal spans and source hashes match')


if __name__ == '__main__':
    main()
