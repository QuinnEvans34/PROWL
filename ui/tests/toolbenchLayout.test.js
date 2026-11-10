import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import {
  DEFAULT_TOOLBENCH_LAYOUT, TOOLBENCH_LAYOUT_KEY, readToolbenchLayout,
  sanitizeToolbenchLayout, saveToolbenchLayout, useToolbenchLayout,
} from '../src/lib/toolbenchLayout.js'

beforeEach(() => localStorage.clear())

describe('toolbench presentation preferences', () => {
  it('validates stored presentation values and clamps pane sizes', () => {
    expect(sanitizeToolbenchLayout({
      panelWidth: 9999, studyListWidth: 1, primaryShare: 4, secondaryShare: 90,
      panelOpen: 'false', studyListOpen: true, measurementsVisible: false, linked: false,
      hiddenPlanes: ['sagittal', 'unknown', 'sagittal'], maximizedPlane: 'coronal',
    })).toEqual({
      ...DEFAULT_TOOLBENCH_LAYOUT,
      panelWidth: 520, studyListWidth: 160, primaryShare: 40, secondaryShare: 75,
      studyListOpen: true, measurementsVisible: false, linked: false,
      hiddenPlanes: ['sagittal'], maximizedPlane: 'coronal',
    })
    expect(sanitizeToolbenchLayout({ panelWidth: NaN, primaryShare: Infinity, studyListWidth: '250' }))
      .toEqual(DEFAULT_TOOLBENCH_LAYOUT)
  })

  it('leaves a visible plane and never maximizes a hidden plane', () => {
    expect(sanitizeToolbenchLayout({ hiddenPlanes: ['axial', 'coronal', 'sagittal'] }).hiddenPlanes).toEqual([])
    expect(sanitizeToolbenchLayout({ hiddenPlanes: ['axial'], maximizedPlane: 'axial' }).maximizedPlane).toBeNull()
    expect(sanitizeToolbenchLayout({ maximizedPlane: 'unexpected' }).maximizedPlane).toBeNull()
  })

  it('only persists allowed layout preferences with a version', () => {
    saveToolbenchLayout({ ...DEFAULT_TOOLBENCH_LAYOUT, panelWidth: 400,
      studyId: 'study-secret', slice: 98, notes: 'clinical content', prediction: { volume: 91 } })
    const saved = JSON.parse(localStorage.getItem(TOOLBENCH_LAYOUT_KEY))
    expect(saved).toEqual({ version: 1, layout: { ...DEFAULT_TOOLBENCH_LAYOUT, panelWidth: 400 } })
    expect(readToolbenchLayout()).toEqual(saved.layout)
    expect(localStorage.getItem(TOOLBENCH_LAYOUT_KEY)).not.toContain('clinical')
  })

  it('uses safe defaults for corrupt, unsupported and denied storage', () => {
    localStorage.setItem(TOOLBENCH_LAYOUT_KEY, '{')
    expect(readToolbenchLayout()).toEqual(DEFAULT_TOOLBENCH_LAYOUT)
    localStorage.setItem(TOOLBENCH_LAYOUT_KEY, JSON.stringify({ version: 2, layout: { panelOpen: false } }))
    expect(readToolbenchLayout()).toEqual(DEFAULT_TOOLBENCH_LAYOUT)
    const denied = {
      getItem() { throw new Error('Storage denied') },
      setItem() { throw new Error('Quota exceeded') },
    }
    expect(readToolbenchLayout(denied)).toEqual(DEFAULT_TOOLBENCH_LAYOUT)
    expect(() => saveToolbenchLayout(DEFAULT_TOOLBENCH_LAYOUT, denied)).not.toThrow()
  })

  it('restores before the first render and preserves patches across updates', () => {
    saveToolbenchLayout({ ...DEFAULT_TOOLBENCH_LAYOUT, panelWidth: 444, studyListOpen: true })
    const { result, unmount } = renderHook(() => useToolbenchLayout())
    expect(result.current[0]).toMatchObject({ panelWidth: 444, studyListOpen: true })
    act(() => result.current[1]({ panelOpen: false }))
    act(() => result.current[1](current => ({ primaryShare: current.primaryShare + 8 })))
    expect(result.current[0]).toMatchObject({ panelWidth: 444, studyListOpen: true, panelOpen: false, primaryShare: 72 })
    unmount()
    const restored = renderHook(() => useToolbenchLayout())
    expect(restored.result.current[0]).toMatchObject({ panelWidth: 444, panelOpen: false, primaryShare: 72 })
    act(() => restored.result.current[2]())
    expect(restored.result.current[0]).toEqual(DEFAULT_TOOLBENCH_LAYOUT)
    expect(readToolbenchLayout()).toEqual(DEFAULT_TOOLBENCH_LAYOUT)
  })
})
