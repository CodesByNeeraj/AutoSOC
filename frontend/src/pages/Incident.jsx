import { useEffect, useState } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { getIncident, getReport, getFindings } from '../services/api'

const priorityColor = {
  p0: 'badge--p0',
  p1: 'badge--p1',
  p2: 'badge--p2',
  p3: 'badge--p3',
  p4: 'badge--p4',
}

export default function Incident() {
  const { id } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const [data, setData] = useState(location.state || null)
  const [incident, setIncident] = useState(null)
  const [activeTab, setActiveTab] = useState('triage')
  const [loading, setLoading] = useState(!location.state)

useEffect(() => {
  if (!location.state) {
    async function load() {
      try {
        const [inc, findings, rep] = await Promise.all([
          getIncident(id),
          getFindings(id),
          getReport(id)
        ])
        setIncident(inc)

        const triageFinding = findings.find(f => f.agent === 'triage')
        const investigationFinding = findings.find(f => f.agent === 'investigation')
        const responseFinding = findings.find(f => f.agent === 'response')

        setData({
          incident_id: id,
          triage: triageFinding ? JSON.parse(triageFinding.content) : null,
          investigation: investigationFinding ? JSON.parse(investigationFinding.content) : null,
          response: responseFinding ? JSON.parse(responseFinding.content) : null,
          report: rep ? JSON.parse(rep.content) : null
        })

      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }
}, [id])

  const tabs = ['triage', 'investigation', 'response', 'report']

  if (loading) {
    return (
      <div className="page-body">
        <div className="loading-bar">
          <div className="loading-bar-fill" />
        </div>
      </div>
    )
  }

  const triage = data?.triage
  const investigation = data?.investigation
  const response = data?.response
  const report = data?.report

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">
            {triage?.title ?? incident?.title ?? 'incident detail'}
          </div>
          <div className="page-subtitle mono">
            id: {id}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {triage?.priority && (
            <span className={`badge ${priorityColor[triage.priority.toLowerCase()] ?? 'badge--p4'}`}>
              {triage.priority.toLowerCase()}
            </span>
          )}
          <button
            className="btn btn--ghost"
            onClick={() => navigate('/incidents')}
          >
            ← back
          </button>
        </div>
      </div>

      <div className="page-body">
        {/*tabs*/}
        <div style={{ display: 'flex', gap: '2px', borderBottom: '1px solid var(--border)', marginBottom: '-8px' }}>
          {tabs.map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '10px 20px',
                background: 'none',
                border: 'none',
                borderBottom: activeTab === tab ? '2px solid var(--accent-blue)' : '2px solid transparent',
                color: activeTab === tab ? 'var(--text-primary)' : 'var(--text-secondary)',
                cursor: 'pointer',
                fontSize: '13px',
                fontFamily: 'DM Sans, sans-serif',
                fontWeight: activeTab === tab ? '500' : '400',
                transition: 'all 0.15s',
                marginBottom: '-1px'
              }}
            >
              {tab}
            </button>
          ))}
        </div>

        {/*triage tab*/}
        {activeTab === 'triage' && triage && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="card">
              <div className="card-header">
                <span className="card-title">triage summary</span>
                <span className={`badge ${priorityColor[triage.priority?.toLowerCase()] ?? 'badge--p4'}`}>
                  {triage.priority?.toLowerCase()}
                </span>
              </div>
              <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div className="detail-grid">
                  <div className="detail-item">
                    <span className="detail-label">category</span>
                    <span className="detail-value">{triage.category}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">confidence</span>
                    <span className="detail-value">{triage.confidence}%</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">needs investigation</span>
                    <span className="detail-value">{triage.needs_investigation ? 'yes' : 'no'}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">human review</span>
                    <span className="detail-value" style={{ color: triage.human_review ? 'var(--amber)' : 'var(--green)' }}>
                      {triage.human_review ? 'required' : 'not required'}
                    </span>
                  </div>
                </div>
                <div>
                  <div className="detail-label" style={{ marginBottom: '8px' }}>summary</div>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                    {triage.summary}
                  </p>
                </div>
                <div>
                  <div className="detail-label" style={{ marginBottom: '8px' }}>justification</div>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                    {triage.justification}
                  </p>
                </div>
                <div>
                  <div className="detail-label" style={{ marginBottom: '8px' }}>indicators</div>
                  <div className="tag-list">
                    {triage.indicators?.map((ind, i) => (
                      <span key={i} className="tag">{ind}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/*investigation tab*/}
        {activeTab === 'investigation' && investigation && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="card">
              <div className="card-header">
                <span className="card-title">investigation findings</span>
                <span style={{
                  fontSize: '12px',
                  color: investigation.escalate ? 'var(--red)' : 'var(--green)',
                  fontFamily: 'JetBrains Mono, monospace'
                }}>
                  {investigation.escalate ? '⚠ escalate' : '✓ contained'}
                </span>
              </div>
              <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div className="detail-grid">
                  <div className="detail-item">
                    <span className="detail-label">attack pattern</span>
                    <span className="detail-value">{investigation.attack_pattern}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">blast radius</span>
                    <span className="detail-value" style={{
                      color: investigation.blast_radius === 'critical' ? 'var(--red)'
                        : investigation.blast_radius === 'spreading' ? 'var(--amber)'
                        : 'var(--green)'
                    }}>
                      {investigation.blast_radius}
                    </span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">confidence</span>
                    <span className="detail-value">{investigation.confidence}%</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">root cause</span>
                    <span className="detail-value">{investigation.root_cause}</span>
                  </div>
                </div>

                <div>
                  <div className="detail-label" style={{ marginBottom: '8px' }}>mitre att&ck tactics</div>
                  <div className="tag-list">
                    {investigation.mitre_tactics?.map((t, i) => (
                      <span key={i} className="tag" style={{ color: 'var(--purple)', borderColor: 'var(--purple)' }}>{t}</span>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="detail-label" style={{ marginBottom: '8px' }}>affected assets</div>
                  <div className="tag-list">
                    {investigation.affected_assets?.map((a, i) => (
                      <span key={i} className="tag">{a}</span>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="detail-label" style={{ marginBottom: '8px' }}>timeline</div>
                  <div className="timeline">
                    {investigation.timeline?.map((t, i) => (
                      <div key={i} className="timeline-item">
                        <div style={{ position: 'relative' }}>
                          <div className="timeline-dot" />
                          {i < investigation.timeline.length - 1 && (
                            <div className="timeline-line" />
                          )}
                        </div>
                        <span className="timeline-text">{t}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="detail-label" style={{ marginBottom: '8px' }}>evidence gaps</div>
                  <div className="action-list">
                    {investigation.evidence_gaps?.map((g, i) => (
                      <div key={i} className="action-item" style={{ color: 'var(--amber)' }}>
                        {g}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/*response tab*/}
        {activeTab === 'response' && response && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="card">
              <div className="card-header">
                <span className="card-title">response actions</span>
                <span style={{
                  fontSize: '12px',
                  color: response.escalate_to_human ? 'var(--red)' : 'var(--green)',
                  fontFamily: 'JetBrains Mono, monospace'
                }}>
                  {response.escalate_to_human ? '⚠ human escalation required' : '✓ autonomous response'}
                </span>
              </div>
              <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div className="detail-grid">
                  <div className="detail-item">
                    <span className="detail-label">estimated resolution</span>
                    <span className="detail-value">{response.estimated_resolution_time}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">confidence</span>
                    <span className="detail-value">{response.confidence}%</span>
                  </div>
                </div>

                <div>
                  <div className="detail-label" style={{ marginBottom: '8px', color: 'var(--red)' }}>
                    immediate — within 15 minutes
                  </div>
                  <div className="action-list">
                    {response.immediate_actions?.map((a, i) => (
                      <div key={i} className="action-item">{a}</div>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="detail-label" style={{ marginBottom: '8px', color: 'var(--amber)' }}>
                    short term — within 2 hours
                  </div>
                  <div className="action-list">
                    {response.short_term_actions?.map((a, i) => (
                      <div key={i} className="action-item">{a}</div>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="detail-label" style={{ marginBottom: '8px', color: 'var(--accent-blue)' }}>
                    long term — within 24 to 72 hours
                  </div>
                  <div className="action-list">
                    {response.long_term_actions?.map((a, i) => (
                      <div key={i} className="action-item">{a}</div>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="detail-label" style={{ marginBottom: '8px' }}>containment strategy</div>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                    {response.containment_strategy}
                  </p>
                </div>

                <div>
                  <div className="detail-label" style={{ marginBottom: '8px' }}>notify teams</div>
                  <div className="tag-list">
                    {response.notify_teams?.map((t, i) => (
                      <span key={i} className="tag">{t}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/*report tab*/}
        {activeTab === 'report' && report && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="card">
              <div className="card-header">
                <span className="card-title">incident report</span>
                <span className="mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  confidence: {report.report_confidence}%
                </span>
              </div>
              <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div>
                  <div className="detail-label" style={{ marginBottom: '8px' }}>executive summary</div>
                  <p style={{
                    fontSize: '14px',
                    color: 'var(--text-primary)',
                    lineHeight: '1.7',
                    padding: '14px',
                    background: 'var(--bg-elevated)',
                    borderRadius: '4px',
                    border: '1px solid var(--border)'
                  }}>
                    {report.executive_summary}
                  </p>
                </div>

                <div>
                  <div className="detail-label" style={{ marginBottom: '8px' }}>technical summary</div>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.7' }}>
                    {report.technical_summary}
                  </p>
                </div>

                <div>
                  <div className="detail-label" style={{ marginBottom: '8px' }}>attack narrative</div>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.7' }}>
                    {report.attack_narrative}
                  </p>
                </div>

                <div>
                  <div className="detail-label" style={{ marginBottom: '8px' }}>lessons learned</div>
                  <div className="action-list">
                    {report.lessons_learned?.map((l, i) => (
                      <div key={i} className="action-item">{l}</div>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="detail-label" style={{ marginBottom: '8px' }}>recommendations</div>
                  <div className="action-list">
                    {report.recommendations?.map((r, i) => (
                      <div key={i} className="action-item">{r}</div>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="detail-label" style={{ marginBottom: '8px', color: 'var(--amber)' }}>open items</div>
                  <div className="action-list">
                    {report.open_items?.map((o, i) => (
                      <div key={i} className="action-item" style={{ color: 'var(--amber)' }}>{o}</div>
                    ))}
                  </div>
                </div>

                <div style={{
                  paddingTop: '16px',
                  borderTop: '1px solid var(--border)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '11px',
                  color: 'var(--text-muted)',
                  fontFamily: 'JetBrains Mono, monospace'
                }}>
                  <span>authored by: {report.authored_by}</span>
                  <span>severity: {report.severity_justification?.slice(0, 60)}...</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/*no data fallback*/}
        {!data && !loading && (
          <div className="empty-state">
            no analysis data found for this incident
          </div>
        )}
      </div>
    </>
  )
}