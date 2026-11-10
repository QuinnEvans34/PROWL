import React, { useEffect, useRef } from 'react'
import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useWorkspaceDisplay } from '../src/components/useWorkspaceDisplay.js'

let display
function MountedViewer({ mounted }) {
  useEffect(() => { mounted() }, [mounted])
  return <input aria-label="Slice position" defaultValue="45" />
}
function Workspace({ mounted = () => {} }) {
  const ref = useRef(null)
  display = useWorkspaceDisplay(ref)
  return <section ref={ref} data-testid="workspace" data-focus={display.focusMode}>
    <MountedViewer mounted={mounted} />
    <button onClick={display.toggleFocus}>Focus</button>
    <button onClick={display.toggleFullscreen}>Full screen</button>
    <output aria-label="Fullscreen error">{display.fullscreenError}</output>
  </section>
}

afterEach(() => {
  delete document.fullscreenElement
  delete document.exitFullscreen
  delete document.fullscreenEnabled
  delete document.webkitFullscreenElement
  delete document.webkitExitFullscreen
  delete document.webkitFullscreenEnabled
})

describe('workspace focus and browser full screen', () => {
  it('keeps mounted viewers and their current slice while focus changes', () => {
    const mounted = vi.fn()
    render(<Workspace mounted={mounted} />)
    const slice = screen.getByLabelText('Slice position')
    fireEvent.change(slice, { target: { value: '92' } })
    fireEvent.click(screen.getByText('Focus'))
    expect(display.focusMode).toBe(true)
    expect(screen.getByLabelText('Slice position')).toBe(slice)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(display.focusMode).toBe(false)
    expect(slice.value).toBe('92')
    expect(mounted).toHaveBeenCalledTimes(1)
  })

  it('explains unavailable or denied full screen without substituting workspace focus', async () => {
    render(<Workspace />)
    await act(async () => { await display.toggleFullscreen() })
    expect(display.focusMode).toBe(false)
    expect(display.isFullscreen).toBe(false)
    expect(screen.getByLabelText('Fullscreen error').textContent).toContain('cannot use display full screen')
    const workspace = screen.getByTestId('workspace')
    workspace.requestFullscreen = vi.fn().mockRejectedValue(new Error('Permission denied'))
    document.exitFullscreen = vi.fn()
    await act(async () => { await display.toggleFullscreen() })
    expect(display.focusMode).toBe(false)
    expect(screen.getByLabelText('Fullscreen error').textContent).toContain('could not open')
  })

  it('consumes Escape only when exiting a display mode so selection survives focus', () => {
    render(<Workspace />)
    const selectionEscape = vi.fn()
    window.addEventListener('keydown', selectionEscape)
    try {
      fireEvent.keyDown(document, { key: 'Escape' })
      expect(selectionEscape).toHaveBeenCalledTimes(1)
      fireEvent.click(screen.getByText('Focus'))
      fireEvent.keyDown(document, { key: 'Escape' })
      expect(display.focusMode).toBe(false)
      expect(selectionEscape).toHaveBeenCalledTimes(1)
      fireEvent.keyDown(document, { key: 'Escape' })
      expect(selectionEscape).toHaveBeenCalledTimes(2)
    } finally {
      window.removeEventListener('keydown', selectionEscape)
    }
  })

  it('tracks native full screen and exits owned full screen with Escape', async () => {
    const mounted = vi.fn()
    render(<Workspace mounted={mounted} />)
    const workspace = screen.getByTestId('workspace')
    workspace.requestFullscreen = vi.fn(async () => {
      Object.defineProperty(document, 'fullscreenElement', { value: workspace, configurable: true })
      document.dispatchEvent(new Event('fullscreenchange'))
    })
    document.exitFullscreen = vi.fn(async () => {
      Object.defineProperty(document, 'fullscreenElement', { value: null, configurable: true })
      document.dispatchEvent(new Event('fullscreenchange'))
    })
    await act(async () => { await display.toggleFullscreen() })
    expect(display.isFullscreen).toBe(true)
    expect(workspace.requestFullscreen).toHaveBeenCalledWith({ navigationUI: 'hide' })
    fireEvent.click(screen.getByText('Focus'))
    await act(async () => { fireEvent.keyDown(document, { key: 'Escape' }) })
    expect(document.exitFullscreen).toHaveBeenCalledTimes(1)
    expect(display.isFullscreen).toBe(false)
    expect(display.focusMode).toBe(false)
    expect(mounted).toHaveBeenCalledTimes(1)
  })

  it('supports Safari prefixed full screen while preserving an existing focus layout', async () => {
    render(<Workspace />)
    const workspace = screen.getByTestId('workspace')
    workspace.webkitRequestFullscreen = vi.fn(() => {
      Object.defineProperty(document, 'webkitFullscreenElement', { value: workspace, configurable: true })
      document.dispatchEvent(new Event('webkitfullscreenchange'))
    })
    document.webkitExitFullscreen = vi.fn(() => {
      Object.defineProperty(document, 'webkitFullscreenElement', { value: null, configurable: true })
      document.dispatchEvent(new Event('webkitfullscreenchange'))
    })
    fireEvent.click(screen.getByText('Focus'))
    await act(async () => { await display.toggleFullscreen() })
    expect(display.isFullscreen).toBe(true)
    expect(display.focusMode).toBe(true)
    await act(async () => { await display.toggleFullscreen() })
    expect(display.isFullscreen).toBe(false)
    expect(display.focusMode).toBe(true)
    expect(document.webkitExitFullscreen).toHaveBeenCalledTimes(1)
  })

  it('does not exit another element full screen and removes listeners on unmount', () => {
    const { unmount } = render(<Workspace />)
    document.exitFullscreen = vi.fn()
    Object.defineProperty(document, 'fullscreenElement', { value: document.body, configurable: true })
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(document.exitFullscreen).not.toHaveBeenCalled()
    const removeListener = vi.spyOn(document, 'removeEventListener')
    unmount()
    expect(removeListener).toHaveBeenCalledWith('fullscreenchange', expect.any(Function))
    expect(removeListener).toHaveBeenCalledWith('keydown', expect.any(Function))
    removeListener.mockRestore()
  })
})
