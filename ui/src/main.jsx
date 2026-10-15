import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import './index.css'
const SavedPredictionView = React.lazy(() => import('./components/SavedPredictionView.jsx'))
const ResearchDemo = React.lazy(() => import('./components/ResearchDemo.jsx'))

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {window.location.pathname === '/research'
      ? <React.Suspense fallback={<p>Loading research evidence…</p>}><ResearchDemo /></React.Suspense>
      : window.location.pathname === '/saved' ? <React.Suspense fallback={<p>Loading saved viewer…</p>}><SavedPredictionView /></React.Suspense> : <App />}
  </React.StrictMode>
)
