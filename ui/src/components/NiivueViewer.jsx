import { useEffect, useRef, useState } from 'react'
import { DRAG_MODE, Niivue } from '@niivue/niivue'
import { LoaderCircle, TriangleAlert } from 'lucide-react'

import { verifyNativeVolumes } from '../lib/nativeGeometry.js'

const BASE = '/cases'

const SOURCE_COLORS = {
  pred: {
    pancreas: [38, 197, 166],
    lesion: [249, 99, 99],
  },
  gt: {
    pancreas: [56, 189, 248],
    lesion: [251, 191, 36],
  },
}

const DIFFERENCE_COLORS = {
  agreement: [196, 181, 253],
  predOnly: [244, 63, 94],
  gtOnly: [251, 191, 36],
}

const CT_WINDOWS = {
  soft: { cal_min: 0.08, cal_max: 0.72 },
  contrast: { cal_min: 0.16, cal_max: 0.6 },
  wide: { cal_min: 0, cal_max: 1 },
}

const PLANE_AXIS = {
  sagittal: 0,
  coronal: 1,
  axial: 2,
}

const PLANE_META = {
  axial: ['Axial', 'Top-down view'],
  coronal: ['Coronal', 'Front view'],
  sagittal: ['Sagittal', 'Side view'],
}

const LABEL_BOUNDS_CACHE = new WeakMap()

function clamp255(value) {
  return Math.max(0, Math.min(255, Math.round(value)))
}

function effectiveCtOpacity(ctOpacity, clip) {
  if (!clip?.enabled) return ctOpacity
  const progress = Math.max(0, Math.min(100, Number(clip?.progress) || 0))
  return progress >= 99.5 ? 0 : ctOpacity
}

function anatomyAlpha(anatomy, {
  anatomyFocus,
  focusTreatment,
  selectedObject,
  source,
}) {
  if (selectedObject) {
    const isSelected = selectedObject.source === source && selectedObject.anatomy === anatomy
    if (isSelected) return 255
    if (focusTreatment === 'isolate') return 0
    if (selectedObject.anatomy === anatomy) return 48
    return anatomy === 'pancreas' ? 34 : 76
  }

  if (anatomyFocus === 'all') return anatomy === 'pancreas' ? 188 : 255
  if (anatomyFocus === anatomy) return 255
  if (focusTreatment === 'isolate') return 0
  return anatomy === 'pancreas' ? 36 : 82
}

function labelColormap(source, presentation) {
  const colors = SOURCE_COLORS[source]
  const sourceScale = (
    presentation.sourceFocus === 'pred' || presentation.sourceFocus === 'gt'
  ) && presentation.sourceFocus !== source ? 0.18 : 1
  const pancreasAlpha = presentation.showPancreas
    ? anatomyAlpha('pancreas', { ...presentation, source }) * sourceScale
    : 0
  const lesionAlpha = presentation.showLesion
    ? anatomyAlpha('lesion', { ...presentation, source }) * sourceScale
    : 0

  return {
    R: [0, colors.pancreas[0], colors.lesion[0]],
    G: [0, colors.pancreas[1], colors.lesion[1]],
    B: [0, colors.pancreas[2], colors.lesion[2]],
    A: [0, clamp255(pancreasAlpha), clamp255(lesionAlpha)],
    I: [0, 1, 2],
    labels: ['Background', 'Pancreas', 'Lesion'],
  }
}

function differenceColormap({ selectedObject, anatomy }) {
  const selectedRegion = selectedObject?.source === 'difference'
    && selectedObject.anatomy === anatomy
    ? selectedObject.region
    : null
  const alpha = (region) => {
    if (!selectedRegion) return region === 'agreement' ? 205 : 255
    return selectedRegion === region ? 255 : 35
  }
  return {
    R: [0, DIFFERENCE_COLORS.agreement[0], DIFFERENCE_COLORS.predOnly[0], DIFFERENCE_COLORS.gtOnly[0]],
    G: [0, DIFFERENCE_COLORS.agreement[1], DIFFERENCE_COLORS.predOnly[1], DIFFERENCE_COLORS.gtOnly[1]],
    B: [0, DIFFERENCE_COLORS.agreement[2], DIFFERENCE_COLORS.predOnly[2], DIFFERENCE_COLORS.gtOnly[2]],
    A: [0, alpha('agreement'), alpha('predOnly'), alpha('gtOnly')],
    I: [0, 1, 2, 3],
    labels: ['Background', 'Agreement', 'Prediction only', 'Reference only'],
  }
}

function voxelToWorld(volume, voxel) {
  const affine = volume?.hdr?.affine
  if (!Array.isArray(affine) || !Array.isArray(affine[0])) return null

  const [x, y, z] = voxel
  const world = [
    affine[0][0] * x + affine[0][1] * y + affine[0][2] * z + affine[0][3],
    affine[1][0] * x + affine[1][1] * y + affine[1][2] * z + affine[1][3],
    affine[2][0] * x + affine[2][1] * y + affine[2][2] * z + affine[2][3],
  ]
  return world.every(Number.isFinite) ? world : null
}

function labelCentroidMM(volume, requestedLabel = 1) {
  const image = volume?.img
  const dims = volume?.hdr?.dims
  if (!image || !dims || dims.length < 4) return null

  const nx = Number(dims[1])
  const ny = Number(dims[2])
  const nz = Number(dims[3])
  const voxelCount = nx * ny * nz
  if (!Number.isFinite(voxelCount) || voxelCount <= 0 || image.length < voxelCount) return null

  let count = 0
  let sumX = 0
  let sumY = 0
  let sumZ = 0
  let foregroundCount = 0
  let foregroundX = 0
  let foregroundY = 0
  let foregroundZ = 0

  for (let index = 0; index < voxelCount; index += 1) {
    const value = Math.round(Number(image[index]))
    if (value <= 0) continue

    const x = index % nx
    const yz = Math.floor(index / nx)
    const y = yz % ny
    const z = Math.floor(yz / ny)
    foregroundCount += 1
    foregroundX += x
    foregroundY += y
    foregroundZ += z

    if (value === requestedLabel) {
      count += 1
      sumX += x
      sumY += y
      sumZ += z
    }
  }

  if (count > 0) {
    return voxelToWorld(volume, [sumX / count, sumY / count, sumZ / count])
  }
  if (requestedLabel === 1 && foregroundCount > 0) {
    return voxelToWorld(volume, [
      foregroundX / foregroundCount,
      foregroundY / foregroundCount,
      foregroundZ / foregroundCount,
    ])
  }
  return null
}

function volumeCenterMM(volume) {
  const dims = volume?.hdr?.dims
  if (!dims || dims.length < 4) return null
  return voxelToWorld(volume, [
    (Number(dims[1]) - 1) / 2,
    (Number(dims[2]) - 1) / 2,
    (Number(dims[3]) - 1) / 2,
  ])
}

function labelBounds(volume, requestedLabel) {
  if (!volume) return null
  const cached = LABEL_BOUNDS_CACHE.get(volume)
  if (cached?.has(requestedLabel)) return cached.get(requestedLabel)

  const image = volume?.img
  const dims = volume?.hdr?.dims
  if (!image || !dims || dims.length < 4) return null

  const nx = Number(dims[1])
  const ny = Number(dims[2])
  const nz = Number(dims[3])
  const voxelCount = nx * ny * nz
  if (!Number.isFinite(voxelCount) || voxelCount <= 0 || image.length < voxelCount) return null

  const min = [nx, ny, nz]
  const max = [-1, -1, -1]
  for (let index = 0; index < voxelCount; index += 1) {
    if (Math.round(Number(image[index])) !== requestedLabel) continue
    const x = index % nx
    const yz = Math.floor(index / nx)
    const y = yz % ny
    const z = Math.floor(yz / ny)
    min[0] = Math.min(min[0], x)
    min[1] = Math.min(min[1], y)
    min[2] = Math.min(min[2], z)
    max[0] = Math.max(max[0], x)
    max[1] = Math.max(max[1], y)
    max[2] = Math.max(max[2], z)
  }
  const bounds = max[0] < 0 ? null : { min, max }
  const nextCache = cached || new Map()
  nextCache.set(requestedLabel, bounds)
  LABEL_BOUNDS_CACHE.set(volume, nextCache)
  return bounds
}

function navigationSnapshot(nv, maskVolume) {
  const dims = nv?.volumes?.[0]?.hdr?.dims
  const crosshair = nv?.scene?.crosshairPos
  if (!dims || dims.length < 4 || !crosshair) return null

  const totals = {
    sagittal: Math.max(1, Number(dims[1])),
    coronal: Math.max(1, Number(dims[2])),
    axial: Math.max(1, Number(dims[3])),
  }
  const indices = {
    sagittal: Math.round(Math.min(1, Math.max(0, Number(crosshair[0]))) * (totals.sagittal - 1)),
    coronal: Math.round(Math.min(1, Math.max(0, Number(crosshair[1]))) * (totals.coronal - 1)),
    axial: Math.round(Math.min(1, Math.max(0, Number(crosshair[2]))) * (totals.axial - 1)),
  }
  const ranges = {}
  for (const [anatomy, labelValue] of [['pancreas', 1], ['lesion', 2]]) {
    const bounds = labelBounds(maskVolume, labelValue)
    ranges[anatomy] = bounds
      ? {
          sagittal: [bounds.min[0], bounds.max[0]],
          coronal: [bounds.min[1], bounds.max[1]],
          axial: [bounds.min[2], bounds.max[2]],
        }
      : null
  }
  return { indices, totals, ranges }
}

function captureViewState(nv) {
  if (!nv?.scene?.crosshairPos) return null
  return {
    crosshair: Array.from(nv.scene.crosshairPos),
    pan2Dxyzmm: Array.from(nv.scene.pan2Dxyzmm || [0, 0, 0, 1]),
    azimuth: Number(nv.scene.renderAzimuth),
    elevation: Number(nv.scene.renderElevation),
    scale: Number(nv.scene.volScaleMultiplier),
    pivot3D: Array.isArray(nv.pivot3D) ? [...nv.pivot3D] : null,
  }
}

function restoreViewState(nv, view, mode, crosshairOnly = false) {
  if (!view) return false
  if (Array.isArray(view.crosshair) && view.crosshair.length >= 3) {
    nv.scene.crosshairPos = new Float32Array(view.crosshair.slice(0, 3))
  }
  if (crosshairOnly) {
    if (mode === '3d') {
      const world = nv.frac2mm(nv.scene.crosshairPos, 0, true)
      if (world && Array.from(world).slice(0, 3).every(Number.isFinite)) {
        nv.pivot3D = Array.from(world).slice(0, 3)
      }
    }
    return true
  }
  if (Array.isArray(view.pan2Dxyzmm) && view.pan2Dxyzmm.length >= 4) {
    nv.scene.pan2Dxyzmm = new Float32Array(view.pan2Dxyzmm.slice(0, 4))
  }
  if (mode === '3d') {
    if (Number.isFinite(view.azimuth) && Number.isFinite(view.elevation)) {
      nv.scene.renderAzimuth = view.azimuth
      nv.scene.renderElevation = view.elevation
    }
    if (Number.isFinite(view.scale)) nv.scene.volScaleMultiplier = view.scale
    if (Array.isArray(view.pivot3D) && view.pivot3D.length >= 3) {
      nv.pivot3D = view.pivot3D.slice(0, 3)
    }
  }
  return true
}

function focusOnWorldPoint(nv, worldMM, mode) {
  if (!worldMM) return false
  const fraction = nv.mm2frac(worldMM, 0, true)
  if (!fraction || !Array.from(fraction).every(Number.isFinite)) return false

  nv.scene.crosshairPos = new Float32Array(Array.from(fraction, (value) => (
    Math.min(1, Math.max(0, value))
  )))
  if (mode === '3d') nv.pivot3D = [...worldMM]
  return true
}

function clearMeshes(nv) {
  ;(nv.meshes || []).slice().forEach((mesh) => {
    try {
      nv.removeMesh(mesh)
    } catch {
      // A mesh can already be gone while NiiVue is switching cases.
    }
  })
}

function semanticFromLocation(location, visibleSources, differenceMode) {
  const values = Array.isArray(location?.values) ? location.values : []
  if (differenceMode) {
    for (const labelValue of [2, 3, 1]) {
      const match = values.find((value) => (
        typeof value?.name === 'string'
        && value.name.startsWith('diff-')
        && Math.round(Number(value.value)) === labelValue
      ))
      if (match) {
        return {
          source: 'difference',
          anatomy: match.name.replace('diff-', '').split('.')[0],
          region: {
            1: 'agreement',
            2: 'predOnly',
            3: 'gtOnly',
          }[labelValue],
        }
      }
    }
  }
  const priority = [...visibleSources].reverse()

  for (const labelValue of [2, 1]) {
    for (const source of priority) {
      const match = values.find((value) => (
        (
          value?.name === source
          || value?.name === `${source}.nii.gz`
          || value?.name?.startsWith(`${source}.`)
        )
        && Math.round(Number(value.value)) === labelValue
      ))
      if (match) {
        return {
          source,
          anatomy: labelValue === 2 ? 'lesion' : 'pancreas',
        }
      }
    }
  }
  return null
}

function meshOpacity({
  anatomy,
  source,
  visible,
  anatomyFocus,
  focusTreatment,
  selectedObject,
  overlayOpacity,
  sourceFocus,
}) {
  if (!visible) return 0
  if (selectedObject) {
    const selected = selectedObject.source === source && selectedObject.anatomy === anatomy
    if (selected) return 1
    if (focusTreatment === 'isolate') return 0
    if (selectedObject.anatomy === anatomy) return 0.16
    return anatomy === 'pancreas' ? 0.11 : 0.3
  }
  const sourceScale = (sourceFocus === 'pred' || sourceFocus === 'gt') && sourceFocus !== source
    ? 0.16
    : 1
  if (anatomyFocus !== 'all' && anatomyFocus !== anatomy) {
    if (focusTreatment === 'isolate') return 0
    return (anatomy === 'pancreas' ? 0.12 : 0.3) * sourceScale
  }
  const base = anatomy === 'pancreas' ? 0.68 : 1
  return Math.max(0, Math.min(1, base * (0.65 + overlayOpacity * 0.5) * sourceScale))
}

export default function NiivueViewer({
  caseData,
  assetUrls = null,
  nativeGeometry = null,
  ctRange = null,
  sources = ['pred'],
  visibleSources = null,
  mode = '2d',
  showFull = false,
  overlayOpacity = 0.62,
  ctOpacity = 0.18,
  ctWindow = 'soft',
  showPancreas = true,
  showLesion = true,
  anatomyFocus = 'all',
  sourceFocus = 'both',
  differenceMode = false,
  enableDifferenceAssets = false,
  focusTreatment = 'context',
  selectedObject = null,
  onSelectObject = null,
  activePlane = 'multiplanar',
  interactionMode = 'navigate',
  navigationCommand = null,
  onNavigationChange = null,
  clip = null,
  resetToken = 0,
  compact = false,
  guided = false,
  label = 'Medical image viewer',
}) {
  const canvasRef = useRef(null)
  const nvRef = useRef(null)
  const registryRef = useRef({
    volumeIndexes: new Map(),
    volumes: new Map(),
    differenceVolumeIndexes: new Map(),
    differenceVolumes: new Map(),
    meshes: new Map(),
  })
  const locationRef = useRef(null)
  const pointerStartRef = useRef(null)
  const loadedSceneKeyRef = useRef('')
  const currentSceneRef = useRef(null)
  const savedViewsRef = useRef(new Map())
  const latestCrosshairRef = useRef(new Map())
  const handledResetTokenRef = useRef(resetToken)
  const previousClipEnabledRef = useRef(Boolean(clip?.enabled))
  const clipFrameRef = useRef(null)
  const navigationFrameRef = useRef(null)
  const pendingNavigationRef = useRef(null)
  const lastNavigationSignatureRef = useRef('')
  const interactiveRef = useRef({
    mode,
    onSelectObject,
    onNavigationChange,
    visibleSources: visibleSources || sources,
    differenceMode,
  })
  const lastFocusedObjectRef = useRef('')
  const [state, setState] = useState({ status: 'loading', message: 'Preparing viewer' })
  const [sceneVersion, setSceneVersion] = useState(0)

  const renderedSources = visibleSources || sources
  const sceneKey = [
    caseData?.case_id || caseData?.files?.ct || 'no-case',
    sources.join('|'),
    mode,
    showFull ? 'full' : 'crop',
    enableDifferenceAssets ? 'difference-ready' : 'standard',
  ].join('::')

  function publishNavigation(nv, { immediate = false } = {}) {
    const maskVolume = registryRef.current.volumes.get('pred')
      || registryRef.current.volumes.get('gt')
      || registryRef.current.volumes.values().next().value
    const snapshot = navigationSnapshot(nv, maskVolume)
    if (!snapshot) return
    const signature = [
      snapshot.indices.sagittal,
      snapshot.indices.coronal,
      snapshot.indices.axial,
      snapshot.totals.sagittal,
      snapshot.totals.coronal,
      snapshot.totals.axial,
    ].join(':')
    if (signature === lastNavigationSignatureRef.current) return

    const commit = () => {
      navigationFrameRef.current = null
      const pending = pendingNavigationRef.current
      pendingNavigationRef.current = null
      if (!pending || pending.signature === lastNavigationSignatureRef.current) return
      lastNavigationSignatureRef.current = pending.signature
      const currentCase = currentSceneRef.current?.caseId
      if (currentCase) {
        latestCrosshairRef.current.set(currentCase, Array.from(nv.scene.crosshairPos))
      }
      interactiveRef.current.onNavigationChange?.(pending.snapshot)
    }

    pendingNavigationRef.current = { signature, snapshot }
    if (immediate) {
      if (navigationFrameRef.current !== null) {
        window.cancelAnimationFrame(navigationFrameRef.current)
      }
      commit()
      return
    }
    if (navigationFrameRef.current === null) {
      navigationFrameRef.current = window.requestAnimationFrame(commit)
    }
  }

  useEffect(() => {
    interactiveRef.current = {
      mode,
      onSelectObject,
      onNavigationChange,
      visibleSources: renderedSources,
      differenceMode,
    }
  }, [mode, onSelectObject, onNavigationChange, renderedSources.join('|'), differenceMode])

  useEffect(() => {
    if (!canvasRef.current) return undefined

    const canvas = canvasRef.current
    const nv = new Niivue({
      backColor: [0.018, 0.026, 0.042, 1],
      show3Dcrosshair: false,
      isColorbar: false,
      multiplanarShowRender: 0,
      // ROW (3): keep axial/coronal/sagittal in one row so the plane labels below
      // always sit over the matching view. AUTO switched to a 2x2 grid in tall viewers.
      multiplanarLayout: 3,
      clipPlaneColor: [0, 0, 0, 0],
      isClipPlanesCutaway: true,
      isClipAllVolumes: false,
      meshXRay: 0.22,
    })

    nv.attachToCanvas(canvas)
    nv.overlayOutlineWidth = 1.15
    nv.onLocationChange = (location) => {
      locationRef.current = location
      if (interactiveRef.current.mode === '2d') publishNavigation(nv)
    }
    nvRef.current = nv

    function handlePointerDown(event) {
      pointerStartRef.current = { x: event.clientX, y: event.clientY }
    }

    function handlePointerUp(event) {
      const start = pointerStartRef.current
      pointerStartRef.current = null
      if (!start) return
      if (Math.hypot(event.clientX - start.x, event.clientY - start.y) > 5) return

      const interaction = interactiveRef.current
      if (typeof interaction.onSelectObject !== 'function') return

      if (interaction.mode === '2d') {
        window.setTimeout(() => {
          interaction.onSelectObject(
            semanticFromLocation(
              locationRef.current,
              interaction.visibleSources,
              interaction.differenceMode,
            ),
          )
        }, 0)
        return
      }

      nv.resetBriCon(event)
      window.setTimeout(() => {
        const fraction = nv.scene?.crosshairPos
        if (!fraction) return
        const world = Array.from(nv.frac2mm(fraction, 0, true)).slice(0, 3)
        if (!world.every(Number.isFinite)) return

        let nearest = null
        registryRef.current.meshes.forEach((entry) => {
          if (!entry.mesh.visible || entry.mesh.opacity <= 0.02) return
          const result = nv.indexNearestXYZmm(entry.mesh.id, world[0], world[1], world[2])
          const distance = Number(result?.[1])
          if (!Number.isFinite(distance)) return
          if (!nearest || distance < nearest.distance) nearest = { ...entry, distance }
        })
        interaction.onSelectObject(
          nearest && nearest.distance <= 12
            ? { source: nearest.source, anatomy: nearest.anatomy }
            : null,
        )
      }, 0)
    }

    canvas.addEventListener('pointerdown', handlePointerDown)
    canvas.addEventListener('pointerup', handlePointerUp)

    return () => {
      if (clipFrameRef.current !== null) {
        window.cancelAnimationFrame(clipFrameRef.current)
        clipFrameRef.current = null
      }
      if (navigationFrameRef.current !== null) {
        window.cancelAnimationFrame(navigationFrameRef.current)
        navigationFrameRef.current = null
      }
      pendingNavigationRef.current = null
      canvas.removeEventListener('pointerdown', handlePointerDown)
      canvas.removeEventListener('pointerup', handlePointerUp)
      nvRef.current = null
    }
  }, [compact])

  useEffect(() => {
    const nv = nvRef.current
    if (!nv || !caseData) return undefined

    let cancelled = false

    async function loadScene() {
      try {
        const previousScene = currentSceneRef.current
        const previousView = captureViewState(nv)
        if (previousScene && previousView && loadedSceneKeyRef.current) {
          savedViewsRef.current.set(
            `${previousScene.caseId}::${previousScene.mode}`,
            previousView,
          )
          latestCrosshairRef.current.set(previousScene.caseId, previousView.crosshair)
        }

        loadedSceneKeyRef.current = ''
        lastNavigationSignatureRef.current = ''
        pendingNavigationRef.current = null
        setState({ status: 'loading', message: 'Loading prepared scan' })
        lastFocusedObjectRef.current = ''
        registryRef.current = {
          volumeIndexes: new Map(),
          volumes: new Map(),
          differenceVolumeIndexes: new Map(),
          differenceVolumes: new Map(),
          meshes: new Map(),
        }

        const ctPath = showFull && caseData.files.ct_full
          ? caseData.files.ct_full
          : caseData.files.ct
        const availableSources = sources.filter((source) => caseData.files[source])
        const renderedCtOpacity = effectiveCtOpacity(ctOpacity, clip)

        clearMeshes(nv)
        const volumes = [{
          url: assetUrls?.ct || `${BASE}/${ctPath}`,
          name: 'ct.nii.gz',
          colormap: 'gray',
          opacity: mode === '2d'
            ? 1
            : renderedCtOpacity,
          ...(ctRange ? { cal_min: ctRange[0], cal_max: ctRange[1] } : CT_WINDOWS[ctWindow]),
          trustCalMinMax: true,
          ignoreZeroVoxels: true,
        }]

        availableSources.forEach((source) => {
          volumes.push({
            url: assetUrls?.[source] || `${BASE}/${caseData.files[source]}`,
            name: `${source}.nii.gz`,
            colormap: 'warm',
            opacity: mode === '2d' ? overlayOpacity : 0,
            cal_min: 0,
            cal_max: 2,
          })
        })
        const canLoadDifference = enableDifferenceAssets
          && availableSources.includes('gt')
          && caseData.files.difference
        if (canLoadDifference) {
          for (const anatomy of ['pancreas', 'lesion']) {
            const differencePath = caseData.files.difference[anatomy]
            if (!differencePath) continue
            volumes.push({
              url: `${BASE}/${differencePath}`,
              name: `diff-${anatomy}.nii.gz`,
              colormap: 'warm',
              opacity: 0,
              cal_min: 0,
              cal_max: 3,
            })
          }
        }

        await nv.loadVolumes(volumes)
        if (cancelled) return
        if (nativeGeometry) verifyNativeVolumes(nv.volumes, nativeGeometry)

        availableSources.forEach((source, index) => {
          const volumeIndex = index + 1
          registryRef.current.volumeIndexes.set(source, volumeIndex)
          registryRef.current.volumes.set(source, nv.volumes[volumeIndex])
        })
        let differenceIndex = availableSources.length + 1
        if (canLoadDifference) {
          for (const anatomy of ['pancreas', 'lesion']) {
            if (!caseData.files.difference[anatomy]) continue
            registryRef.current.differenceVolumeIndexes.set(anatomy, differenceIndex)
            registryRef.current.differenceVolumes.set(anatomy, nv.volumes[differenceIndex])
            differenceIndex += 1
          }
        }

        if (mode === '2d') {
          const sliceType = {
            axial: nv.sliceTypeAxial,
            coronal: nv.sliceTypeCoronal,
            sagittal: nv.sliceTypeSagittal,
            multiplanar: nv.sliceTypeMultiplanar,
          }[activePlane] ?? nv.sliceTypeMultiplanar
          nv.setSliceType(sliceType)
          nv.setCrosshairColor([0.46, 0.57, 0.69, 0.78])
          nv.setAtlasOutline(0.32)
        } else {
          const meshFiles = caseData.files.mesh || {}
          const layers = []
          const layerSemantics = []

          availableSources.forEach((source) => {
            for (const anatomy of ['pancreas', 'lesion']) {
              const meshPath = meshFiles[`${anatomy}_${source}`]
              if (!meshPath) continue
              const colors = SOURCE_COLORS[source][anatomy]
              layers.push({
                url: `${BASE}/${meshPath}`,
                name: `${source}-${anatomy}.obj`,
                rgba255: [...colors, anatomy === 'pancreas' ? 190 : 255],
                opacity: anatomy === 'pancreas' ? 0.68 : 1,
              })
              layerSemantics.push({ source, anatomy })
            }
          })
          if (canLoadDifference) {
            for (const anatomy of ['pancreas', 'lesion']) {
              for (const [region, meshSuffix] of [
                ['agreement', 'agreement'],
                ['predOnly', 'pred_only'],
                ['gtOnly', 'gt_only'],
              ]) {
                const meshPath = meshFiles[`${anatomy}_${meshSuffix}`]
                if (!meshPath) continue
                const colors = DIFFERENCE_COLORS[region]
                layers.push({
                  url: `${BASE}/${meshPath}`,
                  name: `difference-${anatomy}-${region}.obj`,
                  rgba255: [...colors, 255],
                  opacity: 1,
                })
                layerSemantics.push({ source: 'difference', anatomy, region })
              }
            }
          }

          if (layers.length) await nv.loadMeshes(layers)
          if (cancelled) return

          layerSemantics.forEach((semantic, index) => {
            const mesh = nv.meshes[index]
            if (!mesh) return
            const semanticKey = semantic.region
              ? `${semantic.source}:${semantic.anatomy}:${semantic.region}`
              : `${semantic.source}:${semantic.anatomy}`
            registryRef.current.meshes.set(
              semanticKey,
              { ...semantic, mesh },
            )
            nv.setMeshShader(mesh.id, 'Hemispheric')
          })

          nv.setSliceType(nv.sliceTypeRender)
          nv.setRenderAzimuthElevation(
            clip?.enabled ? 0 : 120,
            clip?.enabled ? 0 : 15,
          )
          nv.setClipPlaneColor([0, 0, 0, 0])
          nv.setClipPlane(clip?.enabled
            ? [clip.depth, 0, 0]
            : [2, 0, 0])
        }

        const currentCaseId = caseData.case_id || caseData.files.ct
        const savedView = savedViewsRef.current.get(`${currentCaseId}::${mode}`)
        const latestCrosshair = latestCrosshairRef.current.get(currentCaseId)
        let restored = restoreViewState(nv, savedView, mode)
        if (latestCrosshair?.length >= 3) {
          restoreViewState(nv, { crosshair: latestCrosshair }, mode, true)
          restored = true
        }

        if (!restored) {
          const primaryVolume = registryRef.current.volumes.get(availableSources[0])
          const target = primaryVolume
            ? labelCentroidMM(primaryVolume, 1)
            : volumeCenterMM(nv.volumes[0])
          focusOnWorldPoint(nv, target, mode)
          if (mode === '3d' && compact) nv.setScale(1.55)
        }

        nv.updateGLVolume()
        nv.drawScene()
        currentSceneRef.current = { caseId: currentCaseId, mode }
        loadedSceneKeyRef.current = sceneKey
        publishNavigation(nv, { immediate: true })
        setSceneVersion((version) => version + 1)
        if (!cancelled) setState({ status: 'ready', message: 'Prepared result loaded' })
      } catch (error) {
        if (!cancelled) {
          setState({
            status: 'error',
            message: error instanceof Error ? error.message : 'The prepared scan could not be displayed.',
          })
        }
      }
    }

    loadScene()
    return () => {
      cancelled = true
    }
  }, [caseData, sources.join('|'), mode, showFull, enableDifferenceAssets, sceneKey])

  useEffect(() => {
    const nv = nvRef.current
    if (
      !nv
      || state.status !== 'ready'
      || loadedSceneKeyRef.current !== sceneKey
      || !nv.volumes?.[0]
    ) return

    const presentation = {
      anatomyFocus,
      focusTreatment,
      selectedObject,
      showPancreas,
      showLesion,
      sourceFocus,
    }

    try {
      const ctVolume = nv.volumes[0]
      const windowRange = ctRange ? { cal_min: ctRange[0], cal_max: ctRange[1] } : CT_WINDOWS[ctWindow] || CT_WINDOWS.soft
      ctVolume.cal_min = windowRange.cal_min
      ctVolume.cal_max = windowRange.cal_max

      if (mode === '2d') {
        registryRef.current.volumeIndexes.forEach((volumeIndex, source) => {
          const volume = nv.volumes[volumeIndex]
          if (!volume) return
          volume.setColormapLabel(labelColormap(source, presentation))
          nv.setOpacity(volumeIndex, !differenceMode && renderedSources.includes(source) ? overlayOpacity : 0)
        })
        registryRef.current.differenceVolumeIndexes.forEach((volumeIndex, anatomy) => {
          const volume = nv.volumes[volumeIndex]
          if (!volume) return
          volume.setColormapLabel(differenceColormap({ selectedObject, anatomy }))
          const anatomyVisible = anatomyFocus === 'all' || anatomyFocus === anatomy
          const layerVisible = anatomy === 'pancreas' ? showPancreas : showLesion
          nv.setOpacity(
            volumeIndex,
            differenceMode && anatomyVisible && layerVisible ? overlayOpacity : 0,
          )
        })
        nv.setOpacity(0, 1)
        nv.updateGLVolume()
        nv.drawScene()
        return
      }

      const renderedCtOpacity = effectiveCtOpacity(ctOpacity, clip)
      nv.setOpacity(
        0,
        selectedObject
          ? Math.min(renderedCtOpacity, 0.045)
          : renderedCtOpacity,
      )
      registryRef.current.meshes.forEach((entry) => {
        const structureVisible = entry.anatomy === 'pancreas' ? showPancreas : showLesion
        const sourceVisible = entry.source === 'difference'
          ? differenceMode
          : renderedSources.includes(entry.source)
        const opacity = meshOpacity({
          anatomy: entry.anatomy,
          source: entry.source,
          visible: structureVisible && sourceVisible,
          anatomyFocus,
          focusTreatment,
          selectedObject,
          overlayOpacity,
          sourceFocus,
        })
        const differenceSelected = selectedObject?.source === 'difference'
          && selectedObject.anatomy === entry.anatomy
          && selectedObject.region === entry.region
        const differenceVisible = differenceMode
          && entry.source === 'difference'
          && (anatomyFocus === 'all' || anatomyFocus === entry.anatomy)
        const regularVisible = !differenceMode && entry.source !== 'difference'
        const regionContextOpacity = selectedObject?.source === 'difference' && !differenceSelected
          ? (focusTreatment === 'isolate' ? 0 : 0.12)
          : 1
        const finalOpacity = entry.source === 'difference'
          ? (differenceVisible ? opacity * regionContextOpacity : 0)
          : (regularVisible ? opacity : 0)
        const color = entry.source === 'difference'
          ? DIFFERENCE_COLORS[entry.region]
          : SOURCE_COLORS[entry.source][entry.anatomy]
        entry.mesh.visible = finalOpacity > 0.01
        nv.setMeshProperty(entry.mesh.id, 'rgba255', new Uint8Array([
          color[0],
          color[1],
          color[2],
          clamp255(finalOpacity * 255),
        ]))
        nv.setMeshProperty(entry.mesh.id, 'opacity', finalOpacity)
        const isSelected = selectedObject
          && selectedObject.source === entry.source
          && selectedObject.anatomy === entry.anatomy
          && (entry.source !== 'difference' || selectedObject.region === entry.region)
        nv.setMeshShader(entry.mesh.id, isSelected ? 'Toon' : 'Hemispheric')
      })

      nv.updateGLVolume()
      nv.drawScene()
    } catch (error) {
      setState({
        status: 'error',
        message: error instanceof Error ? error.message : 'The viewer presentation could not be updated.',
      })
    }
  }, [
    sceneVersion,
    state.status,
    mode,
    overlayOpacity,
    ctOpacity,
    ctWindow,
    showPancreas,
    showLesion,
    anatomyFocus,
    sourceFocus,
    focusTreatment,
    selectedObject?.source,
    selectedObject?.anatomy,
    selectedObject?.region,
    renderedSources.join('|'),
    differenceMode,
    clip?.enabled,
    Number(clip?.progress || 0) >= 99.5,
    sceneKey,
  ])

  useEffect(() => {
    const nv = nvRef.current
    if (
      !nv
      || mode !== '2d'
      || state.status !== 'ready'
      || loadedSceneKeyRef.current !== sceneKey
    ) return
    const sliceType = {
      axial: nv.sliceTypeAxial,
      coronal: nv.sliceTypeCoronal,
      sagittal: nv.sliceTypeSagittal,
      multiplanar: nv.sliceTypeMultiplanar,
    }[activePlane] ?? nv.sliceTypeMultiplanar
    nv.setSliceType(sliceType)
    nv.drawScene()
    publishNavigation(nv)
  }, [activePlane, mode, sceneVersion, state.status, sceneKey])

  useEffect(() => {
    const nv = nvRef.current
    if (!nv || state.status !== 'ready' || loadedSceneKeyRef.current !== sceneKey) return

    let primary = DRAG_MODE.crosshair
    if (mode === '2d') {
      if (interactionMode === 'pan') primary = DRAG_MODE.pan
      if (interactionMode === 'window') primary = DRAG_MODE.windowing
      nv.setMouseEventConfig({
        leftButton: {
          primary,
          withShift: DRAG_MODE.pan,
          withCtrl: DRAG_MODE.crosshair,
        },
        rightButton: DRAG_MODE.windowing,
        centerButton: DRAG_MODE.pan,
      })
      nv.setTouchEventConfig({
        singleTouch: primary,
        doubleTouch: DRAG_MODE.pan,
      })
      return
    }

    primary = interactionMode === 'move' ? DRAG_MODE.slicer3D : DRAG_MODE.crosshair
    nv.setMouseEventConfig({
      leftButton: {
        primary,
        withShift: DRAG_MODE.slicer3D,
        withCtrl: DRAG_MODE.crosshair,
      },
      rightButton: DRAG_MODE.slicer3D,
      centerButton: DRAG_MODE.slicer3D,
    })
    nv.setTouchEventConfig({
      singleTouch: primary,
      doubleTouch: DRAG_MODE.slicer3D,
    })
  }, [interactionMode, mode, sceneVersion, state.status, sceneKey])

  useEffect(() => {
    const nv = nvRef.current
    if (
      !navigationCommand
      || !nv
      || state.status !== 'ready'
      || loadedSceneKeyRef.current !== sceneKey
      || !nv.volumes?.[0]
    ) return

    const command = navigationCommand
    if (command.type === 'slice') {
      const axis = PLANE_AXIS[command.plane]
      const total = Number(nv.volumes[0]?.hdr?.dims?.[axis + 1])
      if (Number.isInteger(axis) && Number.isFinite(total) && total > 1) {
        const index = Math.max(0, Math.min(total - 1, Number(command.index)))
        const next = Array.from(nv.scene.crosshairPos)
        next[axis] = index / (total - 1)
        nv.scene.crosshairPos = new Float32Array(next)
      }
    } else if (command.type === 'focus') {
      const volume = registryRef.current.volumes.get(command.source)
        || registryRef.current.volumes.get('pred')
        || registryRef.current.volumes.get('gt')
      const labelValue = command.anatomy === 'lesion' ? 2 : 1
      focusOnWorldPoint(nv, labelCentroidMM(volume, labelValue), mode)
      if (mode === '3d') {
        if (Number.isFinite(command.azimuth) && Number.isFinite(command.elevation)) {
          nv.setRenderAzimuthElevation(command.azimuth, command.elevation)
        }
        if (Number.isFinite(command.scale)) nv.setScale(command.scale)
      }
    } else if (command.type === 'camera') {
      nv.setRenderAzimuthElevation(command.azimuth, command.elevation)
    } else if (command.type === 'rotate') {
      nv.setRenderAzimuthElevation(
        Number(nv.scene.renderAzimuth) + Number(command.deltaAzimuth || 0),
        Math.max(-90, Math.min(90, Number(nv.scene.renderElevation) + Number(command.deltaElevation || 0))),
      )
    } else if (command.type === 'zoom') {
      const scale = Math.max(0.45, Math.min(2.5, Number(nv.scene.volScaleMultiplier) * command.factor))
      nv.setScale(scale)
    } else if (command.type === 'fit') {
      focusOnWorldPoint(nv, volumeCenterMM(nv.volumes[0]), mode)
      if (mode === '3d') nv.setScale(1)
      else nv.setPan2Dxyzmm([0, 0, 0, 1])
    }

    nv.drawScene()
    publishNavigation(nv)
  }, [navigationCommand?.id, sceneVersion, state.status, sceneKey, mode])

  useEffect(() => {
    const nv = nvRef.current
    if (
      !nv
      || state.status !== 'ready'
      || loadedSceneKeyRef.current !== sceneKey
      || !selectedObject
    ) return
    const focusKey = `${selectedObject.source}:${selectedObject.anatomy}`
    if (lastFocusedObjectRef.current === focusKey) return

    const volume = selectedObject.source === 'difference'
      ? registryRef.current.differenceVolumes.get(selectedObject.anatomy)
      : registryRef.current.volumes.get(selectedObject.source)
    const labelValue = selectedObject.source === 'difference'
      ? { agreement: 1, predOnly: 2, gtOnly: 3 }[selectedObject.region]
      : selectedObject.anatomy === 'lesion' ? 2 : 1
    if (focusOnWorldPoint(nv, labelCentroidMM(volume, labelValue), mode)) {
      lastFocusedObjectRef.current = focusKey
      nv.drawScene()
      publishNavigation(nv)
    }
  }, [
    sceneVersion,
    state.status,
    mode,
    selectedObject?.source,
    selectedObject?.anatomy,
    selectedObject?.region,
    sceneKey,
  ])

  useEffect(() => {
    const nv = nvRef.current
    if (
      !nv
      || mode !== '3d'
      || loadedSceneKeyRef.current !== sceneKey
      || !nv.volumes?.[0]
    ) return
    const justActivated = Boolean(clip?.enabled) && !previousClipEnabledRef.current
    previousClipEnabledRef.current = Boolean(clip?.enabled)
    if (clipFrameRef.current !== null) {
      window.cancelAnimationFrame(clipFrameRef.current)
    }
    clipFrameRef.current = window.requestAnimationFrame(() => {
      clipFrameRef.current = null
      nv.setClipPlane(clip?.enabled
        ? [clip.depth, 0, 0]
        : [2, 0, 0])
      if (justActivated) {
        nv.setRenderAzimuthElevation(0, 0)
      }
    })
  }, [clip?.enabled, clip?.depth, mode, sceneKey])

  useEffect(() => {
    const nv = nvRef.current
    if (
      !nv
      || handledResetTokenRef.current === resetToken
      || state.status !== 'ready'
      || loadedSceneKeyRef.current !== sceneKey
      || !nv.volumes?.[0]
    ) return
    handledResetTokenRef.current = resetToken
    lastFocusedObjectRef.current = ''
    if (mode === '3d') {
      nv.setRenderAzimuthElevation(
        clip?.enabled ? 0 : 120,
        clip?.enabled ? 0 : 15,
      )
      nv.setScale(1)
    } else {
      nv.setSliceType({
        axial: nv.sliceTypeAxial,
        coronal: nv.sliceTypeCoronal,
        sagittal: nv.sliceTypeSagittal,
        multiplanar: nv.sliceTypeMultiplanar,
      }[activePlane] ?? nv.sliceTypeMultiplanar)
      nv.setPan2Dxyzmm([0, 0, 0, 1])
    }
    const primaryVolume = registryRef.current.volumes.get(sources[0])
    const target = primaryVolume
      ? labelCentroidMM(primaryVolume, 1)
      : volumeCenterMM(nv.volumes[0])
    focusOnWorldPoint(nv, target, mode)
    nv.drawScene()
    publishNavigation(nv)
  }, [resetToken, sceneVersion, state.status, mode, sceneKey, clip?.enabled])

  return (
    <div className={`niivue-frame niivue-frame--${mode}${compact ? ' niivue-frame--compact' : ''}${guided ? ' niivue-frame--guided' : ''}`}>
      <canvas ref={canvasRef} aria-label={label} style={nativeGeometry && state.status !== 'ready' ? { visibility: 'hidden' } : undefined} />
      {mode === '2d' && (
        <div className={`viewer-plane-labels viewer-plane-labels--${activePlane}`} aria-label="CT anatomical planes">
          {(activePlane === 'multiplanar'
            ? ['axial', 'coronal', 'sagittal']
            : [activePlane]
          ).map((planeKey) => {
            const [plane, explanation] = PLANE_META[planeKey]
            return (
            <span key={plane}>
              <strong>{plane}</strong>
              <small>{explanation}</small>
            </span>
            )
          })}
        </div>
      )}
      {state.status === 'loading' && (
        <div className="viewer-state" role="status">
          <LoaderCircle size={16} className="spin" aria-hidden="true" />
          <span>{state.message}</span>
        </div>
      )}
      {state.status === 'error' && (
        <div className="viewer-state viewer-state--error" role="alert">
          <TriangleAlert size={16} aria-hidden="true" />
          <span>{state.message}</span>
        </div>
      )}
      {state.status === 'ready' && (
        <span className="viewer-ready" aria-label="Prepared result loaded">Evidence ready</span>
      )}
    </div>
  )
}
