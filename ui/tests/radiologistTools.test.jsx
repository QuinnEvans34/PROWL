import React from 'react'
import { it, expect, describe } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import {
  anatomyColormap, anatomyMeshLayers, normalizeInsights, structuredSummaryText, DISTANCE_BANDS,
} from '../src/lib/studyInsights.js'
import { LesionCharacteristics, VesselRelationship, StructuredSummary } from '../src/components/FindingsInsights.jsx'
import CurvedView from '../src/components/CurvedView.jsx'

const raw = {
  schema: 'prowl.workbench.insights.v1',
  case_id: 'PanTS_00009005',
  lesion: {
    present: true, long_axis_mm: 36.1, short_axis_mm: 29.4, slice: 37, volume_ml: 15.58, location: 'body',
    location_share_pct: { head: 1, body: 88, tail: 10 }, lesion_mean_hu: 58, parenchyma_mean_hu: 93,
    attenuation_delta_hu: -35, attenuation: 'hypoattenuating',
  },
  anatomy: [
    { name: 'pancreatic_duct', label: 'Pancreatic duct', kind: 'duct', max_calibre_mm: 6.2, upper_normal_mm: 3, dilated: true },
    { name: 'celiac_artery', label: 'Celiac artery', kind: 'artery', min_distance_mm: 0, contact_angle_deg: 228, contact_category: 'encasement' },
    { name: 'superior_mesenteric_artery', label: 'SMA', kind: 'artery', min_distance_mm: 11.5, contact_angle_deg: 0, contact_category: 'none' },
  ],
  cpr: {
    length_mm: 130.5, width_mm: 60, pixels: [523, 241], lesion_span_mm: [40.5, 73.5],
    method: 'Straightened reformat along the smoothed skeleton of the predicted pancreas',
  },
}
const insights = normalizeInsights(raw)

describe('studyInsights', () => {
  it('rejects unknown schemas and orders anatomy by the shared palette', () => {
    expect(normalizeInsights({ schema: 'other' })).toBeNull()
    expect(insights.anatomy.map(item => item.name)).toEqual(['superior_mesenteric_artery', 'celiac_artery', 'pancreatic_duct'])
  })

  it('builds a label colormap whose indices match the exported anatomy volume', () => {
    const cmap = anatomyColormap(200)
    expect(cmap.I).toEqual([0, 1, 2, 3, 4, 5, 6, 7])
    expect(cmap.A[0]).toBe(0)
    expect(cmap.A.slice(1).every(alpha => alpha === 200)).toBe(true)
  })

  it('splits vessels into distance bands but keeps ducts in their identity colour', () => {
    const { banded, layers } = anatomyMeshLayers({
      anatomy_celiac_artery__contact: 'a.obj', anatomy_celiac_artery__far: 'b.obj',
      anatomy_celiac_artery: 'whole.obj', anatomy_pancreatic_duct: 'duct.obj',
    })
    expect(banded).toBe(true)
    expect(layers.map(layer => layer.key)).toEqual(['anatomy_celiac_artery__contact', 'anatomy_celiac_artery__far', 'anatomy_pancreatic_duct'])
    expect(layers[0].color).toEqual(DISTANCE_BANDS.find(band => band.key === 'contact').color)
  })

  it('uses whole vessel meshes when no lesion banding exists', () => {
    const { banded, layers } = anatomyMeshLayers({ anatomy_aorta: 'aorta.obj' })
    expect(banded).toBe(false)
    expect(layers).toHaveLength(1)
  })

  it('writes a structured draft that is explicit about its limits', () => {
    const text = structuredSummaryText(insights, { studyLabel: 'PanTS 00009005' })
    expect(text).toContain('Draft for radiologist review')
    expect(text).toContain('not a diagnosis')
    expect(text).toContain('3.6 cm × 2.9 cm')
    expect(text).toContain('Celiac artery: encasement, 228°')
    expect(text).toContain('Pancreatic duct: 6.2 mm (dilated)')
    expect(text).not.toMatch(/resectab/i)
  })

  it('does not assess vessels without a predicted lesion', () => {
    const text = structuredSummaryText({ ...insights, lesion: { present: false } })
    expect(text).toContain('No lesion outlined by the model.')
    expect(text).toContain('Not applicable without a predicted lesion.')
  })
})

describe('findings insight cards', () => {
  it('shows lesion characteristics from the model outline', () => {
    render(<LesionCharacteristics insights={insights} />)
    const card = screen.getByRole('region', { name: 'Lesion characteristics' })
    expect(within(card).getByText('3.6 × 2.9 cm')).toBeTruthy()
    expect(within(card).getByText(/From the model outline/)).toBeTruthy()
  })

  it('labels vessel relationships as a review aid against reference anatomy', () => {
    render(<VesselRelationship insights={insights} />)
    const card = screen.getByRole('region', { name: 'Vessel relationship' })
    expect(within(card).getByText(/reference anatomy · for review/)).toBeTruthy()
    expect(within(card).getByText('Celiac artery').closest('tr').className).toContain('is-encasement')
  })

  it('renders nothing for lesion characteristics when no lesion is predicted', () => {
    const { container } = render(<LesionCharacteristics insights={{ ...insights, lesion: { present: false } }} />)
    expect(container.innerHTML).toBe('')
  })

  it('offers the structured draft as copyable text', () => {
    render(<StructuredSummary insights={insights} studyLabel="PanTS 00009005" />)
    expect(screen.getByRole('button', { name: /Copy summary/ })).toBeTruthy()
  })
})

describe('curved view', () => {
  const caseData = { files: { cpr: { ct: 'c/cpr_ct.png', prediction: 'c/cpr_prediction.png', reference: 'c/cpr_reference.png', anatomy: 'c/cpr_anatomy.png' } } }

  it('explains when a study has no curved view', () => {
    render(<CurvedView caseData={{ files: {} }} insights={insights} />)
    expect(screen.getByText(/not available for this study/)).toBeTruthy()
  })

  it('stacks only the requested layers and marks the lesion span', () => {
    const { container } = render(<CurvedView caseData={caseData} insights={insights} showPrediction showReference={false} showAnatomy={false} />)
    const sources = [...container.querySelectorAll('img')].map(img => img.getAttribute('src'))
    expect(sources).toEqual(['/cases/c/cpr_ct.png', '/cases/c/cpr_prediction.png'])
    expect(container.querySelector('.pw-curved__span').getAttribute('title')).toContain('41–74 mm')
    expect(screen.getByText(/not the model/)).toBeTruthy()
  })
})

it('shows only duct calibres when no lesion is predicted', () => {
  const none = { ...insights, lesion: { present: false } }
  render(<VesselRelationship insights={none} />)
  const card = screen.getByRole('region', { name: 'Vessel relationship' })
  expect(within(card).queryByText('Celiac artery')).toBeNull()
  expect(within(card).getByText('Pancreatic duct')).toBeTruthy()
  expect(within(card).getByText(/contact is not assessed/)).toBeTruthy()
})

describe('region CT for native studies', () => {
  it('uses the pancreas-box crop for the 3D region scene only', async () => {
    const { preparedViewerCtPath } = await import('../src/lib/viewerSceneKey.js')
    const caseData = { files: { ct: 'c/ct.nii.gz', ct_region: 'c/ct_region.nii.gz', ct_full: 'c/ct_full.nii.gz', ct_full_native: 'c/ct_full_native.nii.gz' } }
    expect(preparedViewerCtPath({ caseData, mode: '3d', showFull: false })).toBe('c/ct_region.nii.gz')
    expect(preparedViewerCtPath({ caseData, mode: '2d', showFull: false })).toBe('c/ct.nii.gz')
    expect(preparedViewerCtPath({ caseData, mode: '3d', showFull: true })).toBe('c/ct_full_native.nii.gz')
    expect(preparedViewerCtPath({ caseData: { files: { ct: 'c/ct.nii.gz' } }, mode: '3d' })).toBe('c/ct.nii.gz')
  })
})
