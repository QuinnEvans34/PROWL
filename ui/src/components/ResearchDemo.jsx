import ResearchEvidencePanel from './ResearchEvidencePanel.jsx'
import ResearchWorkflowPanel from './ResearchWorkflowPanel.jsx'
import LiteratureSearchPanel from './LiteratureSearchPanel.jsx'

export default function ResearchDemo() {
  return <main style={{ maxWidth: 1000, margin: '0 auto', padding: '32px 24px' }}>
    <a href="/">Back to PROWL</a>
    <h1>PROWL research evidence</h1>
    <p>Explore pancreatic research and inspect the original source passages. Research use only.</p>
    <LiteratureSearchPanel />
    <h2>Earlier guided demos</h2>
    <p>These separate prototypes use the original two-review collection and fixed questions.</p>
    <ResearchWorkflowPanel />
    <ResearchEvidencePanel answers />
    <ResearchEvidencePanel />
  </main>
}
