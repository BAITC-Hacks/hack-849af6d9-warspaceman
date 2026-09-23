import json
from pathlib import Path

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


def test_five_synthetic_demo_drafts_have_varying_completeness(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    demo_path = Path(__file__).parents[1] / "examples" / "demo_drafts.json"
    drafts = json.loads(demo_path.read_text(encoding="utf-8"))["drafts"]
    completeness = {len(main._explicit_fields(draft["draft_text"])) for draft in drafts}

    assert len(drafts) == 5
    assert len(completeness) >= 3
    for draft in drafts:
        questions_response = client.post(
            "/generate-questions",
            json={"draft_text": draft["draft_text"], "topic": draft["topic"]},
        )
        assert questions_response.status_code == 200
        questions = questions_response.json()
        card_response = client.post(
            "/form-card",
            json={
                "draft_text": draft["draft_text"],
                "questions": questions,
                "answers": draft["answers"],
            },
        )
        assert card_response.status_code == 200
        assert set(card_response.json()) == CARD_FIELDS


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
            "questions": [
                "Кто будет пользоваться решением?",
                "Как вы будете оценивать успешность результата?",
            ],
            "answers": {
                "Кто будет пользоваться решением?": "Учителя и родители.",
                "Как вы будете оценивать успешность результата?": "Участники завершат пилот.",
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["users"] == "Учителя и родители."
    assert response.json()["success_criteria"] == "Участники завершат пилот."
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
            evidence = json.loads(input[1]["content"])
            assert evidence["question_answer_pairs"] == [
                {"question": "Who will use it?", "answer": "Finance analysts"}
            ]
            assert "untrusted data" in input[0]["content"]
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
        raise RuntimeError("test-key provider unavailable")

    monkeypatch.setattr(main, "_model_card", provider_failure)
    response = client.post("/form-card", json={"draft_text": "", "questions": [], "answers": {}})
    assert response.status_code == 502
    assert response.json() == {"detail": "Task card generation failed."}
    assert "test-key" not in response.text


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


def test_generated_question_flow_ignores_misleading_english_and_russian_topics(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cases = [
        {
            "draft_text": "We need a better onboarding process.",
            "topic": "Customer data requirements",
            "users_prefix": "Who will use",
            "data_prefix": "What source data",
            "success_prefix": "How will you determine",
            "contact_prefix": "Who should be contacted",
        },
        {
            "draft_text": "Нужен более понятный процесс адаптации.",
            "topic": "Требования к данным пользователей",
            "users_prefix": "Кто будет пользоваться",
            "data_prefix": "Какие данные",
            "success_prefix": "Как вы будете оценивать",
            "contact_prefix": "С кем можно связаться",
        },
    ]
    for case in cases:
        generated = client.post(
            "/generate-questions",
            json={"draft_text": case["draft_text"], "topic": case["topic"]},
        )
        assert generated.status_code == 200
        questions = generated.json()
        assert len(questions) >= 3
        assert len(questions) == len(set(questions))
        user_question = next(q for q in questions if q.startswith(case["users_prefix"]))
        data_question = next(q for q in questions if q.startswith(case["data_prefix"]))
        success_question = next(q for q in questions if q.startswith(case["success_prefix"]))
        contact_question = next(q for q in questions if q.startswith(case["contact_prefix"]))
        contact_answer = "Contact details supplied for follow-up only."
        answers = {
            user_question: "Finance analysts",
            data_question: "Monthly CSV exports",
            success_question: "At least 90% complete onboarding",
            contact_question: contact_answer,
        }
        card_response = client.post(
            "/form-card",
            json={"draft_text": case["draft_text"], "questions": questions, "answers": answers},
        )
        card = card_response.json()
        assert card_response.status_code == 200
        assert set(card) == CARD_FIELDS
        assert card["users"] == "Finance analysts"
        assert card["data_materials"] == "Monthly CSV exports"
        assert card["success_criteria"] == "At least 90% complete onboarding"
        assert contact_answer not in json.dumps(card, ensure_ascii=False)


def test_generated_followup_question_flow_maps_fields_despite_topic_keywords(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    draft = "\n".join(
        [
            "context: Existing workflow",
            "need: Improve the workflow",
            "users: Operations staff",
            "data: Monthly records",
            "constraints: Two-week pilot",
            "expected_result: A revised workflow",
            "success_criteria: Fewer errors",
            "contact: Pilot coordinator",
            "interaction_format: Weekly meetings",
        ]
    )
    for topic, prefixes in [
        (
            "Customer data requirements",
            ("Is there any additional detail to add about users", "Is there any additional detail to add about data materials"),
        ),
        (
            "Требования к данным пользователей",
            ("Есть ли дополнительные сведения о пользователях", "Есть ли дополнительные сведения о данных и материалах"),
        ),
    ]:
        generated = client.post("/generate-questions", json={"draft_text": draft, "topic": topic})
        questions = generated.json()
        assert len(questions) >= 3
        user_question = next(q for q in questions if q.startswith(prefixes[0]))
        data_question = next(q for q in questions if q.startswith(prefixes[1]))
        answers = {user_question: "Support analysts", data_question: "Approved CSV exports"}
        response = client.post(
            "/form-card",
            json={"draft_text": draft, "questions": questions, "answers": answers},
        )
        assert response.status_code == 200
        assert response.json()["users"] == "Support analysts"
        assert response.json()["data_materials"] == "Approved CSV exports"


def test_ambiguous_fallback_question_is_not_guessed(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.post(
        "/form-card",
        json={
            "draft_text": "",
            "questions": ["What should we document about user data requirements?"],
            "answers": {
                "What should we document about user data requirements?": "Team roster",
                "Which details should we clarify for ‘users’?": "Another ambiguous answer",
            },
        },
    )
    assert response.status_code == 200
    assert all(value is None for value in response.json().values())


def test_whole_answer_placeholders_stay_unknown_and_trigger_questions(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    drafts = [
        ("Users: TBD", "Who will use the solution", "users"),
        ("Пользователи: не знаю", "Кто будет пользоваться решением", "users"),
        ("Success criteria: not sure", "How will you determine whether the result is successful", "success_criteria"),
        ("Критерии успеха: уточним позже", "Как вы будете оценивать успешность результата", "success_criteria"),
    ]
    for draft, expected_prompt, field in drafts:
        generated = client.post(
            "/generate-questions", json={"draft_text": draft, "topic": "Placeholder check"}
        )
        questions = generated.json()
        assert generated.status_code == 200
        assert len(questions) >= 3
        assert any(question.startswith(expected_prompt) for question in questions)
        card = client.post(
            "/form-card", json={"draft_text": draft, "questions": [], "answers": {}}
        ).json()
        assert card[field] is None


def test_only_whole_placeholders_are_discarded_and_negative_statements_remain(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.post(
        "/form-card",
        json={
            "draft_text": (
                "Constraints: No personal data may be used.\n"
                "Data: TBD\n"
                "Need: Budget absent"
            ),
            "questions": ["What source data is available?", "Who will use the solution?"],
            "answers": {
                "What source data is available?": "Not sure which formats yet; monthly CSV exports are available.",
                "Who will use the solution?": "not sure",
            },
        },
    )
    card = response.json()
    assert response.status_code == 200
    assert card["constraints"] == "No personal data may be used."
    assert card["data_materials"] == "Not sure which formats yet; monthly CSV exports are available."
    assert card["need"] == "Budget absent"
    assert card["users"] is None


def test_ai_question_presence_prompt_hides_only_labelled_whole_placeholders(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class FakeResponses:
        def parse(self, *, input, **kwargs):
            draft = input[1]["content"]
            assert "Users: TBD" not in draft
            assert "Constraints: No personal data may be used." in draft
            parsed = main.FieldPresence(**{field: False for field in main.FieldPresence.model_fields})
            return type("Result", (), {"output_parsed": parsed})()

    class FakeClient:
        responses = FakeResponses()

        def __init__(self, **kwargs):
            pass

    monkeypatch.setattr(main, "OpenAI", FakeClient)
    assert main._model_supplied_fields(
        main.GenerateQuestionsRequest(
            draft_text="Users: TBD\nConstraints: No personal data may be used.", topic="Data"
        ),
        "test-key",
    ) == set()


def test_ai_prompt_keeps_placeholder_pair_evidence_but_rejects_placeholder_value(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    question = "Who will use the solution?"

    class FakeResponses:
        def parse(self, *, input, **kwargs):
            evidence = json.loads(input[1]["content"])
            assert evidence["question_answer_pairs"] == [{"question": question, "answer": "not sure"}]
            assert "whole answer" in input[0]["content"]
            parsed = main.TaskCard(
                context=None, need=None, users="not sure", data_materials=None,
                constraints=None, expected_result=None, success_criteria=None,
            )
            return type("Result", (), {"output_parsed": parsed})()

    class FakeClient:
        responses = FakeResponses()

        def __init__(self, **kwargs):
            pass

    monkeypatch.setattr(main, "OpenAI", FakeClient)
    response = client.post(
        "/form-card",
        json={"draft_text": "", "questions": [question], "answers": {question: "not sure"}},
    )
    assert response.status_code == 200
    assert response.json()["users"] is None


def test_ai_can_interpret_unknown_question_and_receives_original_pair(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    unfamiliar_question = "Which groups are affected in their day-to-day work?"
    answer = "Night-shift librarians"

    class FakeResponses:
        def parse(self, *, input, **kwargs):
            evidence = json.loads(input[1]["content"])
            assert evidence["draft_text"] == ""
            assert evidence["questions"] == [unfamiliar_question]
            assert evidence["question_answer_pairs"] == [
                {"question": unfamiliar_question, "answer": answer}
            ]
            card = main.TaskCard(
                context=None,
                need=None,
                users=answer,
                data_materials="Invented data source",
                constraints=None,
                expected_result=None,
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
            "draft_text": "",
            "questions": [unfamiliar_question],
            "answers": {unfamiliar_question: answer},
        },
    )
    assert response.status_code == 200
    assert response.json()["users"] == answer
    assert response.json()["data_materials"] is None
