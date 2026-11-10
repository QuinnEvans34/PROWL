import React, { useState } from 'react'
import { createRoot } from 'react-dom/client'
import LiteratureSearchPanel from '../../src/components/LiteratureSearchPanel.jsx'
import ReviewWorkspace from '../../src/components/ReviewWorkspace.jsx'
import '../../src/styles/tokens.css'
import '../../src/index.css'
import '../../src/styles/shell.css'
import '../../src/styles/workbench.css'
import '../../src/styles/assistant.css'
import '../../src/styles/pages.css'
import '../../src/styles/toolbench.css'
import GuidedEvidencePanel from '../../src/components/GuidedEvidencePanel.jsx'
import { workspaceProps } from './workspace.js'

function Fixture() {
  const [caseId, setCaseId] = useState('SYNTHETIC_A')
  const summaryVariant = new URLSearchParams(location.search).get('summary')
  if (summaryVariant === 'page') return <main><p>Synthetic summary fixture — no model or patient data</p><LiteratureSearchPanel variant="page" /></main>
  return <>
    <header>SYNTHETIC UI BASELINE — viewer stub, no patient data
      <button onClick={() => setCaseId(caseId === 'SYNTHETIC_A' ? 'SYNTHETIC_B' : 'SYNTHETIC_A')}>Switch synthetic case</button>
    </header>
    <div style={{ height: 'calc(100vh - 40px)' }}><ReviewWorkspace {...workspaceProps({ caseId })} askPanel={summaryVariant === 'panel' ? <LiteratureSearchPanel variant="panel" /> : null} /></div>
    {/* Earlier guided demonstrations, as on the Research page's explicit demo entry. */}
    <section aria-label="Earlier guided demonstrations"><GuidedEvidencePanel key={caseId} /></section>
  </>
}
if (new URLSearchParams(location.search).has('summary')) document.getElementById('root').classList.add('pw-app')
createRoot(document.getElementById('root')).render(<Fixture />)
