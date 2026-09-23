from fastapi.testclient import TestClient

from service import main


client = TestClient(main.app)
CARD_FIELDS = {
    "context",
    "need",
    "users",
    "data_materials",
    "constraints",
    "expected_result",
    "success_criteria",
}


def test_questions_are_three_distinct_and_follow_russian_input(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.post(
        "/generate-questions",
        json={"draft_text": "Нужен инструмент для подготовки отчетов.", "topic": "Отчеты"},
    )
    questions = response.json()
    assert response.status_code == 200
    assert len(questions) >= 3
    assert len(set(questions)) == len(questions)
    assert all(any("а" <= ch.lower() <= "я" for ch in question) for question in questions)
    assert response.headers["X-Generation-Mode"] == "rule-based-stub"


def test_explicitly_complete_draft_still_gets_three_distinct_questions(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    draft = "\n".join(
        [
            "context: Team workflow",
            "need: Prepare reports",
            "users: Analysts",
            "data: CSV exports",
            "constraints: Monthly deadline",
            "expected_result: Report",
            "success_criteria: Fewer errors",
            "contact: Alex",
            "interaction_format: Chat",
        ]
    )
    response = client.post("/generate-questions", json={"draft_text": draft, "topic": "Reports"})
    questions = response.json()
    assert response.status_code == 200
    assert len(questions) >= 3
    assert len(questions) == len(set(questions))


def test_rule_based_fallback_maps_english_answers_and_marks_mode(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.post(
        "/form-card",
        json={
            "draft_text": "Create a reporting tool.",
            "questions": ["Who will use the solution?", "What source data is available?"],
            "answers": {
                "Who will use the solution?": "Finance analysts.",
                "What source data is available?": "Monthly CSV exports.",
            },
        },
    )
    assert response.status_code == 200
    assert set(response.json()) == CARD_FIELDS
    assert response.json()["users"] == "Finance analysts."
    assert response.json()["data_materials"] == "Monthly CSV exports."
    assert response.json()["need"] == "Create a reporting tool."
    assert response.headers["X-Generation-Mode"] == "rule-based-stub"
    assert "no api key" in response.headers["X-Generation-Notice"].lower()


def test_rule_based_fallback_maps_russian_answer_by_question(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.post(
        "/form-card",
        json={
            "draft_text": "",
            "questions": ["Кто будет пользоваться решением?"],
            "answers": {"Кто будет пользоваться решением?": "Учителя и родители."},
        },
    )
    assert response.status_code == 200
    assert response.json()["users"] == "Учителя и родители."
    assert response.json()["need"] is None


def test_unknown_values_are_null_and_card_has_exact_fields(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.post("/form-card", json={"draft_text": "", "questions": [], "answers": {}})
    assert response.status_code == 200
    assert set(response.json()) == CARD_FIELDS
    assert all(value is None for value in response.json().values())


def test_ai_maps_answers_to_their_question_field_and_filters_inventions(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class FakeResponses:
        def parse(self, *, input, **kwargs):
            assert "'answers_by_field'" in input[1]["content"]
            assert "Finance analysts" in input[1]["content"]
            card = main.TaskCard(
                context=None,
                need="Create a tool.",
                users="Finance analysts",
                data_materials="Finance analysts",  # wrong question field
                constraints=None,
                expected_result="An invented dashboard",  # unsupported
                success_criteria=None,
            )
            return type("Result", (), {"output_parsed": card})()

    class FakeClient:
        responses = FakeResponses()

        def __init__(self, **kwargs):
            pass

    monkeypatch.setattr(main, "OpenAI", FakeClient)
    response = client.post(
        "/form-card",
        json={
            "draft_text": "Create a tool.",
            "questions": ["Who will use it?"],
            "answers": {"Who will use it?": "Finance analysts"},
        },
    )
    assert response.status_code == 200
    assert set(response.json()) == CARD_FIELDS
    assert response.json()["users"] == "Finance analysts"
    assert response.json()["data_materials"] is None
    assert response.json()["expected_result"] is None
    assert response.headers["X-Generation-Mode"] == "openai"


def test_provider_failure_returns_controlled_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def provider_failure(*args, **kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(main, "_model_card", provider_failure)
    response = client.post("/form-card", json={"draft_text": "", "questions": [], "answers": {}})
    assert response.status_code == 502
    assert response.json() == {"detail": "Task card generation failed."}


def test_malformed_ai_response_returns_controlled_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class FakeResponses:
        def parse(self, **kwargs):
            return type("Result", (), {"output_parsed": None})()

    class FakeClient:
        responses = FakeResponses()

        def __init__(self, **kwargs):
            pass

    monkeypatch.setattr(main, "OpenAI", FakeClient)
    response = client.post("/form-card", json={"draft_text": "", "questions": [], "answers": {}})
    assert response.status_code == 502
    assert response.json() == {"detail": "Task card generation failed."}


def test_question_provider_failure_returns_controlled_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def provider_failure(*args, **kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(main, "_model_supplied_fields", provider_failure)
    response = client.post("/generate-questions", json={"draft_text": "", "topic": "Reports"})
    assert response.status_code == 502
    assert response.json() == {"detail": "Question generation failed."}


def test_malformed_question_response_returns_controlled_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class FakeResponses:
        def parse(self, **kwargs):
            return type("Result", (), {"output_parsed": None})()

    class FakeClient:
        responses = FakeResponses()

        def __init__(self, **kwargs):
            pass

    monkeypatch.setattr(main, "OpenAI", FakeClient)
    response = client.post("/generate-questions", json={"draft_text": "", "topic": "Reports"})
    assert response.status_code == 502
    assert response.json() == {"detail": "Question generation failed."}
