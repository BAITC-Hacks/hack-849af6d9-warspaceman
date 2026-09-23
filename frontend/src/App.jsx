import { useState } from 'react'
import Catalog from './pages/Catalog'
import TaskCard from './pages/TaskCard'
import TaskDetail from './pages/TaskDetail'
import TaskDraft from './pages/TaskDraft'

export default function App() {
  const [page, setPage] = useState('catalog'); const [selectedTask, setSelectedTask] = useState(null); const [draft, setDraft] = useState(null)
  return <main><nav aria-label="Main navigation"><button onClick={() => setPage('catalog')}>Catalog</button><button onClick={() => setPage('draft')}>Create task</button></nav>{page === 'catalog' && <Catalog onSelect={(task) => { setSelectedTask(task); setPage('detail') }} />}{page === 'detail' && <TaskDetail task={selectedTask} />}{page === 'draft' && <TaskDraft onCreated={(result) => setDraft(result)} />}{page === 'card' && draft && <TaskCard task={draft.task} questions={draft.questions} />}{page === 'draft' && draft && <p><button onClick={() => setPage('card')}>Continue to task card</button></p>}</main>
}
