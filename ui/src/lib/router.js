import { useCallback, useEffect, useRef, useState } from 'react'

// Minimal history-backed routing for the PROWL shell. No router dependency:
// existing deep links (/research, /saved) keep working, and the active study
// lives in the URL (?study=) so back/forward and reload restore it.
export const VIEWS = ['studies', 'workbench', 'research', 'saved', 'predict']

export function parseLocation(location = window.location) {
  const path = location.pathname.replace(/\/+$/, '') || '/'
  const params = new URLSearchParams(location.search)
  const view = path === '/research' ? 'research'
    : path === '/predict' ? 'predict'
    : path === '/saved' ? 'saved'
      : path === '/workbench' ? 'workbench'
        : 'studies'
  const study = params.get('study')
  const review = params.get('review')
  return {
    view,
    review: view === 'saved' && /^[a-f0-9]{64}$/.test(review || '') ? review : null,
    study: study && /^[A-Za-z0-9_-]{1,80}$/.test(study) ? study : null,
    layout: params.get('layout') === 'compare' ? 'compare' : null,
  }
}

export function hrefFor({ view = 'studies', study = null, layout = null, review = null } = {}) {
  const path = view === 'studies' ? '/' : `/${view}`
  const params = new URLSearchParams()
  if (study && view === 'workbench') params.set('study', study)
  if (layout && view === 'workbench') params.set('layout', layout)
  if (view === 'saved' && /^[a-f0-9]{64}$/.test(review || '')) params.set('review', review)
  const query = params.toString()
  return query ? `${path}?${query}` : path
}

// `guard` may return false to block an in-app navigation (e.g. unsaved draft).
// Browser back/forward cannot be cancelled synchronously; the caller receives
// the change and can restore the previous entry if its guard declines.
export function useRoute({ guard } = {}) {
  const [route, setRoute] = useState(() => parseLocation())
  const guardRef = useRef(guard)
  guardRef.current = guard
  const routeRef = useRef(route)
  routeRef.current = route

  useEffect(() => {
    function onPop() {
      const next = parseLocation()
      if (guardRef.current && guardRef.current(next, { popstate: true }) === false) {
        window.history.pushState(null, '', hrefFor(routeRef.current))
        return
      }
      setRoute(next)
    }
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  const navigate = useCallback((to, { replace = false } = {}) => {
    const next = { ...routeRef.current, layout: null, review: null, ...to }
    if (guardRef.current && guardRef.current(next, { popstate: false }) === false) return false
    const href = hrefFor(next)
    if (href !== window.location.pathname + window.location.search) {
      window.history[replace ? 'replaceState' : 'pushState'](null, '', href)
    }
    setRoute(parseLocation())
    return true
  }, [])

  return [route, navigate]
}
