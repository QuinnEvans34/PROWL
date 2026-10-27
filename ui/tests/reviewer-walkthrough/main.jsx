import React from 'react'
import { createRoot } from 'react-dom/client'
import ReviewDecisionPanel from '../../src/components/ReviewDecisionPanel.jsx'
import '../../src/styles/tokens.css'
import '../../src/index.css'
const identity = await (await fetch('/walkthrough-identity')).json()
const archived = new URLSearchParams(location.search).get('review')
createRoot(document.getElementById('root')).render(<main style={{maxWidth:850,margin:'24px auto'}}>
  <h1>Isolated reviewer walkthrough</h1>
  <p>Synthetic transport fixture only. No patient data, model inference, contour assessment or measurement qualification.</p>
  <ReviewDecisionPanel base={archived ? `/review-records/packages/${archived}/files` : '/saved-prediction'} manifestHash={identity.hash} manifest={identity.manifest}/>
</main>)
