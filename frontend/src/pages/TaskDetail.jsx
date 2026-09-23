import { useEffect, useState } from 'react'
import { createProposal, listProposals, updateProposal } from '../api/proposals'

export default function TaskDetail({ task, taskId }) {
  const id = taskId || task?.id; const [proposals, setProposals] = useState([]); const [form, setForm] = useState({ team_id: '', idea: '', plan: '', deadline: '', link: '' }); const [error, setError] = useState('')
  useEffect(() => { if (id) listProposals(id).then(setProposals).catch((reason) => setError(reason.message)) }, [id])
  if (!id) return <p>Provide a task id.</p>
  async function submit(event) { event.preventDefault(); const value = await createProposal(id, { ...form, team_id: Number(form.team_id) }); setProposals((current) => [...current, value]); setForm({ team_id: '', idea: '', plan: '', deadline: '', link: '' }) }
  async function setStatus(proposal, status) { const value = await updateProposal(proposal.id, status); setProposals((current) => current.map((item) => item.id === value.id ? value : item)) }
  return <section><h1>{task?.title || `Task #${id}`}</h1><pre>{JSON.stringify(task, null, 2)}</pre><h2>Submit proposal</h2><form onSubmit={submit}>{Object.keys(form).map((field) => <label key={field}>{field}<input required={field === 'team_id' || field === 'idea'} value={form[field]} onChange={(event) => setForm({ ...form, [field]: event.target.value })} /></label>)}<button>Submit proposal</button></form>{error && <p role="alert">{error}</p>}<h2>Proposals</h2><ul>{proposals.map((proposal) => <li key={proposal.id}><strong>{proposal.idea}</strong> ({proposal.status})<p>{proposal.plan}</p>{proposal.status === 'pending' && <><button onClick={() => setStatus(proposal, 'accepted')}>Accept</button><button onClick={() => setStatus(proposal, 'rejected')}>Reject</button></>}</li>)}</ul></section>
}
