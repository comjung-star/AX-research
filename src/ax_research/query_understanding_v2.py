"""Query-only bounded literal parsing; keep unknowns and source offsets explicit."""
import re
from copy import deepcopy

from ax_research.semantic_mapping import field_profile

REQUEST = r'싶|원합|원하|필요(?:합|하|한)|주세요|주십시오|바랍|요청합|이어야|여야|되어야'
NEGATIVE = r'않|금지|제외|지\s*마(?:세요|십시오)|(?:해|해서|면|되어서는|해서는)\s*안\s*(?:됩|되|돼)|\b(?:not|never|without)\b'
APPROVAL = r'(?:사람|담당자|팀장|책임자).{0,25}승인|승인(?:이|을).{0,12}(?:필요|받)|승인\s*(?:후|전)|검토를\s*거쳐'
EXTRA_ACTION = r'(?<![가-힣])(?:찾아내|보여주|비교|대조|정리|표시|제공|안내|묶|찾)(?=$|[\s,·]|아|어|고|는|기|다|습|을|하|한|해|했|할|된|되)'


def partition_v2(text):
    pieces = []
    def add(start, end, force_request=False):
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        quote = text[start:end]
        if not quote:
            return
        if re.search(NEGATIVE, quote, re.I):
            role = 'excluded'
        elif re.search(APPROVAL, quote):
            role = 'human_approval'
        elif force_request or re.search(REQUEST, quote):
            role = 'requested'
        else:
            role = 'unknown'
        pieces.append({'quote': quote, 'start': start, 'end': end, 'role': role})
    for match in re.finditer(r'[^.!?;。；\n]+', text):
        start, end = match.span()
        sentence = match.group()
        split = None
        # Split only where a positive request is actually licensed before a negative/approval tail.
        if re.search(NEGATIVE + '|' + APPROVAL, sentence, re.I):
            for boundary in re.finditer(r'[,，]\s*|(?:하되|들되|하며|하지만|하고|이며)\s*', sentence):
                left, right = sentence[:boundary.end()], sentence[boundary.end():]
                licensed = bool(re.search(REQUEST, left) or re.search(r'만\s*(?:제공|안내|작성|보여주).*하고', left)
                                or (boundary.group().startswith(('하되', '들되')) and re.search(r'작성|만들|검토|조회|검색|찾', left)))
                if licensed and not re.search(NEGATIVE, left, re.I) and re.search(NEGATIVE + '|' + APPROVAL, right, re.I):
                    split = start + boundary.end()
                    break
        if split is not None:
            add(start, split, True)
            add(split, end)
        else:
            add(start, end)
    requested = [p for p in pieces if p['role'] == 'requested']
    hints = []
    for piece in requested:
        for match in re.finditer(r'점검 순서|우선순위|요약표|현황표|목록|근거|출처|시각|위치', piece['quote']):
            start, end = piece['start'] + match.start(), piece['start'] + match.end()
            hints.append({'quote': text[start:end], 'start': start, 'end': end})
    return {'source_text': text, 'pieces': pieces,
            'requested_text': '\n'.join(p['quote'] for p in requested),
            'excluded_text': '\n'.join(p['quote'] for p in pieces if p['role'] == 'excluded'),
            'output_hints': hints, 'output_hint_text': '\n'.join(dict.fromkeys(p['quote'] for p in hints)),
            'fallback_used': False, 'request_unknown': not bool(requested),
            'status': 'QUERY_UNDERSTANDING_V2_LITERAL_NOT_SEMANTIC_GOLD'}


def understand(text, config):
    partition = partition_v2(text)
    cfg = deepcopy(config)
    # Avoid extracting operation substrings from identifier/applicant and similar noun forms.
    cfg['action_pattern'] = '(?:' + cfg['action_pattern'] + '|' + EXTRA_ACTION + r')(?!자|번호|코드|값|문서|기간|수(?:\s|$))'
    profile = field_profile(partition['requested_text'], cfg, '', executed=False)
    profile['understanding_version'] = 'query-understanding-v2-20261109'
    return partition, profile
