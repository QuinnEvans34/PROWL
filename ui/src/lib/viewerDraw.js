const listenersByViewer = new WeakMap()

/** Observe completed frames without stacking wrappers as overlays change. */
export function observeViewerDraw(viewer, listener) {
  let entry = listenersByViewer.get(viewer)
  if (!entry) {
    const original = viewer.drawSceneCore
    if (typeof original !== 'function') return () => {}
    const listeners = new Set()
    function drawWithListeners(...args) {
      const result = original.apply(this, args)
      listeners.forEach(refresh => refresh())
      return result
    }
    entry = { original, listeners, drawWithListeners }
    viewer.drawSceneCore = drawWithListeners
    listenersByViewer.set(viewer, entry)
  }
  entry.listeners.add(listener)
  return () => {
    entry.listeners.delete(listener)
    if (entry.listeners.size) return
    if (viewer.drawSceneCore === entry.drawWithListeners) viewer.drawSceneCore = entry.original
    listenersByViewer.delete(viewer)
  }
}
