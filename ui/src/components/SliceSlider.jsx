import { useEffect, useRef } from 'react'

export default function SliceSlider(props) {
  const inputRef = useRef(null)

  useEffect(() => {
    const input = inputRef.current
    const blockWheel = event => event.preventDefault()
    // React registers wheel listeners as passive. Cancel the range's native
    // wheel action without affecting dragging or keyboard navigation.
    input.addEventListener('wheel', blockWheel, { capture: true, passive: false })
    return () => input.removeEventListener('wheel', blockWheel, true)
  }, [])

  return <input {...props} ref={inputRef} type="range" />
}
