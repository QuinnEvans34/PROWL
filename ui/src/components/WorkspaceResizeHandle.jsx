import { useEffect, useRef } from 'react'

// Layout only: mouse, touch and keyboard resizing never touches the image state.
export default function WorkspaceResizeHandle({ label, value, min, max, direction = 1, onChange, className = '' }) {
  const drag = useRef(null)
  const change = useRef(onChange)
  change.current = onChange
  const clamp = next => Math.round(Math.max(min, Math.min(max, next)))
  useEffect(() => {
    function move(event) {
      if (drag.current) change.current(clamp(drag.current.value + direction * (event.clientX - drag.current.x)))
    }
    function end() { drag.current = null }
    window.addEventListener('pointermove', move)
    window.addEventListener('pointerup', end)
    window.addEventListener('pointercancel', end)
    return () => {
      window.removeEventListener('pointermove', move)
      window.removeEventListener('pointerup', end)
      window.removeEventListener('pointercancel', end)
    }
  }, [min, max, direction])
  return <div className={`pw-workspace-resize ${className}`} role="separator" tabIndex={0}
    aria-label={label} aria-orientation="vertical" aria-valuemin={min} aria-valuemax={max} aria-valuenow={value}
    onPointerDown={event => {
      if (event.button !== 0) return
      event.preventDefault()
      drag.current = { x: event.clientX, value }
      event.currentTarget.focus()
    }}
    onKeyDown={event => {
      const delta = event.shiftKey ? 40 : 10
      let next
      if (event.key === 'ArrowLeft') next = value - direction * delta
      if (event.key === 'ArrowRight') next = value + direction * delta
      if (event.key === 'Home') next = min
      if (event.key === 'End') next = max
      if (next !== undefined) { event.preventDefault(); event.stopPropagation(); onChange(clamp(next)) }
    }}><span aria-hidden="true" /></div>
}
