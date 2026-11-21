import { useEffect, useRef, useState } from 'react'
import { ChevronUp, Eye, EyeOff } from 'lucide-react'
import { ANATOMY_STRUCTURES, contactCategoryLabel, rgb } from '../lib/studyInsights.js'

const mm = value => Number.isFinite(value) ? `${value < 10 ? value.toFixed(1) : Math.round(value)} mm` : null

// One-line context for a structure: contact with the predicted lesion for vessels,
// calibre for ducts. Reference anatomy against the model lesion; for review only.
function structureDetail(item, lesionPresent) {
  if (item.annotated === false) return 'Not annotated'
  if (item.kind === 'duct') {
    return Number.isFinite(item.max_calibre_mm) ? `${mm(item.max_calibre_mm)}${item.dilated ? ' · dilated' : ''}` : null
  }
  if (!lesionPresent) return null
  if (item.contact_category && item.contact_category !== 'none') {
    return `${contactCategoryLabel(item.contact_category)} · ${Math.round(item.contact_angle_deg)}°`
  }
  return Number.isFinite(item.min_distance_mm) ? `${mm(item.min_distance_mm)} from lesion` : null
}

// Layer-bar menu for the reference anatomy: names every structure, toggles each one,
// and highlights a structure in 2D and 3D (hover previews, click pins).
export default function AnatomyStructuresMenu({ insights, hidden = [], highlight = null, disabled = false, onHiddenChange, onHighlightChange }) {
  const [open, setOpen] = useState(false)
  const [pinned, setPinned] = useState(null)
  const rootRef = useRef(null)
  const lesionPresent = Boolean(insights?.lesion?.present)
  const listed = new Map((insights?.anatomy || []).map(item => [item.name, item]))
  const structures = ANATOMY_STRUCTURES.filter(item => listed.has(item.name) && listed.get(item.name).annotated !== false)

  useEffect(() => {
    if (!open) return undefined
    const close = event => { if (!rootRef.current?.contains(event.target)) setOpen(false) }
    const escape = event => { if (event.key === 'Escape') setOpen(false) }
    document.addEventListener('pointerdown', close)
    document.addEventListener('keydown', escape)
    return () => { document.removeEventListener('pointerdown', close); document.removeEventListener('keydown', escape) }
  }, [open])
  useEffect(() => { if (!open) onHighlightChange?.(pinned) }, [open, pinned]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!structures.length) return null
  const toggleHidden = name => onHiddenChange?.(hidden.includes(name) ? hidden.filter(item => item !== name) : [...hidden, name])
  const togglePin = name => {
    const next = pinned === name ? null : name
    setPinned(next)
    onHighlightChange?.(next)
  }
  const changed = hidden.length > 0 || pinned
  return (
    <span className="pw-anatomy-menu" ref={rootRef}>
      <button type="button" className={`pw-anatomy-menu__toggle${open ? ' is-open' : ''}${pinned ? ' is-pinned' : ''}`}
        aria-haspopup="dialog" aria-expanded={open} disabled={disabled}
        onClick={() => setOpen(value => !value)} aria-label="Anatomy structures" title="Name, show or highlight each structure">
        <ChevronUp size={14} aria-hidden="true" />
      </button>
      {open && (
        <div className="pw-anatomy-menu__panel" role="dialog" aria-label="Reference anatomy structures"
          onMouseLeave={() => onHighlightChange?.(pinned)}>
          <header>
            <strong>Reference anatomy</strong>
            <small>Dataset annotation · hover to preview, click a name to highlight</small>
          </header>
          <ul>
            {structures.map(structure => {
              const info = listed.get(structure.name)
              const isHidden = hidden.includes(structure.name)
              const detail = structureDetail({ ...info, kind: structure.kind }, lesionPresent)
              const contact = info.contact_category && info.contact_category !== 'none' && lesionPresent
              return (
                <li key={structure.name} className={`${isHidden ? 'is-hidden' : ''}${highlight === structure.name ? ' is-highlighted' : ''}`}
                  onMouseEnter={() => !isHidden && onHighlightChange?.(structure.name)}>
                  <button type="button" className="pw-anatomy-menu__eye" aria-pressed={!isHidden}
                    aria-label={`${isHidden ? 'Show' : 'Hide'} ${structure.longLabel || structure.label}`}
                    onClick={() => toggleHidden(structure.name)}>
                    {isHidden ? <EyeOff size={14} aria-hidden="true" /> : <Eye size={14} aria-hidden="true" />}
                  </button>
                  <button type="button" className="pw-anatomy-menu__name" aria-pressed={pinned === structure.name}
                    disabled={isHidden} onClick={() => togglePin(structure.name)}>
                    <i style={{ background: rgb(structure.color) }} aria-hidden="true" />
                    <span>{structure.longLabel || structure.label}</span>
                    {detail && <small className={contact ? 'is-contact' : ''}>{detail}</small>}
                  </button>
                </li>
              )
            })}
          </ul>
          {changed && (
            <button type="button" className="pw-btn pw-btn--link pw-anatomy-menu__reset"
              onClick={() => { onHiddenChange?.([]); setPinned(null); onHighlightChange?.(null) }}>Show all · clear highlight</button>
          )}
        </div>
      )}
    </span>
  )
}
