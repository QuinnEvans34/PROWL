import { useCallback, useEffect, useRef, useState } from 'react'
import { Niivue, SLICE_TYPE } from '@niivue/niivue'
import { ChevronDown, ChevronUp, Download, Eraser, Paintbrush, RotateCcw, Undo2 } from 'lucide-react'

const BASE = '/cases'
// Passed to setDrawColormap as an object: NiiVue's draw LUT only resolves built-in
// colormap names, so a registered custom name silently falls back to an invisible LUT.
const DRAW_COLORMAP = { R: [0, 38, 249], G: [0, 197, 99], B: [0, 166, 99], A: [0, 255, 255], I: [0, 1, 2], labels: ['', 'Pancreas', 'Lesion'] }
const TOOLS = [
  { key: 'lesion', label: 'Paint lesion', pen: 2, color: '#f96363', icon: Paintbrush },
  { key: 'pancreas', label: 'Paint pancreas', pen: 1, color: '#26c5a6', icon: Paintbrush },
  { key: 'erase', label: 'Erase', pen: 0, color: '#94a3b8', icon: Eraser },
]

function countLabels(nv) {
  const bitmap = nv?.drawBitmap
  if (!bitmap) return { pancreas: 0, lesion: 0 }
  let pancreas = 0
  let lesion = 0
  for (let i = 0; i < bitmap.length; i += 1) {
    if (bitmap[i] === 1) pancreas += 1
    else if (bitmap[i] === 2) lesion += 1
  }
  return { pancreas, lesion }
}

function voxelMl(nv) {
  const dims = nv?.volumes?.[0]?.hdr?.pixDims
  return dims ? Math.abs(dims[1] * dims[2] * dims[3]) / 1000 : null
}

// Correct the saved prediction on axial slices. Edits stay in this browser tab until
// exported; the saved prediction file is never modified.
export default function OutlineEditor({ caseData, startSlice = null, onClose }) {
  const canvasRef = useRef(null)
  const nvRef = useRef(null)
  const baselineRef = useRef(null)
  const [status, setStatus] = useState('loading')
  const [tool, setTool] = useState('lesion')
  const [brush, setBrush] = useState(3)
  const [counts, setCounts] = useState({ pancreas: 0, lesion: 0 })
  const ctUrl = `${BASE}/${caseData.files.ct}`
  const predUrl = `${BASE}/${caseData.files.pred}`

  const refreshCounts = useCallback(() => setCounts(countLabels(nvRef.current)), [])

  const loadPrediction = useCallback(async () => {
    const nv = nvRef.current
    if (!nv) return
    await nv.loadDrawingFromUrl(predUrl, false)
    nv.setDrawColormap(DRAW_COLORMAP)
    nv.drawClearAllUndoBitmaps?.()
    baselineRef.current = countLabels(nv)
    refreshCounts()
    nv.drawScene()
  }, [predUrl, refreshCounts])

  useEffect(() => {
    let cancelled = false
    const nv = new Niivue({ backColor: [0.024, 0.026, 0.029, 1], isColorbar: false, show3Dcrosshair: false, crosshairWidth: 0 })
    nvRef.current = nv
    nv.attachToCanvas(canvasRef.current)
    ;(async () => {
      try {
        await nv.loadVolumes([{ url: ctUrl, colormap: 'gray', cal_min: 0.1, cal_max: 0.65, trustCalMinMax: true }])
        if (cancelled) return
        nv.setSliceType(SLICE_TYPE.AXIAL)
        nv.setDrawingEnabled(true)
        nv.setDrawOpacity(0.55)
        nv.opts.penSize = 3
        nv.setPenValue(2, false)
        await loadPrediction()
        if (cancelled) return
        const dims = nv.volumes[0]?.hdr?.dims
        if (Number.isFinite(startSlice) && dims?.[3] > 1) {
          nv.scene.crosshairPos = new Float32Array([0.5, 0.5, (startSlice + 0.5) / dims[3]])
        }
        nv.drawScene()
        setStatus('ready')
      } catch (error) {
        if (!cancelled) setStatus(`error:${error instanceof Error ? error.message : 'load failed'}`)
      }
    })()
    const canvas = canvasRef.current
    const recount = () => setTimeout(() => setCounts(countLabels(nvRef.current)), 0)
    canvas.addEventListener('pointerup', recount)
    return () => {
      cancelled = true
      canvas.removeEventListener('pointerup', recount)
      nvRef.current = null
    }
  }, [ctUrl, loadPrediction, startSlice])

  useEffect(() => {
    const nv = nvRef.current
    if (!nv || status !== 'ready') return
    const selected = TOOLS.find(item => item.key === tool)
    nv.setPenValue(selected.pen, false)
    nv.opts.penSize = brush
  }, [tool, brush, status])

  const ml = voxelMl(nvRef.current)
  const baseline = baselineRef.current
  const delta = (key) => (baseline && ml ? (counts[key] - baseline[key]) * ml : 0)
  const volume = (key) => (ml ? (counts[key] * ml).toFixed(2) : '—')
  const signed = value => `${value > 0 ? '+' : value < 0 ? '−' : '±'}${Math.abs(value).toFixed(2)}`

  return (
    <div className="pw-editor" role="region" aria-label="Edit outline">
      <div className="pw-editor__tools" role="toolbar" aria-label="Outline editing tools">
        {TOOLS.map(item => {
          const Icon = item.icon
          return <button key={item.key} type="button" className="pw-editor__tool" aria-pressed={tool === item.key}
            onClick={() => setTool(item.key)}>
            <Icon size={14} aria-hidden="true" style={{ color: item.color }} /> {item.label}
          </button>
        })}
        <label className="pw-editor__brush">
          <span>Brush <output>{brush}</output></span>
          <input type="range" min="1" max="12" value={brush} onChange={event => setBrush(Number(event.target.value))} aria-label="Brush size in voxels" />
        </label>
        <span className="pw-toolbar__spacer" />
        <button type="button" className="pw-icon-btn" aria-label="Previous slice" title="Previous slice"
          onClick={() => { nvRef.current?.moveCrosshairInVox(0, 0, -1); nvRef.current?.drawScene() }}><ChevronDown size={15} /></button>
        <button type="button" className="pw-icon-btn" aria-label="Next slice" title="Next slice"
          onClick={() => { nvRef.current?.moveCrosshairInVox(0, 0, 1); nvRef.current?.drawScene() }}><ChevronUp size={15} /></button>
        <button type="button" className="pw-btn pw-btn--sm pw-btn--ghost" onClick={() => { nvRef.current?.drawUndo(); refreshCounts() }}>
          <Undo2 size={13} aria-hidden="true" /> Undo</button>
        <button type="button" className="pw-btn pw-btn--sm pw-btn--ghost" onClick={loadPrediction}>
          <RotateCcw size={13} aria-hidden="true" /> Reset to saved</button>
        <button type="button" className="pw-btn pw-btn--sm pw-btn--secondary" disabled={status !== 'ready'}
          onClick={() => nvRef.current?.saveImage({ filename: `${caseData.case_id || 'study'}-edited-outline.nii.gz`, isSaveDrawing: true, volumeByIndex: 0 })}>
          <Download size={13} aria-hidden="true" /> Export edited mask</button>
        {onClose && <button type="button" className="pw-btn pw-btn--sm pw-btn--primary" onClick={onClose}>Done</button>}
      </div>
      <div className="pw-editor__body">
        <canvas ref={canvasRef} className="pw-editor__canvas" aria-label="Axial CT with editable outline" />
        {status === 'loading' && <p className="pw-editor__status" role="status">Loading CT and saved outline…</p>}
        {status.startsWith('error') && <p className="pw-editor__status" role="alert">The editor could not load this study ({status.slice(6)}).</p>}
      </div>
      <dl className="pw-editor__readout" aria-label="Edited outline volumes">
        <div><dt><i style={{ background: '#f96363' }} />Lesion</dt><dd className="pw-num">{volume('lesion')} mL <small>{signed(delta('lesion'))} mL vs saved</small></dd></div>
        <div><dt><i style={{ background: '#26c5a6' }} />Pancreas (excl. lesion)</dt><dd className="pw-num">{volume('pancreas')} mL <small>{signed(delta('pancreas'))} mL vs saved</small></dd></div>
        <p>Drag to paint on the axial slice · scroll to change slice. Edits stay in this tab until exported; the saved prediction is unchanged.</p>
      </dl>
    </div>
  )
}
