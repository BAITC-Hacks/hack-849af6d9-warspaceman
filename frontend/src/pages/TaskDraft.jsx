import { useState } from 'react'
import { createTask } from '../api/tasks'

export default function TaskDraft({ onCreated }) {
  const [draftText, setDraftText] = useState('')
  const [topic, setTopic] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  async function submit(event) {
    event.preventDefault(); setError('')
    try { const value = await createTask(draftText, topic || null); setResult(value); onCreated?.(value) } catch (reason) { setError(reason.message) }
  }
  return <section>
    <h1>Create task</h1>
    <form onSubmit={submit}>
      <label>Raw draft<textarea required value={draftText} onChange={(event) => setDraftText(event.target.value)} /></label>
      <label>Topic<input value={topic} onChange={(event) => setTopic(event.target.value)} /></label>
      <button type="submit">Submit draft</button>
    </form>
    {error && <p role="alert">{error}</p>}
    {result && <div><h2>Clarifying questions</h2><ol>{result.questions.map((question) => <li key={question.id}>{question.question_text}</li>)}</ol><p>Task #{result.task.id} is ready for answers.</p></div>}
  </section>
}
