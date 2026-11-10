// Both the pane coordinator and the renderer use this identity to reject delayed
// navigation/window events from a previous scan or image source.
export function viewerSceneKey({ caseData, sources = ['pred'], mode = '2d', showFull = false, enableDifferenceAssets = false, assetUrls = null }) {
  return [
    caseData?.case_id || caseData?.files?.ct || 'no-case',
    assetUrls?.ct || (showFull && caseData?.files?.ct_full ? caseData.files.ct_full : caseData?.files?.ct) || '',
    sources.join('|'),
    sources.map(source => `${source}:${assetUrls?.[source] || caseData?.files?.[source] || ''}`).join('|'),
    mode,
    showFull ? 'full' : 'crop',
    enableDifferenceAssets ? 'difference-ready' : 'standard',
  ].join('::')
}
