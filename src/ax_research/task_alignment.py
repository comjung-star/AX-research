"""Literal request/exclusion partition; no inferred case outcomes or relevance labels."""
import re

import numpy as np

from ax_research.pairwise_ridge import unit


def partition_request(text):
    pieces = []
    for match in re.finditer(r'[^.!?;。；\n]+', text):
        start, end = match.span()
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        sentence = text[start:end]
        # A bounded mixed-polarity construction; do not split coordinated negatives.
        mixed = re.match(r'(.+?만\s*제공하고)\s+(.+)', sentence)
        ranges = [(start, start + mixed.end(1)), (start + mixed.start(2), end)] if mixed else [(start, end)]
        for left, right in ranges:
            quote = text[left:right]
            if re.search(r'않|금지|제외|\b(?:not|never|without)\b', quote, re.I):
                role = 'excluded'
            elif re.search(r'(?:사람|담당자).{0,30}승인', quote):
                role = 'human_approval'
            elif re.search(r'싶|원합|원하|요청합', quote) or (mixed and right == start + mixed.end(1)):
                role = 'requested'
            else:
                role = 'background'
            pieces.append({'quote': quote, 'start': left, 'end': right, 'role': role})
    chosen = [p for p in pieces if p['role'] == 'requested']
    fallback = not bool(chosen)
    if fallback:
        chosen = [p for p in pieces if p['role'] == 'background']
    requested = '\n'.join(p['quote'] for p in chosen)
    hints = []
    for part in chosen:
        for match in re.finditer(r'점검 순서|우선순위|요약표|현황표|목록|근거|출처|시각|위치', part['quote']):
            start, end = part['start'] + match.start(), part['start'] + match.end()
            hints.append({'quote': text[start:end], 'start': start, 'end': end})
    return {'source_text': text, 'pieces': pieces, 'requested_text': requested,
            'excluded_text': '\n'.join(p['quote'] for p in pieces if p['role'] == 'excluded'),
            'output_hints': hints, 'output_hint_text': '\n'.join(dict.fromkeys(p['quote'] for p in hints)),
            'fallback_used': fallback, 'status': 'BOUNDED_LITERAL_RULES_NOT_VERIFIED_SEMANTIC_PARSE'}


def cosine(first, second, embeddings):
    if not first or not second:
        return None
    return float(np.clip(np.dot(embeddings[first], embeddings[second]), -1, 1))


def replace_core(matrix, action, objects, task=None):
    result = np.array(matrix, dtype=float, copy=True)
    has_a = np.array([v is not None for v in action], dtype=float)
    has_o = np.array([v is not None for v in objects], dtype=float)
    a = np.array([v if v is not None else 0 for v in action])
    o = np.array([v if v is not None else 0 for v in objects])
    for index, values in [(3, unit(a)), (4, unit(o)), (5, unit(np.minimum(a, o) * has_a * has_o)),
                          (6, unit(a * o * has_a * has_o)), (7, has_a), (8, has_o)]:
        result[:, index] = values
    if task is not None:
        result[:, 9] = unit(task)
    return result
