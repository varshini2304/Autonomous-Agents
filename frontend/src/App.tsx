import { useState } from 'react'
import RequestComposer from './components/RequestComposer'
import AgentResult from './components/AgentResult'
import Icon from './components/Icon'
import { createDocument, downloadDocument } from './services/agentApi'
import type { AgentResponse } from './types'

export default function App() {
  const [request, setRequest] = useState('')
  const [selectedExample, setSelectedExample] = useState<string | null>(null)
  const [result, setResult] = useState<AgentResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [downloading, setDownloading] = useState(false)
  const [downloadError, setDownloadError] = useState<string | null>(null)

  const submit = async () => {
    if (!request.trim()) {
      setError('Add a request before generating a document.')
      return
    }
    if (request.length > 12000) {
      setError('Keep your request under 12,000 characters.')
      return
    }
    setError(null)
    setResult(null)
    setDownloadError(null)
    setLoading(true)
    try {
      const response = await createDocument({ request: request.trim() })
      setResult(response)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'The document could not be generated. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setRequest('')
    setSelectedExample(null)
    setResult(null)
    setError(null)
    setDownloadError(null)
    setDownloading(false)
  }

  const download = async () => {
    if (!result) return
    setDownloadError(null)
    setDownloading(true)
    try {
      await downloadDocument(result)
    } catch (caught) {
      setDownloadError(caught instanceof Error ? caught.message : 'The document download failed. Please try again.')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="Document Agent Workspace home"><span className="brand-mark"><Icon name="spark" /></span><span>Northstar <b>Agent Workspace</b></span></a>
        <div className="topbar-right"><span className="connection-indicator"><i /> Agent ready</span><span className="topbar-divider" /><span className="workspace-label">DOCUMENT STUDIO</span></div>
      </header>

      <main id="top" className={`workspace ${result ? 'has-result' : ''}`}>
        {!result && <div className="welcome-block"><div className="welcome-mark"><Icon name="spark" /></div><p className="welcome-overline">AUTONOMOUS DOCUMENT AGENT</p><h2>From a clear brief<br />to a <em>ready-to-use</em> document.</h2><p className="welcome-description">Give your agent the context. It will build a plan, work through each step, and create a polished Word document.</p><div className="capability-row"><span><Icon name="layers" /> Structured planning</span><span><Icon name="file" /> Word output</span><span><Icon name="shield" /> Safe execution</span></div></div>}
        <div className="workspace-grid">
          <RequestComposer value={request} loading={loading} error={error} selectedExample={selectedExample} onChange={(value) => { setRequest(value); if (error) setError(null); setSelectedExample(null) }} onSelectExample={(id, value) => { setSelectedExample(id); setRequest(value); setError(null) }} onSubmit={submit} />
          {result ? <AgentResult result={result} downloadError={downloadError} downloading={downloading} onDownload={download} onReset={reset} /> : <aside className="side-panel"><div className="side-panel-top"><span className="minor-label">YOUR WORKFLOW</span><span className="workflow-count">01 — 04</span></div><div className="workflow-list"><div className="workflow-item active"><span className="workflow-step"><Icon name="file" /></span><div><strong>Describe</strong><small>Share your brief and goals</small></div></div><div className="workflow-connector" /><div className="workflow-item"><span className="workflow-step"><Icon name="layers" /></span><div><strong>Plan</strong><small>Review the agent’s approach</small></div></div><div className="workflow-connector" /><div className="workflow-item"><span className="workflow-step"><Icon name="spark" /></span><div><strong>Execute</strong><small>Tasks run through permitted tools</small></div></div><div className="workflow-connector" /><div className="workflow-item"><span className="workflow-step"><Icon name="download" /></span><div><strong>Download</strong><small>Get the finished Word document</small></div></div></div><div className="side-note"><div className="side-note-icon"><Icon name="shield" /></div><div><strong>Built for careful output</strong><p>Your request is checked and the generated document is verified before it’s shared.</p></div></div></aside>}
        </div>
        {loading && <div className="loading-banner" role="status"><span className="spinner dark-spinner" /> The agent is working through your request. Results will appear when the run completes.</div>}
      </main>
      <footer className="site-footer"><span>Autonomous AI Document Agent</span><span>Plan · Execute · Generate</span></footer>
    </div>
  )
}
