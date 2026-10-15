import ResearchEvidencePanel from './ResearchEvidencePanel.jsx'

export default function ResearchDemo() {
  return <main style={{ maxWidth: 1000, margin: '0 auto', padding: '32px 24px' }}>
    <a href="/">Back to PROWL</a>
    <h1>PROWL research evidence</h1>
    <p>Explore two research reviews with three guided questions. Search source passages or ask the
      local model to select cited quotations. No scan or patient information is used.</p>
    <p>Research use only. These excerpts do not establish medical accuracy, completeness, or a diagnosis.</p>
    <ResearchEvidencePanel answers />
    <ResearchEvidencePanel />
  </main>
}
