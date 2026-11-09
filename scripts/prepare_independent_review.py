"""Create empty independent-author and blind reviewer forms, not fabricated data."""
import csv
import json

from scripts.improvement_cycle import ROOT, read


def main():
    output = ROOT / 'docs/independent-validation-20261108'
    author = output / 'author'
    review = output / 'review'
    if author.exists() or review.exists():
        raise FileExistsError('Independent submission forms already exist')
    author.mkdir()
    review.mkdir()
    with (author / 'questions_to_fill.csv').open('x', encoding='utf-8-sig', newline='') as target:
        writer = csv.DictWriter(target, fieldnames=['query_id', 'business_problem', 'input', 'desired_output', 'constraints', 'author_id'])
        writer.writeheader()
        writer.writerows({'query_id': f'IVQ{position:03d}'} for position in range(1, 41))
    declaration = {'author_id': '', 'independent_of_model_development': None, 'saw_case_corpus': None,
                   'saw_rankings_or_old_labels': None, 'authored_from_real_work_needs': None,
                   'submission_status': 'EMPTY_TEMPLATE_NOT_COLLECTED_DATA'}
    (author / 'authorship_to_fill.json').write_text(json.dumps(declaration, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    author_notes = '질문 작성자에게는 이 폴더만 전달합니다. 사례 목록·검토 폴더·기존 연구 결과를 함께 전달하지 않습니다.\n빈40행은 제출 자리이며 새 질문40개가 생성됐다는 뜻이 아닙니다. 실제 업무의 입력·원하는 결과·제약을 작성하고 작성자 노출 이력을 기입합니다.\n'
    (author / 'README.ko.md').write_text(author_notes, encoding='utf-8')
    cases = read('docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    with (review / 'cases_blind.csv').open('x', encoding='utf-8-sig', newline='') as target:
        writer = csv.DictWriter(target, fieldnames=['case_id', 'problem', 'task', 'context', 'evidence_ids'])
        writer.writeheader()
        writer.writerows({key: value.get(key, '') for key in writer.fieldnames} for _, value in sorted(cases.items()))
    fields = ['query_id', 'case_id', 'grade_0_to_3', 'status_JUDGED_or_ABSTAIN', 'task_quote', 'rationale', 'reviewer_id']
    for reviewer in ('A', 'B'):
        with (review / f'reviewer_{reviewer}_to_fill.csv').open('x', encoding='utf-8-sig', newline='') as target:
            writer = csv.DictWriter(target, fieldnames=fields)
            writer.writeheader()
            writer.writerows({'query_id': f'IVQ{position:03d}', 'case_id': case} for position in range(1, 41) for case in sorted(cases))
    (review / 'README.ko.md').write_text('검토자A/B는 서로의 파일을 열지 않고 각각 판정합니다. 두 파일을 같은 검토자에게 함께 주지 않습니다.\n새 질문이 실제 제출·확인된 뒤 질문 원문과 cases_blind.csv만 제공합니다. 모델명·추천 순위·과거 정답은 제공하지 않습니다.\n빈 판정칸은0점이 아닙니다. 판단 불가이면ABSTAIN으로 남깁니다. 이견 조정 전까지 원본A/B를 덮어쓰지 않습니다.\n', encoding='utf-8')
    print(json.dumps({'state': 'EMPTY_FORMS_PREPARED', 'author_slots': 40, 'blind_cases': len(cases),
                      'blank_rating_slots_per_reviewer': 40 * len(cases), 'actual_new_queries': 0, 'actual_human_grades': 0}))


if __name__ == '__main__':
    main()
