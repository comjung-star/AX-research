"""Read-only verifier amendment: JSON turns integer count-map keys into strings."""
import json

from scripts import llm_catalog_retrieval_comparison_20261109 as run
from scripts.task_alignment_20261109 import sha


def main():
    run.frozen()
    original = run.compute_evaluation
    saved = run.load('evaluation.json')
    raw = run.load('predictions.json')
    labels, _ = run.load_labels()
    recomputed = original(raw['questions'], labels, run.load('query-case-evidence.json'), run.inputs()[3])
    differences = [k for k in recomputed if recomputed[k] != saved[k]]
    assert differences == ['selection_counts'], differences
    assert json.loads(json.dumps(recomputed['selection_counts'])) == saved['selection_counts']
    protected = ['evaluation.json', 'predictions.json', 'query-case-evidence.json', 'selections.json', 'freeze.json', 'vectors.npz']
    before = {p: sha(run.OUT / p) for p in protected}
    def canonical_compute(*args, **kwargs):
        return json.loads(json.dumps(original(*args, **kwargs), ensure_ascii=False))
    # Affect equality checking in this verifier process only; inference sources and
    # saved scores remain byte-identical. The frozen original verifier is retained.
    run.compute_evaluation = canonical_compute
    run.verify()
    assert all(sha(run.OUT / p) == h for p, h in before.items())
    note = {'state': 'VERIFIER_JSON_KEY_FORMAT_AMENDMENT_ONLY',
        'original_failure': 'selection_counts integer keys became string keys in saved JSON',
        'only_differing_recomputed_field_before_canonicalization': differences,
        'all_numeric_metrics_equal_before_amendment': True,
        'method_prompt_ranking_or_labels_changed': False,
        'protected_artifact_sha256': before, 'amended_verifier_sha256': sha(__file__),
        'replay_command': 'python -m scripts.verify_llm_catalog_retrieval_comparison_20261109',
        'new_paid_calls': 0}
    (run.OUT / 'verification-format-note.json').write_text(json.dumps(note, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
