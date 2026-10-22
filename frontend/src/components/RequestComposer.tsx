import type { FormEvent } from 'react'
import Icon from './Icon'

export const examples = [
  {
    id: 'proposal',
    label: 'Business proposal',
    description: 'Appointment booking system',
    request: 'Create a project proposal for a small business launching an online appointment booking system. Include objectives, scope, features, timeline, risks, and success metrics.',
  },
  {
    id: 'recovery',
    label: 'Project recovery',
    description: 'Chatbot launch · two-week window',
    request: 'Prepare a project recovery plan for a delayed customer support chatbot launch. The original deadline is in two weeks, the budget is limited, testing is incomplete, and the team has not agreed on the launch scope. Identify missing information, state reasonable assumptions, prioritize critical tasks, propose a revised two-week schedule, and include risks, decision points, and go/no-go criteria. Do not invent actual company data.',
  },
]

interface RequestComposerProps {
  value: string
  loading: boolean
  error: string | null
  selectedExample: string | null
  onChange: (value: string) => void
  onSelectExample: (id: string, value: string) => void
  onSubmit: () => void
}

export default function RequestComposer({ value, loading, error, selectedExample, onChange, onSelectExample, onSubmit }: RequestComposerProps) {
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    onSubmit()
  }

  return (
    <section className="composer panel" aria-labelledby="request-title">
      <div className="section-eyebrow"><span className="eyebrow-dot" /> DOCUMENT BRIEF</div>
      <div className="composer-heading">
        <div>
          <h1 id="request-title">What should we create?</h1>
          <p>Describe the outcome. Your agent will plan the work and prepare a Word document.</p>
        </div>
        <span className="private-badge"><Icon name="shield" /> Private workspace</span>
      </div>

      <div className="examples-block">
        <div className="minor-label">START WITH AN EXAMPLE</div>
        <div className="example-list">
          {examples.map((example) => (
            <button
              className={`example-card ${selectedExample === example.id ? 'selected' : ''}`}
              key={example.id}
              type="button"
              aria-pressed={selectedExample === example.id}
              onClick={() => onSelectExample(example.id, example.request)}
            >
              <span className="example-icon"><Icon name={example.id === 'proposal' ? 'file' : 'layers'} /></span>
              <span className="example-copy"><strong>{example.label}</strong><small>{example.description}</small></span>
              <Icon className="example-arrow" name="arrow" />
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={submit}>
        <label className="minor-label" htmlFor="agent-request">YOUR REQUEST</label>
        <textarea
          id="agent-request"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="For example: Prepare a launch plan for… Include the key sections, constraints, and outcomes you need."
          rows={7}
          maxLength={12000}
          disabled={loading}
          aria-describedby="request-hint request-count"
        />
        <div className="textarea-footer">
          <span id="request-hint">Be specific about the audience, scope, and important constraints.</span>
          <span id="request-count">{value.length.toLocaleString()} / 12,000</span>
        </div>
        {error && <div className="inline-error" role="alert"><Icon name="alert" />{error}</div>}
        <div className="form-actions">
          <span className="workflow-note"><Icon name="clock" /> Planning and document creation may take a moment.</span>
          <button className="primary-button" type="submit" disabled={loading || !value.trim()}>
            {loading ? <><span className="spinner" /> Creating document…</> : <><Icon name="spark" /> Generate document <Icon className="button-arrow" name="arrow" /></>}
          </button>
        </div>
      </form>
    </section>
  )
}
