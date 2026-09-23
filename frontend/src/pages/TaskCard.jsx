import { useEffect, useState } from 'react'
import { answerTask, confirmTask, getTaskRating, updateTask } from '../api/tasks'

const fields = ['title', 'context', 'need', 'users', 'data_materials', 'constraints', 'expected_result', 'success_criteria', 'contact', 'interaction_format', 'topic']

export default function TaskCard({ task, questions = [], taskId }) {
  const id = taskId || task?.id
  const [answers, setAnswers] = useState(() => questions.map(() => ''))
  const [card, setCard] = useState(task || null)
  const [rating, setRating] = useState(null)
  const [message, setMessage] = useState('')
  useEffect(() => { if (task) setCard(task) }, [task])
  if (!id) return <p>Provide a task id.</p>
  async function submitAnswers(event) { event.preventDefault(); setCard(await answerTask(id, answers)) }
  async function saveField(field, value) { const next = await updateTask(id, { [field]: value }); setCard(next) }
  async function confirm() { const next = await confirmTask(id); setCard(next); setRating(await getTaskRating(id)); setMessage('Task confirmed') }
  return <section>
    <h1>Task card</h1>
    {questions.length > 0 && <form onSubmit={submitAnswers}><h2>Answers</h2>{questions.map((question, index) => <label key={question.id}>{question.question_text}<textarea value={answers[index] || ''} onChange={(event) => setAnswers((current) => current.map((value, item) => item === index ? event.target.value : value))} /></label>)}<button>Save answers</button></form>}
    {card && <div><h2>Editable card</h2>{fields.map((field) => <label key={field}>{field}<input value={card[field] || ''} onChange={(event) => setCard({ ...card, [field]: event.target.value })} onBlur={(event) => saveField(field, event.target.value)} /></label>)}<button onClick={confirm}>Confirm</button><p>Status: {card.status}</p></div>}
    {message && <p>{message}</p>}{rating && <div><h2>Rating: {rating.score}</h2><pre>{JSON.stringify(rating, null, 2)}</pre></div>}
  </section>
}
