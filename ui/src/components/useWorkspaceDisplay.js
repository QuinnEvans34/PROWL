import { useCallback, useEffect, useRef, useState } from 'react'

const fullscreenElement = doc => doc.fullscreenElement || doc.webkitFullscreenElement
const requestFullscreen = element => {
  // Keep this call in the click's activation stack, including Safari's older API.
  if (element.requestFullscreen) return element.requestFullscreen({ navigationUI: 'hide' })
  return element.webkitRequestFullscreen()
}
const exitFullscreen = doc => doc.exitFullscreen ? doc.exitFullscreen() : doc.webkitExitFullscreen()
const supportsFullscreen = (element, doc) => Boolean(
  (doc.fullscreenEnabled !== false && element.requestFullscreen && doc.exitFullscreen)
  || (doc.webkitFullscreenEnabled !== false && element.webkitRequestFullscreen && doc.webkitExitFullscreen)
)

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
    setFullscreenAvailable(supportsFullscreen(container, doc))
    const syncFullscreen = () => setIsFullscreen(fullscreenElement(doc) === container)
    const handleEscape = event => {
      if (event.key !== 'Escape') return
      const ownsFullscreen = fullscreenElement(doc) === container
      if (!focusRef.current && !ownsFullscreen) return
      // Exiting a display mode consumes Escape. The workspace's ordinary Escape
      // selection handler must not also clear the current anatomy or isolate view.
      event.stopPropagation()
      setFocusMode(false)
      if (ownsFullscreen) {
        Promise.resolve().then(() => {
          if (fullscreenElement(doc) === container) return exitFullscreen(doc)
          return undefined
        }).catch(() => {
          setFullscreenError('Unable to exit full screen. Use your browser full-screen control.')
        })
      }
    }
    syncFullscreen()
    doc.addEventListener('fullscreenchange', syncFullscreen)
    doc.addEventListener('webkitfullscreenchange', syncFullscreen)
    doc.addEventListener('keydown', handleEscape)
    return () => {
      doc.removeEventListener('fullscreenchange', syncFullscreen)
      doc.removeEventListener('webkitfullscreenchange', syncFullscreen)
      doc.removeEventListener('keydown', handleEscape)
    }
  }, [containerRef])

  const toggleFullscreen = useCallback(async () => {
    const container = containerRef.current
    const doc = container?.ownerDocument
    if (!doc) return false
    setFullscreenError('')
    try {
      if (fullscreenElement(doc) === container) {
        await exitFullscreen(doc)
      } else if (supportsFullscreen(container, doc)) {
        await requestFullscreen(container)
      } else {
        setFullscreenError('This browser cannot use display full screen. Open PROWL in Safari, Chrome or Edge for full screen, or choose Focus workspace to fill this window.')
        return false
      }
      setIsFullscreen(fullscreenElement(doc) === container)
      return true
    } catch {
      setFullscreenError('Display full screen could not open. Try PROWL in Safari, Chrome or Edge, or choose Focus workspace to fill this window.')
      return false
    }
  }, [containerRef])

  return { focusMode, setFocusMode, toggleFocus, isFullscreen, toggleFullscreen, fullscreenAvailable, fullscreenError }
}
