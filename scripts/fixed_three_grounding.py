"""Literal source anchors from Dev questions, never used in generation or ranking."""
import re
from collections import defaultdict

from ax_research.heldout import read, write
from scripts.fixed_three_views import OUT

# Each tuple is action, object/input, output, and business purpose. Each regex
# allows inflections or common paraphrases. This is lexical coverage only.
ANCHORS = {
    '01': ('찾|검색|탐색|조회', r'운영\s*지침|처리\s*기록', r'원문\s*위치|출처|근거\s*위치', r'복구|장애\s*대응'),
    '02': ('감지|탐지|찾|식별', r'접속\s*기록|접속\s*로그', '알림|알리|통지|통보|전달', '현재|실시간|지금|즉시'),
    '03': ('(?=.*(?:분류|나누|구분))(?=.*(?:배정|할당|전달))', '첨부|서류|증빙', r'대기함|담당\s*큐|담당\s*함', '종류|유형'),
    '04': ('확인|검토|점검|검증', r'증빙|제출\s*자료', '표시|표기|보여|알리|목록', '갱신|기준'),
    '05': ('요약|정리', r'임대\s*계약|계약서', r'비교|요약\s*자료', r'갱신|비교\s*준비'),
    '06': (r'대조|비교|매칭|맞춰|일치\s*확인', '은행|입출금', '알림|알리|통지|전달|보고', '중복|누락|불일치'),
    '07': ('(?=.*(?:안내|설명|응답))(?=.*(?:이관|넘기|전달|인계))', r'포장|회수\s*일정|규정', '직원|담당자', '반납|렌탈|반품|반환'),
    '08': ('등록|입력|기록|갱신', '계좌|거래처', r'완료\s*(?:통지|알림|기록)|처리\s*완료', '승인'),
    '09': ('예측|예상|추정', r'작업\s*조건|검사\s*기록', r'불량\s*가능성|품질\s*위험|불량\s*위험', r'다음\s*(?:생산|묶음|배치)|미래'),
    '10': ('감지|탐지|식별|찾', '온도|보관함', '알림|통지|통보|알리|경보', '현재|실시간|즉시'),
}


def main(output=OUT):
    groups = defaultdict(list)
    for slot in read(output / 'slots.json')['records']:
        groups[slot['kind'], slot['query_id'], slot['repeat']].append(slot)
    rows = []
    for (kind, query, repeat), slots in groups.items():
        patterns = dict(zip(('action', 'object', 'output', 'purpose'), ANCHORS[query[-2:]]))
        text = ' '.join(s['title'] + ' ' + s['description'] for s in slots)
        rows.append({'kind': kind, 'query_id': query, 'repeat': repeat,
                     'triplet': {key: bool(re.search(pattern, text)) for key, pattern in patterns.items()},
                     'individual': [
                         {'id': s['id'], **{key: bool(re.search(pattern, s['title']+' '+s['description']))
                                            for key, pattern in patterns.items()}}
                         for s in slots],
                     'searchable_count': sum(s.get('status') != 'MISSING' for s in slots)})
    write(output / 'grounding.json', {'rows': rows, 'patterns': ANCHORS,
                                  'interpretation': 'Lexical retention proxy; contextual errors need manual review. No tuning.'})


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=OUT)
    main(parser.parse_args().output)
