import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import './styles/tokens.css'
import './index.css'
import './styles/shell.css'
import './styles/workbench.css'
import './styles/assistant.css'
import './styles/pages.css'

// All routes (/, /workbench, /research, /saved) render inside the shared PROWL shell.
createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
