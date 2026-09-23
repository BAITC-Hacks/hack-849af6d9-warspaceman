export default function ReadinessScore({ task, rating }) {
  const score = rating?.score ?? task?.rating_score ?? 0
  const level = task?.readiness_level
  const breakdown = rating?.breakdown || task?.rating_breakdown || {}
  const missing = rating?.missing_fields || []
  return <section className="readiness-score" aria-label="Readiness score"><div><strong>Readiness: {score}</strong>{level && <span className="status-badge">{level}</span>}</div>{Object.keys(breakdown).length > 0 && <details><summary>Score breakdown</summary><ul>{Object.entries(breakdown).map(([key, value]) => <li key={key}>{key}: {value}</li>)}</ul></details>}{missing.length > 0 && <p>Missing information: {missing.join(', ')}</p>}</section>
}
