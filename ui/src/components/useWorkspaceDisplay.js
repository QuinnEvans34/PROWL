import { useCallback, useEffect, useRef, useState } from 'react'

// Display modes change only the surrounding layout. Keep the workspace and its
// viewers mounted so NiiVue retains slices, zoom, pan, windows and loaded layers.
export function useWorkspaceDisplay(containerRef) {
  const [focusMode, setFocusMode] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [fullscreenAvailable, setFullscreenAvailable] = useState(false)
  const [fullscreenError, setFullscreenError] = useState('')
  const focusRef = useRef(focusMode)
  focusRef.current = focusMode

  const toggleFocus = useCallback(() => setFocusMode(value => !value), [])

  useEffect(() => {
    const container = containerRef.current
    const doc = container?.ownerDocument
    if (!doc) return undefined
    setFullscreenAvailable(doc.fullscreenEnabled !== false
      && typeof container.requestFullscreen === 'function'
      && typeof doc.exitFullscreen === 'function')
    const syncFullscreen = () => setIsFullscreen(doc.fullscreenElement === container)
    const handleEscape = event => {
      if (event.key !== 'Escape') return
      const ownsFullscreen = doc.fullscreenElement === container
      if (!focusRef.current && !ownsFullscreen) return
      // Exiting a display mode consumes Escape. The workspace's ordinary Escape
      // selection handler must not also clear the current anatomy or isolate view.
      event.stopPropagation()
      setFocusMode(false)
      if (ownsFullscreen) {
        Promise.resolve().then(() => {
          if (doc.fullscreenElement === container) return doc.exitFullscreen()
          return undefined
        }).catch(() => {
          setFullscreenError('Unable to exit full screen. Use your browser full-screen control.')
        })
      }
    }
    syncFullscreen()
    doc.addEventListener('fullscreenchange', syncFullscreen)
    doc.addEventListener('keydown', handleEscape)
    return () => {
      doc.removeEventListener('fullscreenchange', syncFullscreen)
      doc.removeEventListener('keydown', handleEscape)
    }
  }, [containerRef])

  const toggleFullscreen = useCallback(async () => {
    const container = containerRef.current
    const doc = container?.ownerDocument
    if (!doc) return false
    setFullscreenError('')
    try {
      if (doc.fullscreenElement === container) {
        await doc.exitFullscreen()
      } else if (doc.fullscreenEnabled !== false && typeof container.requestFullscreen === 'function'
        && typeof doc.exitFullscreen === 'function') {
        await container.requestFullscreen()
      } else {
        setFocusMode(true)
        setFullscreenError('Full screen is unavailable here. Workspace focus is enabled.')
        return false
      }
      setIsFullscreen(doc.fullscreenElement === container)
      return true
    } catch {
      setFocusMode(true)
      setFullscreenError('Full screen could not open. Workspace focus is enabled.')
      return false
    }
  }, [containerRef])

  return { focusMode, setFocusMode, toggleFocus, isFullscreen, toggleFullscreen, fullscreenAvailable, fullscreenError }
}
