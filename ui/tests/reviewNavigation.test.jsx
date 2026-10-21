import React, { useState } from 'react'
import { afterEach, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { hrefFor, parseLocation, useRoute } from '../src/lib/router.js'
import AppShell from '../src/shell/AppShell.jsx'
const hash = 'a'.repeat(64)
afterEach(() => window.history.replaceState(null, '', '/'))
it('round-trips a saved prediction identity without allowing arbitrary paths', () => {
  expect(hrefFor({view:'saved',review:hash})).toBe(`/saved?review=${hash}`)
  expect(parseLocation({pathname:'/saved',search:`?review=${hash}`}).review).toBe(hash)
  expect(parseLocation({pathname:'/saved',search:'?review=../secret'}).review).toBeNull()
  expect(hrefFor({view:'saved',review:'../secret'})).toBe('/saved')
  expect(parseLocation({pathname:'/research',search:`?review=${hash}`}).review).toBeNull()
})
function Shell() {
  const [dirty,setDirty]=useState(true)
  const [route,navigate]=useRoute({guard:()=> !dirty || window.confirm('Discard unsaved review?')})
  return <AppShell route={route} navigate={navigate} endpointStatus="offline">
    <p data-testid="route">{route.view}:{route.review}</p>
    <button onClick={()=>setDirty(false)}>Simulate durable save</button>
  </AppShell>
}
it('exposes Analyze and Saved reviews, keeps the current review when navigation is declined',()=>{
  window.history.replaceState(null,'',`/saved?review=${hash}`)
  vi.stubGlobal('confirm',vi.fn().mockReturnValue(false))
  render(<Shell />)
  expect(screen.getByRole('link',{name:'Saved reviews'}).getAttribute('aria-current')).toBe('page')
  fireEvent.click(screen.getByRole('link',{name:'Analyze'}))
  expect(window.location.pathname).toBe('/saved')
  expect(screen.getByTestId('route').textContent).toBe(`saved:${hash}`)
  fireEvent.click(screen.getByText('Simulate durable save'))
  fireEvent.click(screen.getByRole('link',{name:'Analyze'}))
  expect(window.location.pathname).toBe('/predict')
  expect(screen.getByTestId('route').textContent).toBe('predict:')
  expect(confirm).toHaveBeenCalledTimes(1)
})
it('restores the exact saved target when a back/forward navigation is declined',()=>{
  window.history.replaceState(null,'',`/saved?review=${hash}`)
  vi.stubGlobal('confirm',vi.fn().mockReturnValue(false))
  render(<Shell />)
  act(()=>{window.history.replaceState(null,'','/research');window.dispatchEvent(new PopStateEvent('popstate'))})
  expect(window.location.pathname+window.location.search).toBe(`/saved?review=${hash}`)
  expect(screen.getByTestId('route').textContent).toBe(`saved:${hash}`)
})
