import { useState } from 'react'
import Catalog from './pages/Catalog'
import TaskCard from './pages/TaskCard'
import TaskDetail from './pages/TaskDetail'
import TaskDraft from './pages/TaskDraft'

export default function App() {
  const [page, setPage] = useState('catalog'); const [role, setRole] = useState('business'); const [selectedTask, setSelectedTask] = useState(null); const [draft, setDraft] = useState(null)
  const openTask = (task) => { setSelectedTask(task); setPage('detail') }
  const finishTask = (task) => { setSelectedTask(task); setDraft(null); setPage('catalog') }
  return <main><nav aria-label="Main navigation"><button onClick={() => setPage('catalog')}>Catalog</button><button onClick={() => setPage('draft')}>Create task</button><span>Role: <button aria-pressed={role === 'business'} onClick={() => setRole('business')}>Business</button><button aria-pressed={role === 'student'} onClick={() => setRole('student')}>Student / Team</button></span></nav>{page === 'catalog' && <Catalog onSelect={openTask} />}{page === 'detail' && <TaskDetail task={selectedTask} role={role} />}{page === 'draft' && <TaskDraft onCreated={(result) => setDraft(result)} />}{page === 'card' && draft && <TaskCard task={draft.task} questions={draft.questions} onConfirmed={finishTask} />}{page === 'draft' && draft && <p><button onClick={() => setPage('card')}>Continue to task card</button></p>}</main>
}
