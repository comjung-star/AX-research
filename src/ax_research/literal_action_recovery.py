"""Versioned literal coverage repair for missing actions; no embeddings or labels."""
from copy import deepcopy
import re

from ax_research.semantic_mapping import field_profile


def recover_action_profile(text, config, negation_guard, recovery, *, executed=False, context=''):
    original = field_profile(text, config, negation_guard, executed=executed, context=context)
    result = deepcopy(original)
    additions = []
    # Do not rewrite the 88 existing nonempty action profiles or held clauses.
    if not original['fields']['action']:
        for clause in original['spans']['task']:
            for rule in recovery['rules']:
                for match in re.finditer(rule['pattern'], clause['quote'], re.I):
                    begin, end = match.span('action')
                    if begin < 0 or begin == end:
                        raise ValueError('Recovery rules must capture a nonempty literal action')
                    start = clause['start'] + begin
                    stop = clause['start'] + end
                    additions.append({'quote': text[start:stop], 'start': start, 'end': stop,
                                      'rule_id': rule['id'], 'clause': clause})
    additions.sort(key=lambda span: (span['start'], span['end'], span['rule_id']))
    unique = {}
    for addition in additions:
        unique.setdefault((addition['start'], addition['end']), addition)
    additions = list(unique.values())
    if additions:
        action_spans = [{key: span[key] for key in ('quote', 'start', 'end')} for span in additions]
        # Rebuild the old shallow residual object using actual action boundaries.
        # This removes recovered verbs from the object field, not a semantic-role claim.
        objects = []
        for clause in original['spans']['task']:
            local = [span for span in action_spans if clause['start'] <= span['start'] and span['end'] <= clause['end']]
            cursor = clause['start']
            ranges = []
            for span in local:
                if span['start'] < cursor:
                    raise ValueError('Overlapping recovery spans')
                ranges.append((cursor, span['start']))
                cursor = span['end']
            ranges.append((cursor, clause['end']))
            for start, end in ranges:
                for match in re.finditer(r'[^,·:：/()]+', text[start:end]):
                    raw = match.group()
                    if re.sub(config['object_stopwords'], '', raw, flags=re.I).strip():
                        left, right = len(raw) - len(raw.lstrip()), len(raw.rstrip())
                        offset = start + match.start()
                        objects.append({'quote': raw[left:right], 'start': offset + left, 'end': offset + right})
        result['spans']['action'], result['spans']['object'] = action_spans, objects
        for field in ('action', 'object'):
            result['fields'][field] = '\n'.join(dict.fromkeys(span['quote'] for span in result['spans'][field]))
        result['unknown_fields'] = [key for key, value in result['fields'].items() if not value]
    result['action_recovery'] = {
        'version': recovery['version'], 'changed': bool(additions), 'added_evidence': additions,
        'status': 'LITERAL_ACTION_RECOVERED' if additions else ('EXISTING_ACTION_PRESERVED' if original['fields']['action'] else 'UNKNOWN_NO_LITERAL_ACTION'),
        'semantically_verified': False, 'embeddings_recomputed': False,
    }
    return result
