"""Heldout I/O and evaluation adapters. No change to frozen scoring functions."""
import hashlib
import json
import math
import re
import unicodedata
from pathlib import Path

SYSTEMS = ('Single Dense', 'A', 'B', 'C')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write(path, obj):
    """Exclusive creation: even intermediate artifacts cannot be overwritten."""
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def jsonl(path):
    with Path(path).open(encoding='utf-8-sig') as stream:
        return [json.loads(line) for line in stream if line.strip()]


def normalize(text):
    return re.sub(r'\W+', '', unicodedata.normalize('NFKC', text)).casefold()


def questions(path, *, development=False, previous=()):
    rows = jsonl(path)
    if not rows:
        raise ValueError('Empty questions')
    ids, texts = set(), set()
    old_ids = {q['query_id'] for q in previous}
    old_texts = {normalize(q['text']) for q in previous}
    for row in rows:
        if set(row) != {'query_id', 'text', 'split'}:
            raise ValueError('Question fields must be query_id/text/split')
        qid, text = row['query_id'], row['text']
        if not isinstance(qid, str) or not qid.strip() or not isinstance(text, str) or not text.strip():
            raise ValueError('Invalid question')
        if row['split'] != ('DEV' if development else 'TEST'):
            raise ValueError('Wrong split')
        n = normalize(text)
        if not n or qid in ids or n in texts:
            raise ValueError('Duplicate question')
        if not development and (qid in old_ids or n in old_texts):
            raise ValueError('Known Dev/pilot question overlap')
        ids.add(qid)
        texts.add(n)
    return rows


def manifest(path, corpus_sha):
    m = read(path)
    if m['schema_version'] != 'ax-heldout-v1' or not isinstance(m['test_id'], str) or not m['test_id'].strip():
        raise ValueError('Invalid schema/test_id')
    if m['grade_scale'] != [0, 1, 2, 3] or m['relevant_threshold'] != 2:
        raise ValueError('Policy mismatch')
    if m['corpus'] != {'id': 'ax112', 'case_count': 112, 'sha256': corpus_sha}:
        raise ValueError('Corpus mismatch')
    if m['judgment_scope'] not in ('FULL_CORPUS', 'PARTIAL'):
        raise ValueError('Invalid judgment_scope')
    if not m['label_sources'] or len(set(m['label_sources'])) != len(m['label_sources']) or any(s not in ('AI-Silver', 'Human-Gold') for s in m['label_sources']):
        raise ValueError('Explicit label_sources required')
    history = m['unused_history']
    if not isinstance(history, dict) or history.get('previously_used') is not False or not history.get('provenance') or not history.get('exposure_log'):
        raise ValueError('Unused history evidence required (not proof of semantic independence)')
    for name in ('questions', 'qrels'):
        desc = m['files'][name]
        if not isinstance(desc['path'], str) or not desc['path'] or not re.fullmatch('[0-9a-f]{64}', desc['sha256']):
            raise ValueError('Invalid file descriptor')
    return m


def input_path(mpath, desc):
    path = (Path(mpath).parent / desc['path']).resolve()
    if sha(path) != desc['sha256']:
        raise ValueError('Input hash mismatch')
    return path


def validate_predictions(pred):
    ids = pred['case_ids']
    qids = pred['query_ids']
    if len(ids) != 112 or len(set(ids)) != 112 or not qids or len(set(qids)) != len(qids):
        raise ValueError('Invalid prediction registry')
    if set(pred['systems']) != set(SYSTEMS):
        raise ValueError('Missing system')
    for records in pred['systems'].values():
        if len(records) != len(qids) or {r['query_id'] for r in records} != set(qids):
            raise ValueError('Prediction query mapping')
        for row in records:
            ranking = row['ranking']
            if len(ranking) != 112 or set(ranking) != set(ids):
                raise ValueError('Invalid ranking')
            for k in (5, 10, 20):
                if row[f'top{k}'] != ranking[:k]:
                    raise ValueError('TopK mapping')


def evaluate(pred, rows, scope, sources):
    validate_predictions(pred)
    ids, qids = set(pred['case_ids']), set(pred['query_ids'])
    labels = {source: {qid: {} for qid in qids} for source in sources}
    if not sources or len(set(sources)) != len(sources) or any(s not in ('AI-Silver', 'Human-Gold') for s in sources):
        raise ValueError('Invalid sources')
    if scope not in ('FULL_CORPUS', 'PARTIAL'):
        raise ValueError('Invalid scope')
    for r in rows:
        if set(r) != {'query_id', 'case_id', 'grade', 'status', 'label_source', 'rationale'}:
            raise ValueError('Invalid qrel fields')
        q, c, source = r['query_id'], r['case_id'], r['label_source']
        if q not in qids or c not in ids or source not in labels:
            raise ValueError('Unknown qrel ID/source')
        if c in labels[source][q]:
            raise ValueError('Duplicate qrel')
        grade, status = r['grade'], r['status']
        if status not in ('JUDGED', 'ABSTAIN', 'UNJUDGED'):
            raise ValueError('Invalid status')
        if (status == 'JUDGED' and (type(grade) is not int or grade not in range(4))) or (status != 'JUDGED' and grade is not None):
            raise ValueError('Invalid grade/status')
        if not isinstance(r['rationale'], str) or (status != 'UNJUDGED' and not r['rationale'].strip()):
            raise ValueError('Rationale required')
        labels[source][q][c] = grade if status == 'JUDGED' else None
    output = []
    for source, queries in labels.items():
        for system, records in pred['systems'].items():
            for row in records:
                q = row['query_id']; grades = queries[q]
                complete = len(grades) == 112 and all(v is not None for v in grades.values())
                full = scope == 'FULL_CORPUS' and complete
                positives = sum(v >= 2 for v in grades.values() if v is not None)
                metrics = {}; reasons = {}
                for k in (5, 10, 20):
                    top = [grades.get(c) for c in row['ranking'][:k]]
                    p = sum(v >= 2 for v in top) / k if all(v is not None for v in top) else None
                    r = sum(v >= 2 for v in top) / positives if full and positives else None
                    f = 2*p*r/(p+r) if r is not None and p+r else (0.0 if r is not None else None)
                    metrics.update({f'Precision@{k}': p, f'Recall@{k}': r, f'F1@{k}': f})
                    if p is None: reasons[f'Precision@{k}'] = 'TOPK_UNJUDGED_OR_ABSTAIN'
                    if r is None:
                        reason = 'ZERO_POSITIVES' if full else 'INCOMPLETE_OR_PARTIAL_QRELS'
                        reasons[f'Recall@{k}'] = reasons[f'F1@{k}'] = reason
                    if k in (5, 10):
                        ideal = sorted(grades.values(), reverse=True)[:k] if full else []
                        dcg = lambda seq: sum((2**v-1)/math.log2(i+2) for i,v in enumerate(seq))
                        denom = dcg(ideal)
                        metrics[f'nDCG@{k}'] = dcg(top)/denom if full and denom else None
                        if metrics[f'nDCG@{k}'] is None:
                            reasons[f'nDCG@{k}'] = 'ZERO_IDCG' if full else 'INCOMPLETE_OR_PARTIAL_QRELS'
                output.append({'label_source': source, 'system': system, 'query_id': q, 'complete_qrels': complete, 'judged_count': sum(v is not None for v in grades.values()), 'positive_count': positives, 'metrics': metrics, 'undefined_reasons': reasons})
    macro = []
    for source in sources:
        for system in SYSTEMS:
            group = [r for r in output if r['label_source'] == source and r['system'] == system]
            for metric in group[0]['metrics']:
                valid = [r['metrics'][metric] for r in group if r['metrics'][metric] is not None]
                macro.append({'label_source': source, 'system': system, 'metric': metric, 'value': sum(valid)/len(valid) if valid else None, 'defined': len(valid), 'total': len(qids), 'excluded_query_ids': sorted(r['query_id'] for r in group if r['metrics'][metric] is None)})
    return {'per_query': output, 'macro': macro, 'scope': scope, 'threshold': 2, 'label_sources': sources, 'comparison': 'Compare systems within identical label_source only; Dev0-4>=3 is not directly comparable.'}
