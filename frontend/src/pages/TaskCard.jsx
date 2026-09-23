import { useState } from 'react'
import { answerTask, confirmTask, getTaskRating, updateTask } from '../api/tasks'
import ReadinessScore from '../components/ReadinessScore'

const fields = ['title', 'context', 'need', 'users', 'data_materials', 'constraints', 'expected_result', 'success_criteria', 'contact', 'interaction_format', 'topic']
export default function TaskCard({ task, questions = [], taskId }) {
  const id = taskId || task?.id; const [answers, setAnswers] = useState(questions.map(() => '')); const [card, setCard] = useState(task || null); const [rating, setRating] = useState(null); const [saving, setSaving] = useState(false); const [error, setError] = useState('')
  if (!id) return <p>Provide a task id.</p>
  async function submitAnswers(event) { event.preventDefault(); setSaving(true); setError(''); try { setCard(await answerTask(id, answers)) } catch (reason) { setError(reason.message) } finally { setSaving(false) } }
  async function saveField(field, value) { try { setCard(await updateTask(id, { [field]: value })) } catch (reason) { setError(reason.message) } }
  async function confirm() { setSaving(true); setError(''); try { const next = await confirmTask(id); setCard(next); setRating(await getTaskRating(id)) } catch (reason) { setError(reason.message) } finally { setSaving(false) } }
  return <section><h1>Task card</h1>{error && <p role="alert">{error}</p>}{questions.length > 0 && <form onSubmit={submitAnswers}><h2>Answers</h2>{questions.map((question, index) => <label key={question.id}>{question.question_text}<textarea value={answers[index] || ''} onChange={(event) => setAnswers((current) => current.map((value, item) => item === index ? event.target.value : value))} /></label>)}<button disabled={saving}>{saving ? 'Saving…' : 'Save answers'}</button></form>}{card && <div><h2>Editable card</h2>{fields.map((field) => <label key={field}>{field}<input value={card[field] || ''} onChange={(event) => setCard({ ...card, [field]: event.target.value })} onBlur={(event) => saveField(field, event.target.value)} /></label>)}<button disabled={saving} onClick={confirm}>Confirm</button><p>Status: {card.status}</p><ReadinessScore task={card} rating={rating} /></div>}</section>
}
