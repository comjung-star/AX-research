"""Post-label synthetic rater sanity controls; no benchmark label rewriting."""
import json
import os
import urllib.request

from scripts.claude_blind_questions import OUT, save
from scripts.ai_pilot_review_v2 import MODELS, RATES, PROMPT, parse_rows


def main():
    target = OUT / 'synthetic_rater_controls'
    if target.exists():
        raise FileExistsError(target)
    target.mkdir()
    task_texts = ['Draft answers to customer questions for employee approval.',
                  'Predict industrial pump failures from sensor histories.',
                  'Detect product surface defects in photos and alert staff.',
                  'Translate purchase orders between Korean and English.',
                  'Retrieve FAQ passages for agents without generating answers.',
                  'Automatically send customer answers without human approval.']
    payload = {'query': '고객 문의에 대한 답변 초안을 작성하고, 직원이 승인한 뒤에만 발송하도록 돕고 싶다.',
               'cases': [{'position': position, 'Problem': '', 'Task': task, 'Context': ''} for position, task in enumerate(task_texts)]}
    prompt = PROMPT.replace('EXACTLY112', 'EXACTLY6').replace('positions0through111', 'positions0through5')
    expected = [True, False, False, False, False, False]
    save(target / 'preregistration.json', {'expected_binary': expected, 'payload': payload, 'prompt': prompt,
         'role': 'SELF_AUTHORED_LITERAL_SYNTHETIC_SANITY_CHECK_NOT_HUMAN_GOLD', 'changes_to_pilot_labels': False,
         'additional_cost_upper_usd': .01, 'timing': 'After rater calls; before opening model comparison metrics'})
    results = {}
    for provider in ('claude', 'gemini'):
        if provider == 'claude':
            endpoint = 'https://api.anthropic.com/v1/messages'
            headers = {'x-api-key': os.environ['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01'}
            body = {'model': MODELS[provider], 'max_tokens': 512, 'system': prompt, 'thinking': {'type': 'disabled'},
                    'output_config': {'effort': 'low'}, 'messages': [{'role': 'user', 'content': json.dumps(payload, ensure_ascii=False)}]}
        else:
            endpoint = 'https://generativelanguage.googleapis.com/v1beta/models/' + MODELS[provider] + ':generateContent'
            headers = {'x-goog-api-key': os.environ['GEMINI_API_KEY']}
            body = {'systemInstruction': {'parts': [{'text': prompt}]}, 'contents': [{'parts': [{'text': json.dumps(payload, ensure_ascii=False)}]}],
                    'generationConfig': {'maxOutputTokens': 512, 'responseMimeType': 'application/json', 'thinkingConfig': {'thinkingLevel': 'minimal'},
                     'responseSchema': {'type': 'OBJECT', 'properties': {'rows': {'type': 'ARRAY', 'minItems': 6, 'maxItems': 6,
                       'items': {'type': 'OBJECT', 'properties': {'position': {'type': 'INTEGER'}, 'grade': {'type': 'INTEGER', 'nullable': True}},
                                 'required': ['position', 'grade']}}}, 'required': ['rows']}}}
        headers['Content-Type'] = 'application/json'
        request = urllib.request.Request(endpoint, json.dumps(body).encode(), headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = json.load(response)
        except Exception:
            save(target / (provider + '_unknown_failure.json'), {'state': 'NO_AUTOMATIC_RETRY', 'reserved_usd': .005})
            continue
        save(target / (provider + '_response.json'), raw)
        rows = parse_rows(raw, provider)
        grades = {row['position']: row['grade'] for row in rows}
        passed = [grades.get(position) is not None and (grades[position] >= 2) == value for position, value in enumerate(expected)]
        usage = raw.get('usage', {}) if provider == 'claude' else raw.get('usageMetadata', {})
        inputs = usage.get('input_tokens', 0) if provider == 'claude' else usage.get('promptTokenCount', 0)
        outputs = usage.get('output_tokens', 0) if provider == 'claude' else usage.get('candidatesTokenCount', 0) + usage.get('thoughtsTokenCount', 0)
        cost = (inputs * RATES[provider][0] + outputs * RATES[provider][1]) / 1e6
        results[provider] = {'passed': sum(passed), 'total': 6, 'per_case_pass': passed, 'grades': grades, 'usage': usage, 'estimated_usd': cost}
    save(target / 'results.json', {'results': results, 'does_not_certify_real_case_ground_truth': True, 'original_labels_changed': False})
    print(json.dumps(results))


if __name__ == '__main__':
    main()
