import { beforeEach, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../src/App.jsx'
import { hrefFor } from '../src/lib/router.js'
import { loadSavedPrediction } from '../src/lib/savedPrediction.js'
import { disposePrediction, predictStudy, predictionCatalog } from '../src/lib/onDemandPrediction.js'

vi.mock('../src/lib/onDemandPrediction.js', async importOriginal => ({
  ...await importOriginal(), disposePrediction: vi.fn(), predictStudy: vi.fn(), predictionCatalog: vi.fn(),
}))
vi.mock('../src/lib/savedPrediction.js', () => ({ loadSavedPrediction: vi.fn() }))
vi.mock('../src/components/ReviewWorkspace.jsx', () => ({ default: ({
  caseData, verifiedPrediction, predictionJob, onReviewDirty,
}) => <section aria-label="Rendered workspace">
  <p>{verifiedPrediction ? `Verified image ${verifiedPrediction.urls.ct} and ${verifiedPrediction.urls.pred}` : 'Legacy prepared study'}</p>
  {verifiedPrediction && <>
    <p>{predictionJob.base}</p>
    <p>{verifiedPrediction.measurement.pancreasMl} mL</p>
    <p>{Object.keys(caseData.files).join(' ')}</p>
    <button type="button" onClick={() => onReviewDirty(true)}>Edit verified draft</button>
  </>}
</section> }))
vi.mock('../src/components/SavedReviewList.jsx', () => ({ default: () => null }))
vi.mock('../src/components/LiteratureSearchPanel.jsx', () => ({ default: () => null }))

const job = { case_id: 'SYNTHETIC_A', job_id: 'a'.repeat(32), request_identity: 'b'.repeat(64), status: 'ready' }
const jobBase = `/scan-inference/jobs/${job.job_id}/files`
const route = (study = job.case_id) => hrefFor({ view: 'workbench', study, run: job.job_id })
const release = vi.fn()
const loaded = {
  manifest: {
    case_id: job.case_id, prediction_mode: 'pancreas_assisted', model_sha256: { segmenter: 'e'.repeat(64) },
    files: { ct: { uri: 'ct.nii.gz' }, pred: { uri: 'prediction.nii.gz' } },
    geometry: { affine: [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 2, 0], [0, 0, 0, 1]] },
  },
  manifestHash: 'c'.repeat(64),
  urls: { ct: 'blob:verified-original-ct', pred: 'blob:verified-current-mask' },
  measurement: { status: 'ready', pancreasMl: 12.5, lesionVoxels: 1 },
  release,
}

beforeEach(() => {
  window.history.replaceState(null, '', '/')
  predictionCatalog.mockResolvedValue({ configured: true, cases: [{ case_id: job.case_id }] })
  predictStudy.mockImplementation(async (_id, _signal, onState, onJob) => {
    onJob(job.job_id)
    onState(job.status)
    return job
  })
  loadSavedPrediction.mockResolvedValue(loaded)
  vi.stubGlobal('fetch', vi.fn(async (url) => {
    if (url === `/scan-inference/jobs/${job.job_id}`) return { ok: true, json: async () => job }
    return { ok: false, status: 404, json: async () => ({ error: 'Unavailable' }) }
  }))
})

it('transfers Analyze ownership and opens the exact verified result in Workbench even without prepared studies', async () => {
  window.history.replaceState(null, '', '/predict')
  const user = userEvent.setup()
  const { unmount } = render(<App />)
  await screen.findByRole('option', { name: /SYNTHETIC_A/ })
  await user.selectOptions(screen.getByLabelText('Scan'), job.case_id)
  await user.click(screen.getByRole('button', { name: 'Run prediction' }))
  await user.click(await screen.findByRole('button', { name: 'Open prediction in Workbench' }))
  expect(window.location.pathname + window.location.search).toBe(route())
  await screen.findByText('Verified image blob:verified-original-ct and blob:verified-current-mask')
  expect(screen.getByText('Prediction artifact verified')).toBeTruthy()
  expect(screen.getByText(jobBase)).toBeTruthy()
  expect(screen.getByText('12.5 mL')).toBeTruthy()
  expect(screen.getByText('ct pred')).toBeTruthy()
  expect(loadSavedPrediction).toHaveBeenCalledWith(jobBase, expect.any(AbortSignal), { ...job, base: jobBase })
  await user.click(screen.getByRole('button', { name: 'Edit verified draft' }))
  await user.click(screen.getByRole('button', { name: 'Settings and tools' }))
  await user.click(screen.getByRole('link', { name: /^Analyze a scan/ }))
  await waitFor(() => expect(screen.getByRole('link', { name: 'Workbench' }).getAttribute('href')).toBe(route()))
  await user.click(screen.getByRole('link', { name: 'Workbench' }))
  expect(await screen.findByRole('region', { name: 'Rendered workspace' })).toBeTruthy()
  expect(loadSavedPrediction).toHaveBeenCalledOnce()
  unmount()
  expect(release).toHaveBeenCalledOnce()
  expect(disposePrediction).not.toHaveBeenCalled()
})

it('reopens a verified result from its URL and refuses a different study for the same job', async () => {
  window.history.replaceState(null, '', route('SYNTHETIC_WRONG'))
  const user = userEvent.setup()
  const { unmount } = render(<App />)
  expect((await screen.findByRole('alert')).textContent).toMatch(/different study/)
  expect(loadSavedPrediction).not.toHaveBeenCalled()
  expect(screen.queryByRole('region', { name: 'Rendered workspace' })).toBeNull()
  await user.click(screen.getByRole('button', { name: 'Retry verification' }))
  expect((await screen.findByRole('alert')).textContent).toMatch(/different study/)
  unmount()
  window.history.replaceState(null, '', route())
  render(<App />)
  expect(await screen.findByRole('region', { name: 'Rendered workspace' })).toBeTruthy()
  expect(loadSavedPrediction).toHaveBeenCalledOnce()
})
