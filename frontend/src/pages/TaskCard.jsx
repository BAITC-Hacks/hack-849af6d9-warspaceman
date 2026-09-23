import { useState } from 'react'
import { answerTask, confirmTask, getTaskRating, updateTask } from '../api/tasks'
import ReadinessScore from '../components/ReadinessScore'

const fields = ['title', 'context', 'need', 'users', 'data_materials', 'constraints', 'expected_result', 'success_criteria', 'contact', 'interaction_format', 'topic']

export default function TaskCard({ task, questions = [], taskId, onConfirmed }) {
  const id = taskId || task?.id
  const [answers, setAnswers] = useState(questions.map(() => ''))
  const [card, setCard] = useState(task || null)
  const [rating, setRating] = useState(null)
  const [action, setAction] = useState(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  if (!id) return <p>Provide a task id.</p>

  const cardPayload = () => Object.fromEntries(fields.map((field) => [field, card?.[field] ?? null]))

  async function submitAnswers(event) {
    event.preventDefault()
    setAction('answers'); setError(''); setSuccess('')
    try {
      const generatedCard = await answerTask(id, answers)
      setCard(generatedCard)
      try { setRating(await getTaskRating(id)) } catch (reason) { setError(`Task card created, but rating could not be loaded: ${reason.message}`) }
    } catch (reason) { setError(reason.message) } finally { setAction(null) }
  }

  async function saveAndRecalculate() {
    setAction('recalculate'); setError(''); setSuccess('')
    try {
      const savedCard = await updateTask(id, cardPayload())
      setCard(savedCard)
      setRating(await getTaskRating(id))
      setSuccess('Task saved and readiness recalculated.')
    } catch (reason) { setError(reason.message) } finally { setAction(null) }
  }

  async function publish() {
    setAction('publish'); setError(''); setSuccess('')
    try {
      await updateTask(id, cardPayload())
      const confirmedTask = await confirmTask(id)
      setCard(confirmedTask)
      onConfirmed?.(confirmedTask)
    } catch (reason) { setError(reason.message) } finally { setAction(null) }
  }

  return <section><h1>Task card</h1>{error && <p role="alert">{error}</p>}{success && <p role="status">{success}</p>}{questions.length > 0 && <form onSubmit={submitAnswers}><h2>Clarifying questions</h2>{questions.map((question, index) => <label key={question.id}>{question.question_text}<textarea aria-label={question.question_text} value={answers[index] || ''} onChange={(event) => setAnswers((current) => current.map((value, item) => item === index ? event.target.value : value))} /></label>)}<button disabled={action !== null}>{action === 'answers' ? 'Saving…' : 'Save answers'}</button></form>}{card && <div><h2>Editable task card</h2>{fields.map((field) => <label key={field}>{field}<input aria-label={field} value={card[field] || ''} onChange={(event) => setCard({ ...card, [field]: event.target.value })} /></label>)}<div className="button-row task-actions"><button className="secondary" disabled={action !== null} onClick={saveAndRecalculate}>{action === 'recalculate' ? 'Recalculating…' : 'Save & recalculate'}</button><button disabled={action !== null} onClick={publish}>{action === 'publish' ? 'Publishing…' : 'Publish task'}</button></div><p>Status: <span className={`status-badge status-${card.status}`}>{card.status}</span></p><ReadinessScore task={card} rating={rating} /></div>}</section>
}
