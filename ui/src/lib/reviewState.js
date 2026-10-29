export const EVIDENCE_MODES = ['ct', 'prediction', 'truth', 'overlap']
export const ANATOMY_FOCUS = ['all', 'pancreas', 'lesion']
export const SOURCE_FOCUS = ['both', 'pred', 'gt', 'difference']

export function makeReviewState({ hasPrediction = false } = {}) {
  return {
    viewMode: '2d',
    activePlane: 'multiplanar',
    interactionMode: 'navigate',
    evidenceMode: hasPrediction ? 'prediction' : 'ct',
    anatomyFocus: 'all',
    sourceFocus: 'both',
    focusTreatment: 'context',
    selectedObject: null,
    layerVisibility: {
      pancreas: true,
      lesion: true,
      pred: true,
      gt: true,
    },
    showFull: false,
    displayPreset: 'anatomy',
    ctWindow: 'soft',
    overlayOpacity: 0.62,
  ctOpacity: 0.44,
    clipEnabled: true,
    clipProgress: 100,
    resetToken: 0,
    drawerOpen: true,
    settingsOpen: false,
  }
}

export function reviewReducer(state, action) {
  switch (action.type) {
    case 'CASE_CHANGED':
      return makeReviewState({ hasPrediction: action.hasPrediction })
    // A live prediction arrived for a scan that loaded unmarked. Advance the view from
    // the bare CT to the model proposal WITHOUT resetting the rest of the review state
    // (CASE_CHANGED would wipe layer toggles, opacity, and the current plane).
    case 'PREDICTION_READY':
      return state.evidenceMode === 'ct'
        ? { ...state, evidenceMode: 'prediction', selectedObject: null }
        : state
    case 'SET_VIEW_MODE':
      return {
        ...state,
        viewMode: action.value,
        interactionMode: action.value === '3d' ? 'rotate' : 'navigate',
        settingsOpen: false,
      }
    case 'SET_ACTIVE_PLANE':
      return { ...state, activePlane: action.value }
    case 'SET_INTERACTION_MODE':
      return { ...state, interactionMode: action.value }
    case 'SET_EVIDENCE_MODE':
      return {
        ...state,
        evidenceMode: action.value,
        sourceFocus: action.value === 'overlap' ? state.sourceFocus : 'both',
        selectedObject: null,
      }
    case 'SET_ANATOMY_FOCUS':
      return {
        ...state,
        anatomyFocus: action.value,
        selectedObject: action.value === 'all' ? null : state.selectedObject,
        layerVisibility: action.value === 'all'
          ? state.layerVisibility
          : { ...state.layerVisibility, [action.value]: true },
      }
    case 'SET_SOURCE_FOCUS':
      return { ...state, sourceFocus: action.value, selectedObject: null }
    case 'SET_FOCUS_TREATMENT':
      return { ...state, focusTreatment: action.value }
    case 'SELECT_OBJECT':
      return {
        ...state,
        selectedObject: action.value,
        anatomyFocus: action.value?.anatomy || 'all',
        sourceFocus: action.value?.source || state.sourceFocus,
        layerVisibility: action.value
          ? {
              ...state.layerVisibility,
              [action.value.anatomy]: true,
              ...(action.value.source === 'pred' || action.value.source === 'gt'
                ? { [action.value.source]: true }
                : {}),
            }
          : state.layerVisibility,
      }
    case 'CLEAR_SELECTION':
      return { ...state, selectedObject: null, anatomyFocus: 'all' }
    case 'TOGGLE_LAYER':
      return {
        ...state,
        layerVisibility: {
          ...state.layerVisibility,
          [action.layer]: !state.layerVisibility[action.layer],
        },
      }
    case 'PATCH_SETTINGS':
      return { ...state, ...action.value }
    case 'TOGGLE_SETTINGS':
      return { ...state, settingsOpen: !state.settingsOpen }
    case 'TOGGLE_DRAWER':
      return { ...state, drawerOpen: !state.drawerOpen }
    case 'RESET_VIEW':
      return {
        ...state,
        anatomyFocus: 'all',
        activePlane: 'multiplanar',
        interactionMode: state.viewMode === '3d' ? 'rotate' : 'navigate',
        sourceFocus: 'both',
        focusTreatment: 'context',
        selectedObject: null,
        layerVisibility: {
          pancreas: true,
          lesion: true,
          pred: true,
          gt: true,
        },
        displayPreset: 'anatomy',
        overlayOpacity: 0.62,
        ctOpacity: 0.44,
        clipEnabled: true,
        clipProgress: 100,
        resetToken: state.resetToken + 1,
        settingsOpen: false,
      }
    default:
      return state
  }
}
