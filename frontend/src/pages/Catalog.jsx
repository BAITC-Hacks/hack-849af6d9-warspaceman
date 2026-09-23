import { useEffect, useState } from 'react'
import { listTasks } from '../api/tasks'

export default function Catalog({ onSelect }) {
  const [tasks, setTasks] = useState([]); const [topic, setTopic] = useState(''); const [readiness, setReadiness] = useState(''); const [sort, setSort] = useState(''); const [error, setError] = useState('')
  useEffect(() => { listTasks({ topic, readiness_level: readiness, sort }).then(setTasks).catch((reason) => setError(reason.message)) }, [topic, readiness, sort])
  return <section><h1>Task catalog</h1><label>Topic<input value={topic} onChange={(event) => setTopic(event.target.value)} /></label><label>Readiness<select value={readiness} onChange={(event) => setReadiness(event.target.value)}><option value="">All</option><option value="draft">Draft</option><option value="partial">Partial</option><option value="ready">Ready</option></select></label><label>Sort<select value={sort} onChange={(event) => setSort(event.target.value)}><option value="">Newest</option><option value="rating">Rating</option></select></label>{error && <p role="alert">{error}</p>}<ul>{tasks.map((task) => <li key={task.id}><button onClick={() => onSelect?.(task)}>{task.title || `Task #${task.id}`}</button> — {task.topic || 'No topic'} — rating {task.rating_score} — {task.readiness_level}</li>)}</ul></section>
}
