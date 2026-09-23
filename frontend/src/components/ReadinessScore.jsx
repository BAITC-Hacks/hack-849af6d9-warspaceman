export default function ReadinessScore({ task, rating }) {
  const score = rating?.score ?? task?.rating_score ?? 0
  const level = rating?.readiness_level ?? task?.readiness_level
  const breakdown = rating?.breakdown || task?.rating_breakdown || {}
  const missing = rating?.missing_fields || []
  const suggestions = rating?.suggestions || []
  return <section className="readiness-score" aria-label="Readiness score"><div><strong>Readiness: {score}</strong>{level && <span className={`status-badge readiness-${level}`}>{level}</span>}</div>{Object.keys(breakdown).length > 0 && <details><summary>Score breakdown</summary><ul>{Object.entries(breakdown).map(([key, value]) => <li key={key}>{key}: {value}</li>)}</ul></details>}{missing.length > 0 && <p>Missing information: {missing.join(', ')}</p>}{suggestions.length > 0 && <div className="suggestions"><h3>How to improve</h3><ul>{suggestions.map((suggestion, index) => <li key={`${index}-${suggestion}`}>{suggestion}</li>)}</ul></div>}</section>
}
