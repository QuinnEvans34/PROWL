// NiiVue's public setters each refresh every volume texture. Group synchronous
// presentation changes so they become visible together, with one final refresh.
// Never put asynchronous work in this callback.
export function batchViewerUpdate(nv, change) {
  const update = nv.updateGLVolume
  const draw = nv.drawScene
  const updateOwn = Object.getOwnPropertyDescriptor(nv, 'updateGLVolume')
  const drawOwn = Object.getOwnPropertyDescriptor(nv, 'drawScene')
  let volumeDirty = false
  let sceneDirty = false
  nv.updateGLVolume = () => { volumeDirty = true }
  nv.drawScene = () => { sceneDirty = true }
  let succeeded = false
  try {
    const result = change()
    if (result?.then) throw new Error('Viewer updates must be synchronous')
    succeeded = true
    return result
  } finally {
    if (updateOwn) Object.defineProperty(nv, 'updateGLVolume', updateOwn)
    else delete nv.updateGLVolume
    if (drawOwn) Object.defineProperty(nv, 'drawScene', drawOwn)
    else delete nv.drawScene
    // updateGLVolume already draws the scene in the installed NiiVue version.
    if (succeeded && volumeDirty) update.call(nv)
    else if (succeeded && sceneDirty) draw.call(nv)
  }
}
