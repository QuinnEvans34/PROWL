export function preparedViewerCtPath({ caseData, mode = '2d', showFull = false, preferNativeFull = true }) {
  const files = caseData?.files
  if (showFull) {
    if (mode === '3d' && preferNativeFull && files?.ct_full_native) return files.ct_full_native
    if (files?.ct_full) return files.ct_full
  }
  // Native studies keep a whole-body-width `ct` for 2D; the 3D region scene uses a
  // pancreas-box crop so "Region" is a real close-up and loads a fraction of the voxels.
  if (mode === '3d' && files?.ct_region) return files.ct_region
  return files?.ct || ''
}

// Both the pane coordinator and the renderer use this identity to reject delayed
// navigation/window events from a previous scan or image source.
export function viewerSceneKey({ caseData, sources = ['pred'], mode = '2d', showFull = false, preferNativeFull = true, enableDifferenceAssets = false, assetUrls = null }) {
  return [
    caseData?.case_id || caseData?.files?.ct || 'no-case',
    assetUrls?.ct || preparedViewerCtPath({ caseData, mode, showFull, preferNativeFull }),
    sources.join('|'),
    sources.map(source => `${source}:${assetUrls?.[source] || caseData?.files?.[source] || ''}`).join('|'),
    mode === '3d' ? ['pancreas', 'lesion'].flatMap(anatomies =>
      sources.map(source => assetUrls?.mesh?.[`${anatomies}_${source}`] || caseData?.files?.mesh?.[`${anatomies}_${source}`] || '')).join('|') : '',
    mode,
    showFull ? 'full' : 'crop',
    enableDifferenceAssets ? 'difference-ready' : 'standard',
  ].join('::')
}
