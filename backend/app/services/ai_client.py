import logging
import re
from typing import Any

import httpx

from app.core.config import ML_SERVICE_URL

logger = logging.getLogger(__name__)


def _stub_questions(draft_text: str) -> list[str]:
    questions = [
        "What specific need or problem should this task address?",
        "Who are the intended users or beneficiaries?",
        "What result would show that the task is successful?",
    ]
    if not draft_text.strip():
        return questions
    return questions


async def get_clarifying_questions(draft_text: str, topic: str | None) -> list[str]:
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(f"{ML_SERVICE_URL}/generate-questions", json={"draft_text": draft_text, "topic": topic})
            response.raise_for_status()
            data = response.json()
            questions = data.get("questions", data) if isinstance(data, dict) else data
            if isinstance(questions, list) and len(questions) >= 3 and all(isinstance(q, str) for q in questions):
                return questions
    except Exception as exc:
        logger.warning("ML question generation failed; using deterministic fallback: %s", exc)
    return _stub_questions(draft_text)


def _extract_card(draft_text: str, questions: list[str], answers: list[str] | dict[str, str]) -> dict[str, Any]:
    answer_values = list(answers.values()) if isinstance(answers, dict) else answers
    text = draft_text.strip()
    card: dict[str, Any] = {field: None for field in ("title", "context", "need", "users", "data_materials", "constraints", "expected_result", "success_criteria", "contact", "interaction_format")}
    card["context"] = text or None
    if answer_values:
        mappings = ["need", "users", "success_criteria", "expected_result", "constraints", "data_materials", "contact", "interaction_format"]
        for field, answer in zip(mappings, answer_values):
            if str(answer).strip():
                card[field] = str(answer).strip()
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), None)
    card["title"] = first_line[:500] if first_line else None
    return card


async def build_card_from_answers(draft_text: str, questions: list[str], answers: list[str] | dict[str, str]) -> dict[str, Any]:
    payload = {"draft_text": draft_text, "questions": questions, "answers": answers}
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.post(f"{ML_SERVICE_URL}/form-card", json=payload)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and isinstance(data.get("card", data), dict):
                return data.get("card", data)
    except Exception as exc:
        logger.warning("ML card generation failed; using deterministic fallback: %s", exc)
    return _extract_card(draft_text, questions, answers)
