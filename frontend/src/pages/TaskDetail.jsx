import { useEffect, useState } from 'react'
import { createProposal, listProposals, updateProposal } from '../api/proposals'
import { getTaskRating } from '../api/tasks'
import { createTeam, listTeams } from '../api/teams'
import ReadinessScore from '../components/ReadinessScore'

const detailFields = ['title', 'context', 'need', 'users', 'data_materials', 'constraints', 'expected_result', 'success_criteria', 'contact', 'interaction_format', 'topic']
const fieldLabels = { title: 'Title', context: 'Context', need: 'Business need', users: 'Users', data_materials: 'Data and materials', constraints: 'Constraints', expected_result: 'Expected result', success_criteria: 'Success criteria', contact: 'Contact', interaction_format: 'Interaction format', topic: 'Topic' }
const emptyProposal = { team_id: '', idea: '', plan: '', deadline: '', link: '' }
const emptyTeam = { name: '', interests: '', skills: '', technologies: '' }

export default function TaskDetail({ task, taskId, role = 'business' }) {
  const id = taskId || task?.id
  const [proposals, setProposals] = useState([])
  const [teams, setTeams] = useState([])
  const [rating, setRating] = useState(null)
  const [form, setForm] = useState(emptyProposal)
  const [teamForm, setTeamForm] = useState(emptyTeam)
  const [loading, setLoading] = useState(false)
  const [ratingLoading, setRatingLoading] = useState(true)
  const [teamsLoading, setTeamsLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [teamCreating, setTeamCreating] = useState(false)
  const [pendingAction, setPendingAction] = useState(null)
  const [success, setSuccess] = useState('')
  const [teamSuccess, setTeamSuccess] = useState('')
  const [error, setError] = useState('')
  const [proposalError, setProposalError] = useState('')
  const [teamsError, setTeamsError] = useState('')
  const [teamCreateError, setTeamCreateError] = useState('')

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
    setLoading(true); setProposalError('')
    listProposals(id).then((items) => { if (active) setProposals(items) }).catch((reason) => { if (active) setProposalError(reason.message) }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [id, role])

  useEffect(() => {
    if (!id) return
    let active = true
    setTeamsLoading(true); setTeamsError('')
    listTeams().then((items) => { if (active) setTeams((current) => { const merged = new Map(items.map((team) => [team.id, team])); current.forEach((team) => merged.set(team.id, team)); return [...merged.values()] }) }).catch((reason) => { if (active) setTeamsError(reason.message) }).finally(() => { if (active) setTeamsLoading(false) })
    return () => { active = false }
  }, [id])

  if (!id) return <p>Provide a task id.</p>

  const teamNames = new Map(teams.map((team) => [team.id, team.name]))

  async function submitProposal(event) {
    event.preventDefault(); setSubmitting(true); setError(''); setSuccess('')
    try {
      const value = await createProposal(id, { ...form, team_id: Number(form.team_id), plan: form.plan || null, deadline: form.deadline || null, link: form.link || null })
      setProposals((current) => [...current, value]); setForm(emptyProposal); setSuccess('Proposal submitted.')
    } catch (reason) { setError(reason.message) } finally { setSubmitting(false) }
  }

  async function submitTeam(event) {
    event.preventDefault(); setTeamCreating(true); setTeamCreateError(''); setTeamSuccess('')
    try {
      const created = await createTeam({ name: teamForm.name, interests: teamForm.interests || null, skills: teamForm.skills || null, technologies: teamForm.technologies || null })
      setTeams((current) => [...current.filter((team) => team.id !== created.id), created])
      setForm((current) => ({ ...current, team_id: String(created.id) }))
      setTeamForm(emptyTeam); setTeamsError(''); setTeamSuccess(`Team “${created.name}” created and selected.`)
    } catch (reason) { setTeamCreateError(reason.message) } finally { setTeamCreating(false) }
  }

  async function setStatus(proposal, status) {
    setPendingAction(proposal.id); setError('')
    try {
      const value = await updateProposal(proposal.id, status)
      setProposals((current) => current.map((item) => item.id === value.id ? value : item)); setSuccess(`Proposal ${status}.`)
    } catch (reason) { setError(reason.message) } finally { setPendingAction(null) }
  }

  return <section><h1>{task?.title || `Task #${id}`}</h1>{error && <p role="alert">{error}</p>}{success && <p role="status">{success}</p>}{ratingLoading ? <p>Loading readiness…</p> : <ReadinessScore task={task} rating={rating} />}<h2>Task information</h2><div className="detail-grid">{detailFields.map((field) => task?.[field] ? <article key={field}><h3>{fieldLabels[field]}</h3><p>{task[field]}</p></article> : <article key={field}><h3>{fieldLabels[field]}</h3><p className="muted">Not provided.</p></article>)}</div>{role === 'student' && <><h2>Submit proposal</h2>{teamsLoading && <p>Loading teams…</p>}{teamsError && <p role="alert">Teams could not be loaded: {teamsError}</p>}{!teamsLoading && !teamsError && teams.length === 0 && <p>No teams are available.</p>}<form onSubmit={submitProposal}><label>Team<select required disabled={teamsLoading || teams.length === 0} value={form.team_id} onChange={(event) => setForm({ ...form, team_id: event.target.value })}><option value="">Select a team</option>{teams.map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}</select></label><label>Idea<textarea required value={form.idea} onChange={(event) => setForm({ ...form, idea: event.target.value })} /></label><label>Plan<textarea value={form.plan} onChange={(event) => setForm({ ...form, plan: event.target.value })} /></label><label>Deadline<input value={form.deadline} onChange={(event) => setForm({ ...form, deadline: event.target.value })} /></label><label>Prototype link<input type="url" value={form.link} onChange={(event) => setForm({ ...form, link: event.target.value })} /></label><button disabled={submitting || teamsLoading || teams.length === 0 || !form.team_id}>{submitting ? 'Submitting…' : 'Submit proposal'}</button></form><section className="team-creation"><h3>Create team</h3><p className="muted">Create a team if yours is not listed above.</p>{teamCreateError && <p role="alert">{teamCreateError}</p>}{teamSuccess && <p role="status">{teamSuccess}</p>}<form onSubmit={submitTeam}><label>Name<input required value={teamForm.name} onChange={(event) => setTeamForm({ ...teamForm, name: event.target.value })} /></label><label>Interests<input value={teamForm.interests} onChange={(event) => setTeamForm({ ...teamForm, interests: event.target.value })} /></label><label>Skills<input value={teamForm.skills} onChange={(event) => setTeamForm({ ...teamForm, skills: event.target.value })} /></label><label>Technologies<input value={teamForm.technologies} onChange={(event) => setTeamForm({ ...teamForm, technologies: event.target.value })} /></label><button disabled={teamCreating}>{teamCreating ? 'Creating…' : 'Create team'}</button></form></section></>}{role === 'business' && <><h2>Proposals</h2>{teamsLoading && <p className="muted">Loading team names…</p>}{teamsError && <p className="muted">Team names are unavailable; proposal IDs are shown instead.</p>}{proposalError && <p role="alert">{proposalError}</p>}{loading && <p>Loading proposals…</p>}{!loading && !proposalError && proposals.length === 0 && <p>No proposals yet.</p>}<ul className="card-list">{proposals.map((proposal) => <li key={proposal.id}><div className="card-heading"><strong>{proposal.idea}</strong><span className={`status-badge status-${proposal.status}`}>{proposal.status}</span></div><p className="proposal-team">{teamNames.get(proposal.team_id) || `Team #${proposal.team_id}`}</p><p>{proposal.plan || 'No plan provided.'}</p>{proposal.deadline && <p>Deadline: {proposal.deadline}</p>}{proposal.link && <p><a href={proposal.link} target="_blank" rel="noreferrer">Prototype link</a></p>}{proposal.status === 'pending' && <div className="button-row"><button disabled={pendingAction === proposal.id} onClick={() => setStatus(proposal, 'accepted')}>{pendingAction === proposal.id ? 'Updating…' : 'Accept'}</button><button className="secondary" disabled={pendingAction === proposal.id} onClick={() => setStatus(proposal, 'rejected')}>Reject</button></div>}</li>)}</ul></>}</section>
}
