from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.models import ClarifyingQuestion, Task
from app.schemas import AnswersSubmit, QuestionRead, TaskCreate, TaskRead, TaskUpdate, TaskWithQuestions
from app.services.ai_client import build_card_from_answers, get_clarifying_questions
from app.services.rating import calculate_rating, readiness_for_score

router = APIRouter(tags=["tasks"])


async def _get_task(task_id: int, db: AsyncSession) -> Task:
    result = await db.execute(select(Task).options(selectinload(Task.questions)).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks", response_model=TaskWithQuestions, status_code=201)
async def create_task(payload: TaskCreate, db: AsyncSession = Depends(get_db)):
    task = Task(context=payload.draft_text, topic=payload.topic, status="clarifying")
    db.add(task)
    await db.flush()
    questions = await get_clarifying_questions(payload.draft_text, payload.topic)
    task.questions = [ClarifyingQuestion(task_id=task.id, question_text=q, order=i) for i, q in enumerate(questions, 1)]
    await db.commit()
    task = await _get_task(task.id, db)
    return {"task": task, "questions": task.questions}


@router.patch("/tasks/{task_id}/answers", response_model=TaskRead)
async def answer_task(task_id: int, payload: AnswersSubmit, db: AsyncSession = Depends(get_db)):
    task = await _get_task(task_id, db)
    questions = sorted(task.questions, key=lambda q: q.order)
    answer_values = list(payload.answers.values()) if isinstance(payload.answers, dict) else payload.answers
    for question, answer in zip(questions, answer_values):
        question.answer_text = answer
    card = await build_card_from_answers(task.context or "", [q.question_text for q in questions], payload.answers)
    for field, value in card.items():
        if hasattr(task, field) and field not in {"id", "status"}:
            setattr(task, field, value)
    task.status = "card_ready"
    await db.commit()
    return task


@router.patch("/tasks/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, payload: TaskUpdate, db: AsyncSession = Depends(get_db)):
    task = await _get_task(task_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "status" and value not in {"draft", "clarifying", "card_ready", "confirmed"}:
            raise HTTPException(status_code=422, detail="Invalid task status")
        setattr(task, field, value)
    await db.commit()
    return task


@router.post("/tasks/{task_id}/confirm", response_model=TaskRead)
async def confirm_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await _get_task(task_id, db)
    score, breakdown, missing = calculate_rating(task)
    task.rating_score = score
    task.rating_breakdown = breakdown
    task.readiness_level = readiness_for_score(score)
    task.status = "confirmed"
    await db.commit()
    return task


@router.get("/tasks/{task_id}/rating")
async def task_rating(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await _get_task(task_id, db)
    score, breakdown, missing = calculate_rating(task)
    return {"score": score, "breakdown": breakdown, "missing_fields": missing}


@router.get("/tasks", response_model=list[TaskRead])
async def list_tasks(topic: str | None = None, readiness_level: str | None = None, sort: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    query = select(Task).where(Task.status == "confirmed")
    if topic:
        query = query.where(Task.topic == topic)
    if readiness_level:
        query = query.where(Task.readiness_level == readiness_level)
    if sort == "rating":
        query = query.order_by(Task.rating_score.desc())
    result = await db.execute(query)
    return list(result.scalars().all())
