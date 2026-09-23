import { useEffect, useState } from 'react'
import { createProposal, listProposals, updateProposal } from '../api/proposals'
import { getTaskRating } from '../api/tasks'
import ReadinessScore from '../components/ReadinessScore'

const detailFields = ['title', 'context', 'need', 'users', 'data_materials', 'constraints', 'expected_result', 'success_criteria', 'contact', 'interaction_format', 'topic']
export default function TaskDetail({ task, taskId, role = 'business' }) {
  const id = taskId || task?.id; const [proposals, setProposals] = useState([]); const [rating, setRating] = useState(null); const [form, setForm] = useState({ team_id: '', idea: '', plan: '', deadline: '', link: '' }); const [loading, setLoading] = useState(false); const [ratingLoading, setRatingLoading] = useState(true); const [submitting, setSubmitting] = useState(false); const [pendingAction, setPendingAction] = useState(null); const [success, setSuccess] = useState(''); const [error, setError] = useState(''); const [proposalError, setProposalError] = useState('')
  useEffect(() => {
    if (!id) return
    let active = true
    setRatingLoading(true)
    getTaskRating(id).then((score) => { if (active) setRating(score) }).catch((reason) => { if (active) setError(reason.message) }).finally(() => { if (active) setRatingLoading(false) })
    return () => { active = false }
  }, [id])
  useEffect(() => {
    if (!id || role !== 'business') { setLoading(false); return }
    let active = true
    setLoading(true)
    setProposalError('')
    listProposals(id).then((items) => { if (active) setProposals(items) }).catch((reason) => { if (active) setProposalError(reason.message) }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [id, role])
  if (!id) return <p>Provide a task id.</p>
  async function submit(event) { event.preventDefault(); setSubmitting(true); setError(''); setSuccess(''); try { const value = await createProposal(id, { ...form, team_id: Number(form.team_id), plan: form.plan || null, deadline: form.deadline || null, link: form.link || null }); setProposals((current) => [...current, value]); setForm({ team_id: '', idea: '', plan: '', deadline: '', link: '' }); setSuccess('Proposal submitted.') } catch (reason) { setError(reason.message) } finally { setSubmitting(false) } }
  async function setStatus(proposal, status) { setPendingAction(proposal.id); setError(''); try { const value = await updateProposal(proposal.id, status); setProposals((current) => current.map((item) => item.id === value.id ? value : item)); setSuccess(`Proposal ${status}.`) } catch (reason) { setError(reason.message) } finally { setPendingAction(null) } }
  return <section><h1>{task?.title || `Task #${id}`}</h1>{error && <p role="alert">{error}</p>}{success && <p role="status">{success}</p>}{ratingLoading ? <p>Loading readiness…</p> : <ReadinessScore task={task} rating={rating} />}<h2>Task information</h2><div className="detail-grid">{detailFields.map((field) => task?.[field] ? <article key={field}><h3>{field}</h3><p>{task[field]}</p></article> : <article key={field}><h3>{field}</h3><p className="muted">Not provided.</p></article>)}</div>{role === 'student' && <><h2>Submit proposal</h2><form onSubmit={submit}><label>Team ID<input type="number" min="1" required value={form.team_id} onChange={(event) => setForm({ ...form, team_id: event.target.value })} /></label><label>Idea<textarea required value={form.idea} onChange={(event) => setForm({ ...form, idea: event.target.value })} /></label><label>Plan<textarea value={form.plan} onChange={(event) => setForm({ ...form, plan: event.target.value })} /></label><label>Deadline<input value={form.deadline} onChange={(event) => setForm({ ...form, deadline: event.target.value })} /></label><label>Prototype link<input type="url" value={form.link} onChange={(event) => setForm({ ...form, link: event.target.value })} /></label><button disabled={submitting}>{submitting ? 'Submitting…' : 'Submit proposal'}</button></form></>}{role === 'business' && <><h2>Proposals</h2>{proposalError && <p role="alert">{proposalError}</p>}{loading && <p>Loading proposals…</p>}{!loading && !proposalError && proposals.length === 0 && <p>No proposals yet.</p>}<ul className="card-list">{proposals.map((proposal) => <li key={proposal.id}><div className="card-heading"><strong>{proposal.idea}</strong><span className={`status-badge status-${proposal.status}`}>{proposal.status}</span></div><p>Team {proposal.team_id}</p><p>{proposal.plan || 'No plan provided.'}</p>{proposal.deadline && <p>Deadline: {proposal.deadline}</p>}{proposal.link && <p><a href={proposal.link} target="_blank" rel="noreferrer">Prototype link</a></p>}{proposal.status === 'pending' && <div className="button-row"><button disabled={pendingAction === proposal.id} onClick={() => setStatus(proposal, 'accepted')}>{pendingAction === proposal.id ? 'Updating…' : 'Accept'}</button><button className="secondary" disabled={pendingAction === proposal.id} onClick={() => setStatus(proposal, 'rejected')}>Reject</button></div>}</li>)}</ul></>}</section>
}
