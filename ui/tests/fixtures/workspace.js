// Entirely synthetic legacy component props; not a validated capstone case package.
export function workspaceProps(overrides = {}) {
  return {
    caseId: 'SYNTHETIC_A', caseData: {
      files: { ct: 'synthetic-region.nii.gz', ct_full: 'synthetic-abdomen.nii.gz' },
      gt_has_lesion: false,
    },
    profile: { eyebrow: 'Synthetic fixture', label: 'No patient data' },
    caseItems: [], isCurated: false, hasLiveResult: false, liveResult: null,
    isAnalyzing: false, endpointStatus: 'offline', truthRevealed: false,
    reviewStatus: 'unreviewed', finding: { lesionFlagged: false }, overlap: {},
    onSelectScan() {}, onAnalyze: async () => false, onRevealTruth: () => false,
    onResetScan() {}, onSetReviewStatus() {}, onOpenComparison() {}, onOpenLibrary() {},
    ...overrides,
  }
}
