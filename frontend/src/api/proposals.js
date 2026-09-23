const API_BASE = (import.meta?.env?.VITE_API_BASE_URL || '').replace(/\/$/, '')
const mockProposals = []
let mockProposalId = 1

async function request(method, path, body) {
  try {
    const response = await fetch(`${API_BASE}/${path.replace(/^\//, '')}`, { method, headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return response.json()
  } catch (error) {
    if (typeof window === 'undefined' || !error) throw error
    const parts = path.split('/').filter(Boolean)
    if (method === 'POST' && parts[0] === 'tasks') {
      const proposal = { id: mockProposalId++, task_id: Number(parts[1]), ...body, status: 'pending', created_at: new Date().toISOString() }
      mockProposals.push(proposal)
      return proposal
    }
    if (method === 'GET') return mockProposals.filter((proposal) => proposal.task_id === Number(parts[1]))
    const proposal = mockProposals.find((item) => item.id === Number(parts[1]))
    if (!proposal) throw new Error('Proposal not found')
    proposal.status = body.status
    return proposal
  }
}

export const createProposal = (taskId, proposal) => request('POST', `/tasks/${taskId}/proposals`, proposal)
export const listProposals = (taskId) => request('GET', `/tasks/${taskId}/proposals`)
export const updateProposal = (id, status) => request('PATCH', `/proposals/${id}`, { status })
export default { createProposal, listProposals, updateProposal }
