"""Label-free literal field extraction and frozen embedding score composition."""

import re

import numpy as np


def spans(text, pattern):
    return [
        {"quote": match.group(), "start": match.start(), "end": match.end()}
        for match in re.finditer(pattern, text, re.I)
    ]


def field_profile(text, config, negation_guard, *, executed=False, context=""):
    clauses = spans(text, r"[^.;。；\n]+")
    supported = []
    held = []
    for clause in clauses:
        if executed and re.search(negation_guard, clause["quote"], re.I):
            held.append(clause)
        else:
            supported.append(clause)
    actions = []
    objects = []
    outputs = []
    for clause in supported:
        quote = clause["quote"]
        matches = list(re.finditer(config["action_pattern"], quote, re.I))
        for match in matches:
            actions.append({"quote": match.group(), "start": clause["start"] + match.start(),
                            "end": clause["start"] + match.end()})
        boundaries = [0] + [position for match in matches for position in (match.start(), match.end())] + [len(quote)]
        for start, end in zip(boundaries[::2], boundaries[1::2]):
            residual = quote[start:end]
            for match in re.finditer(r"[^,·:：/()]+", residual):
                raw = match.group()
                if re.sub(config["object_stopwords"], "", raw, flags=re.I).strip():
                    left = len(raw) - len(raw.lstrip())
                    right = len(raw.rstrip())
                    offset = clause["start"] + start + match.start()
                    objects.append({"quote": raw[left:right], "start": offset + left, "end": offset + right})
        for match in re.finditer(config["output_pattern"], quote, re.I):
            group = 1 if match.group(1) is not None else 2
            outputs.append({"quote": match.group(group), "start": clause["start"] + match.start(group),
                            "end": clause["start"] + match.end(group)})
    context_spans = spans(text, config["context_pattern"]) if not executed else []
    fields = {
        "task": "\n".join(clause["quote"].strip() for clause in supported),
        "action": "\n".join(dict.fromkeys(item["quote"] for item in actions)),
        "object": "\n".join(dict.fromkeys(item["quote"] for item in objects)),
        "output": "\n".join(dict.fromkeys(item["quote"] for item in outputs)),
        "context": context if executed else "\n".join(item["quote"] for item in context_spans),
    }
    if not fields["task"]:
        fields = dict.fromkeys(fields, "")
    return {"source_text": text, "fields": fields,
            "spans": {"task": supported, "action": actions, "object": objects, "output": outputs,
                      "context": spans(context, r"[^.;。；\n]+") if executed else context_spans},
            "held_clauses": held, "unknown_fields": [key for key, value in fields.items() if not value],
            "object_status": "SHALLOW_RESIDUAL_SPANS_NOT_VERIFIED_SEMANTIC_ROLES",
            "output_status": "EXPLICIT_LITERAL_ONLY" if outputs else "UNKNOWN",
            "task_status": "SUPPORTED_STRUCTURED_TASK_SUMMARY" if fields["task"] else "UNKNOWN",
            "execution_claim": "Task summary only; original publication not re-audited" if executed else "QUERY_NEED_NOT_EXECUTION"}


def compare_fields(query, case, embeddings, weights):
    components = {}
    if not query["fields"]["task"] or not case["fields"]["task"]:
        return {"score": -1.0, "components": {}, "status": "UNKNOWN_TASK", "available_weight": 0.0}
    for field, weight in weights.items():
        query_text = query["fields"][field]
        case_text = case["fields"][field]
        if query_text and case_text:
            cosine = float(np.clip(np.dot(embeddings[query_text], embeddings[case_text]), -1, 1))
            components[field] = {"cosine": cosine, "weight": weight}
    available = sum(item["weight"] for item in components.values())
    return {"score": sum(item["cosine"] * item["weight"] for item in components.values()) / available,
            "components": components, "available_weight": available,
            "status": "EMBEDDING_SIMILARITY_NOT_VERIFIED_RELEVANCE"}


def aggregate(whole, branches):
    return (whole + max(branches)) / 2 if branches else whole


def combined_score(rule_strength, semantic_score):
    return 0.5 * rule_strength / 4 + 0.5 * (semantic_score + 1) / 2


def ranking_key(score, retrieval_score, case_id):
    return -score, -retrieval_score, case_id
