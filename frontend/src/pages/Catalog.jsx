import { useEffect, useState } from 'react'
import { listTasks } from '../api/tasks'
import ReadinessScore from '../components/ReadinessScore'

export default function Catalog({ onSelect }) {
  const [tasks, setTasks] = useState([]); const [topic, setTopic] = useState(''); const [readiness, setReadiness] = useState(''); const [sort, setSort] = useState(''); const [loading, setLoading] = useState(true); const [error, setError] = useState('')
  useEffect(() => { let active = true; setLoading(true); setError(''); listTasks({ topic, readiness_level: readiness, sort }).then((value) => { if (active) setTasks(value) }).catch((reason) => { if (active) setError(reason.message) }).finally(() => active && setLoading(false)); return () => { active = false } }, [topic, readiness, sort])
  return <section><h1>Task catalog</h1><label>Topic<input value={topic} onChange={(event) => setTopic(event.target.value)} /></label><label>Readiness<select value={readiness} onChange={(event) => setReadiness(event.target.value)}><option value="">All</option><option value="draft">Draft</option><option value="partial">Partial</option><option value="ready">Ready</option></select></label><label>Sort<select value={sort} onChange={(event) => setSort(event.target.value)}><option value="">Default</option><option value="rating">Rating</option></select></label>{loading && <p>Loading tasks…</p>}{error && <p role="alert">{error}</p>}{!loading && !error && tasks.length === 0 && <p>No confirmed tasks found.</p>}<ul>{tasks.map((task) => <li key={task.id}><button onClick={() => onSelect?.(task)}>{task.title || `Task #${task.id}`}</button><p>{task.context || 'No context provided.'}</p><ReadinessScore task={task} /></li>)}</ul></section>
}
