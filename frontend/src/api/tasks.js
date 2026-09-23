const API_BASE = (import.meta?.env?.VITE_API_BASE_URL || '').replace(/\/$/, '')

let mockTaskId = 1
const mockTasks = []
const mockQuestions = new Map()

const now = () => new Date().toISOString()

const emptyTask = (id, values = {}) => ({
  id,
  title: null,
  context: null,
  need: null,
  users: null,
  data_materials: null,
  constraints: null,
  expected_result: null,
  success_criteria: null,
  contact: null,
  interaction_format: null,
  topic: null,
  status: 'clarifying',
  rating_score: 0,
  rating_breakdown: {},
  readiness_level: 'draft',
  created_at: now(),
  updated_at: now(),
  ...values,
})

const mockRequest = async (method, path, body) => {
  const parts = path.split('/').filter(Boolean)
  if (method === 'POST' && parts[0] === 'tasks') {
    const task = emptyTask(mockTaskId++, { draft_text: body.draft_text, topic: body.topic || null })
    mockTasks.push(task)
    const questions = [
      'What context should someone understand before starting this task?',
      'Who are the intended users or beneficiaries?',
      'What result would make this task successful?',
    ].map((question_text, index) => ({ id: index + 1, task_id: task.id, question_text, answer_text: null, order: index + 1 }))
    mockQuestions.set(task.id, questions)
    return { task, questions }
  }
  if (method === 'GET' && parts[0] === 'tasks' && parts.length === 1) {
    const query = new URLSearchParams(path.split('?')[1] || '')
    let result = mockTasks.filter((task) => task.status === 'confirmed')
    if (query.get('topic')) result = result.filter((task) => task.topic === query.get('topic'))
    if (query.get('readiness_level')) result = result.filter((task) => task.readiness_level === query.get('readiness_level'))
    if (query.get('sort') === 'rating') result.sort((a, b) => b.rating_score - a.rating_score)
    return result
  }
  const id = Number(parts[1])
  const task = mockTasks.find((item) => item.id === id)
  if (!task) throw new Error('Task not found')
  if (method === 'PATCH' && parts[2] === 'answers') {
    const answers = Array.isArray(body.answers) ? body.answers : Object.values(body.answers || {})
    task.context = answers[0] || task.context
    task.users = answers[1] || task.users
    task.success_criteria = answers[2] || task.success_criteria
    task.status = 'card_ready'
    task.updated_at = now()
    return task
  }
  if (method === 'PATCH' && parts.length === 2) {
    Object.assign(task, body, { updated_at: now() })
    return task
  }
  if (method === 'POST' && parts[2] === 'confirm') {
    task.status = 'confirmed'
    task.rating_score = ['context', 'need', 'data_materials', 'expected_result', 'success_criteria', 'constraints', 'users', 'contact', 'interaction_format'].filter((key) => task[key]).length
    task.readiness_level = task.rating_score >= 7 ? 'ready' : task.rating_score >= 4 ? 'partial' : 'draft'
    task.rating_breakdown = { 'context+need': task.context && task.need ? 1 : 0, data_materials: task.data_materials ? 1 : 0, expected_result: task.expected_result ? 1 : 0, success_criteria: task.success_criteria ? 1 : 0, constraints: task.constraints ? 1 : 0, users: task.users ? 1 : 0, 'contact+interaction_format': task.contact && task.interaction_format ? 1 : 0 }
    task.updated_at = now()
    return task
  }
  if (method === 'GET' && parts[2] === 'rating') return { score: task.rating_score, breakdown: task.rating_breakdown, missing_fields: ['context', 'need'].filter((key) => !task[key]) }
  throw new Error('Unsupported mock request')
}

async function request(method, path, body) {
  try {
    const response = await fetch(`${API_BASE}/${path.replace(/^\//, '')}`, { method, headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return response.json()
  } catch (error) {
    if (typeof window === 'undefined' || !error) throw error
    return mockRequest(method, path.replace(/^\//, ''), body)
  }
}

export const createTask = (draft_text, topic = null) => request('POST', '/tasks', { draft_text, topic })
export const answerTask = (id, answers) => request('PATCH', `/tasks/${id}/answers`, { answers })
export const updateTask = (id, fields) => request('PATCH', `/tasks/${id}`, fields)
export const confirmTask = (id) => request('POST', `/tasks/${id}/confirm`, {})
export const getTaskRating = (id) => request('GET', `/tasks/${id}/rating`)
export const listTasks = ({ topic, readiness_level, sort } = {}) => {
  const query = new URLSearchParams()
  if (topic) query.set('topic', topic)
  if (readiness_level) query.set('readiness_level', readiness_level)
  if (sort) query.set('sort', sort)
  return request('GET', `/tasks${query.toString() ? `?${query}` : ''}`)
}

export default { createTask, answerTask, updateTask, confirmTask, getTaskRating, listTasks }
