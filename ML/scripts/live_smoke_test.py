"""Optional paid smoke test for the configured local OpenAI-backed service."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

ML_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_ROOT))

from service import main  # noqa: E402


BASE_URL = "http://127.0.0.1:8001"
SYNTHETIC_DRAFT = "A school club needs a simple way to schedule its weekly robotics sessions."
SYNTHETIC_TOPIC = "Synthetic robotics club scheduling demo"
SYNTHETIC_ANSWERS = {
    "users": "Synthetic answer: robotics club students and instructor",
    "data_materials": "Synthetic answer: a sample room schedule and kit inventory",
    "success_criteria": "Synthetic answer: 90% of sessions start on time",
    "contact": "Synthetic answer: demo contact only",
}


def post_json(path: str, payload: dict[str, object]) -> tuple[dict[str, object], str]:
    request = Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8")), response.headers.get("X-Generation-Mode", "missing")


def main_run() -> int:
    if not main._configured_api_key():
        print(json.dumps({"error": "A configured OpenAI key is required; live smoke test not run."}))
        return 2

    try:
        questions, questions_mode = post_json(
            "/generate-questions",
            {"draft_text": SYNTHETIC_DRAFT, "topic": SYNTHETIC_TOPIC},
        )
        if not isinstance(questions, list) or not all(isinstance(item, str) for item in questions):
            print(json.dumps({"schema_valid": False, "error": "Question response schema invalid."}))
            return 1

        answers = {}
        for question in questions:
            field = main._field_for_question(question)
            if field in SYNTHETIC_ANSWERS:
                answers[question] = SYNTHETIC_ANSWERS[field]

        card, card_mode = post_json(
            "/form-card",
            {"draft_text": SYNTHETIC_DRAFT, "questions": questions, "answers": answers},
        )
        schema_valid = (
            isinstance(card, dict)
            and set(card) == set(main.CARD_FIELDS)
            and all(value is None or isinstance(value, str) for value in card.values())
        )
        evidence = [SYNTHETIC_DRAFT, *answers.values()]
        evidence_check = schema_valid and all(
            value is None or any(value in source for source in evidence)
            for value in card.values()
        )
        user_mapping_check = card.get("users") == SYNTHETIC_ANSWERS["users"]
        data_mapping_check = card.get("data_materials") == SYNTHETIC_ANSWERS["data_materials"]
        contact_excluded = (
            schema_valid
            and SYNTHETIC_ANSWERS["contact"] not in json.dumps(card, ensure_ascii=False)
        )
        result = {
            "schema_valid": schema_valid,
            "generation_modes": {
                "generate_questions": questions_mode,
                "form_card": card_mode,
            },
            "evidence_check": evidence_check,
            "expected_answer_mapping": {
                "users": user_mapping_check,
                "data_materials": data_mapping_check,
            },
            "contact_excluded": contact_excluded,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if all(
            (schema_valid, evidence_check, user_mapping_check, data_mapping_check, contact_excluded)
        ) else 1
    except (URLError, TimeoutError, ValueError):
        print(json.dumps({"error": "Smoke test could not complete; check service availability and configuration."}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main_run())
