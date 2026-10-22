import type { ReactNode } from 'react'
import type { AgentResponse, StepResult } from '../types'
import Icon from './Icon'

function ResultValue({ value }: { value: unknown }): ReactNode {
  if (value === null || value === undefined) return <span className="muted-value">No output returned.</span>
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return <p className="result-text">{String(value)}</p>
  if (Array.isArray(value)) return <ul className="result-list">{value.map((item, index) => <li key={index}><ResultValue value={item} /></li>)}</ul>
  if (typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>)
    if (!entries.length) return <span className="muted-value">No details.</span>
    return <dl className="result-data">{entries.map(([key, item]) => <div className="result-data-row" key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd><ResultValue value={item} /></dd></div>)}</dl>
  }
  return null
}

function StepCard({ step, index }: { step: StepResult; index: number }) {
  return (
    <article className="step-card">
      <div className={`step-icon status-${step.status}`}>
        {step.status === 'succeeded' ? <Icon name="check" /> : step.status === 'failed' ? <Icon name="alert" /> : <Icon name="clock" />}
      </div>
      <div className="step-main">
        <div className="step-title-row"><h3>{step.description}</h3><span className={`status-pill status-${step.status}`}>{step.status}</span></div>
        <div className="step-meta"><span>STEP {String(index + 1).padStart(2, '0')}</span><span>{step.tool.replaceAll('_', ' ')}</span></div>
        {step.error && <p className="step-error">{step.error}</p>}
        {step.output !== null && step.output !== undefined && <details className="step-output"><summary>View execution result</summary><ResultValue value={step.output} /></details>}
      </div>
    </article>
  )
}

interface AgentResultProps {
  result: AgentResponse
  downloadError: string | null
  downloading: boolean
  onDownload: () => void
  onReset: () => void
}

export default function AgentResult({ result, downloadError, downloading, onDownload, onReset }: AgentResultProps) {
  const modeLabel = result.provider_mode === 'fallback' ? 'Fallback mode' : `${result.provider_mode.toUpperCase()} live model`
  const canDownload = Boolean(result.download_url || result.document_id)

  return (
    <section className="result-panel" aria-labelledby="result-title" aria-live="polite">
      <div className="result-topline"><div className="section-eyebrow"><span className={`eyebrow-dot ${result.status === 'succeeded' ? 'success-dot' : ''}`} /> AGENT RUN {result.status.replaceAll('_', ' ').toUpperCase()}</div><button className="text-button" onClick={onReset}><Icon name="plus" /> Start new request</button></div>
      <div className="result-heading">
        <div className="document-mark"><Icon name="file" /></div>
        <div className="result-title-copy"><div className="result-kicker">{result.plan.document_type}</div><h2 id="result-title">{result.plan.title}</h2></div>
      </div>

      <div className="summary-card"><div className="summary-icon"><Icon name="spark" /></div><div><div className="minor-label">AGENT SUMMARY</div><p>{result.summary}</p></div></div>

      <div className="run-meta"><span className={`mode-chip ${result.provider_mode === 'fallback' ? 'fallback-chip' : ''}`}><span className="mode-dot" />{modeLabel}</span><span className={`planner-status planner-${result.planner_status}`}>LLM planner {result.planner_status}</span><span className={`run-status status-${result.status}`}>Request {result.status}</span>{result.document_id && <span className="document-id">ID · {result.document_id.slice(0, 8)}</span>}</div>
      {result.fallback_reason && <div className="fallback-note"><Icon name="alert" /><span>{result.fallback_reason}</span></div>}

      <div className="result-section"><div className="result-section-heading"><div><div className="minor-label">EXECUTION PLAN</div><h3>{result.plan.tasks.length} planned steps</h3></div><span className="objective-label">OBJECTIVE</span></div><p className="objective-copy">{result.plan.objective}</p>
        <div className="plan-list">{result.plan.tasks.map((task, index) => <div className="plan-row" key={task.id}><span className="plan-index">{String(index + 1).padStart(2, '0')}</span><div><strong>{task.description}</strong><small>{task.tool.replaceAll('_', ' ')} · Expected: {task.expected_output}</small></div></div>)}</div>
      </div>

      {result.assumptions.length > 0 && <div className="result-section assumptions-section"><div className="minor-label">ASSUMPTIONS</div><ul className="assumption-list">{result.assumptions.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul></div>}

      <div className="result-section"><div className="result-section-heading"><div><div className="minor-label">EXECUTION DETAILS</div><h3>Task results</h3></div><span className="completed-count">{result.steps.filter((step) => step.status === 'succeeded').length} / {result.steps.length} successful</span></div>
        <div className="steps-list">{result.steps.map((step, index) => <StepCard key={step.step_id} step={step} index={index} />)}</div>
      </div>

      {canDownload ? <div className="download-card"><div className="download-file"><span className="word-icon">W</span><span><strong>{result.plan.title}.docx</strong><small>Microsoft Word document</small></span></div><button className="download-button" onClick={onDownload} disabled={downloading}><Icon name="download" />{downloading ? 'Preparing…' : 'Download Word document'}</button></div> : <div className="fallback-note"><Icon name="alert" /><span>No document link was returned. Review the execution results above.</span></div>}
      {downloadError && <div className="inline-error download-error" role="alert"><Icon name="alert" />{downloadError}</div>}
      <div className="result-footer"><span>Generated by Autonomous AI Document Agent</span><button className="text-button" onClick={onReset}>Create another <Icon name="arrow" /></button></div>
    </section>
  )
}
