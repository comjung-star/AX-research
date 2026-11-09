"""One bounded corpus-blind Claude author request; never masquerade as human data."""
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone

from scripts.improvement_cycle import ROOT, read

OUT = ROOT / 'docs/independent-validation-20261108/ai_pilot'
MODEL = 'claude-sonnet-5-5'
SYSTEM = 'You write realistic fictional Korean business problem questions. You have no access to any case corpus, previous questions, rankings or research results. Treat this as a fresh authoring task. Return only valid JSON, without Markdown.'
PROMPT = '''Write exactly40 distinct Korean business workflow questions,4 for each sector:
manufacturing, logistics, retail, customer_service, finance, healthcare, public_services,
human_resources, construction, energy. Use ordinary plausible workplace problems,
not named real companies or unsupported factual claims. Vary the actual requested
operations, input types, outputs, workflow and constraints; changing industry names
alone does not make questions different. Include narrow and multi-step workflows,
current monitoring and future planning, human approval boundaries and realistic
uncertainty. Do not assume any supporting case exists. Do not suggest algorithms,
vendors, AI products, answers, reference cases, relevance labels or solutions.
Each problem should stand alone and be understandable to a business practitioner.
Return {"questions":[{"query_id":"IVQ001","sector":"manufacturing",
"business_problem":"Korean2-4sentences describing the need",
"input":"explicit input","desired_output":"explicit output",
"constraints":"explicit limits or empty string"},...]}. IDs IVQ001 through IVQ040,
ordered by the10sectors listed,4each. The full question must contain its essential
inputs, desired outputs and constraints in business_problem, not only metadata.
Do not provide any relevance grading or assessment of how easy a question is.'''


def save(path, value):
    text = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    for name in ('ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'GEMINI_API_KEY'):
        secret = os.environ.get(name)
        if secret and secret in text:
            raise ValueError('Refusing to save secret')
    with path.open('x', encoding='utf-8') as target:
        target.write(text)


def parse_output(response):
    text = ''.join(block.get('text', '') for block in response.get('content', []) if block.get('type') == 'text').strip()
    text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text).strip()
    data = json.loads(text)
    rows = data['questions']
    assert len(rows) == 40
    assert [row['query_id'] for row in rows] == [f'IVQ{position:03d}' for position in range(1, 41)]
    assert len({row['business_problem'].strip() for row in rows}) == 40
    required = {'query_id', 'sector', 'business_problem', 'input', 'desired_output', 'constraints'}
    assert all(set(row) == required and all(isinstance(value, str) for value in row.values()) for row in rows)
    assert all(row['business_problem'].strip() and row['input'].strip() and row['desired_output'].strip() for row in rows)
    return rows


def main():
    if OUT.exists():
        raise FileExistsError('Existing AI author run: inspect receipt; do not silently retry')
    OUT.mkdir()
    body = {'model': MODEL, 'max_tokens': 14000, 'system': SYSTEM,
            'messages': [{'role': 'user', 'content': PROMPT}], 'output_config': {'effort': 'low'}}
    reserve = (len(json.dumps(body, ensure_ascii=False).encode()) + 2000) * 2 / 1e6 + 14000 * 10 / 1e6
    assert reserve < 2
    save(OUT / 'author_preregistration.json', {'state': 'FROZEN_BEFORE_AUTHOR_REQUEST', 'request': body,
         'limit_usd': 2, 'reserved_upper_usd': reserve, 'input_rate_per_million': 2, 'output_rate_per_million': 10,
         'pricing_source': 'https://platform.claude.com/docs/en/about-claude/pricing', 'price_checked': '2026-11-08',
         'user_authorized_claude_ai_author_instead_of_human': True, 'human_gold': False,
         'source_corpus_or_old_results_in_request': False, 'retries': 0,
         'role': 'AI_GENERATED_CORPUS_BLIND_PILOT_NOT_HUMAN_AUTHORED_FINAL_TEST',
         'frozen_model_sha256': read('docs/independent-validation-20261108/source_freeze.json')['sha256']})
    receipt = {'state': 'ATTEMPT_RESERVED', 'reserved_upper_usd': reserve,
               'started_utc': datetime.now(timezone.utc).isoformat(),
               'request_sha256': hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode()).hexdigest()}
    save(OUT / 'author_attempt.json', receipt)
    headers = {'x-api-key': os.environ['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'}
    request = urllib.request.Request('https://api.anthropic.com/v1/messages', json.dumps(body).encode(), headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        save(OUT / 'author_failure.json', {'state': 'HTTP_FAILURE_NO_RETRY', 'status': error.code})
        raise RuntimeError('Claude author request failed; status=' + str(error.code)) from None
    except Exception:
        save(OUT / 'author_failure.json', {'state': 'UNKNOWN_DELIVERY_NO_RETRY', 'reservation_retained': True})
        raise RuntimeError('Claude author delivery uncertain; no automatic retry') from None
    save(OUT / 'author_response.json', result)
    usage = result['usage']
    cost = (usage.get('input_tokens', 0) * 2 + usage.get('output_tokens', 0) * 10) / 1e6
    save(OUT / 'author_receipt.json', {'state': 'RESPONSE_RECEIVED', 'response_id': result.get('id'),
         'returned_model': result.get('model'), 'usage': usage, 'estimated_usd': cost,
         'stop_reason': result.get('stop_reason'), 'finished_utc': datetime.now(timezone.utc).isoformat()})
    assert result.get('stop_reason') == 'end_turn', 'Output incomplete; original response retained'
    rows = parse_output(result)
    save(OUT / 'claude_authored_questions.json', {'state': 'AI_AUTHOR_OUTPUT_NOT_YET_SCREENED', 'questions': rows})
    with (OUT / 'questions.jsonl').open('x', encoding='utf-8') as target:
        for row in rows:
            target.write(json.dumps({'query_id': row['query_id'], 'text': row['business_problem'], 'split': 'AI_BLIND_PILOT'}, ensure_ascii=False) + '\n')
    print(json.dumps({'state': 'CLAUDE_BLIND_AUTHOR_COMPLETE', 'questions': len(rows), 'model': result.get('model'),
                      'estimated_usd': cost, 'human_authored': False, 'old_cases_or_results_sent': False}))


if __name__ == '__main__':
    main()
