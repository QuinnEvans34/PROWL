import { useEffect, useId, useState } from 'react'
import { MeasurementReadout } from './PredictionMeasurements.jsx'
import './FindingAskPanel.css'

function centimetres(mm) {
  return mm < 0.1 ? '<0.01' : (mm / 10).toFixed(2)
}

function SelectedOutline({ finding, measurement, onInspect }) {
  const dimensions = finding.dimensions
  const { calipers, superiorInferiorMm } = dimensions || {}
  const axes = calipers?.axes
  const validCalipers = axes?.length === 2 && axes.every(axis => Number.isFinite(axis.lengthMm) && axis.lengthMm > 0)
  const validExtent = Number.isFinite(superiorInferiorMm) && superiorInferiorMm > 0
  const pancreas = finding.anatomy === 'pancreas'
  const heading = pancreas ? 'Pancreas outline' : `Predicted lesion ${finding.ordinal || ''}`.trim()
  const volume = finding.volumeMl ?? (pancreas ? measurement.pancreasMl : dimensions?.volumeMl)
  return <>
    <h3>{heading}</h3>
    <dl className="pw-finding-ask__measurements">
      {validCalipers && <div><dt>Centered slice calipers</dt>
        <dd>{axes.map(axis => centimetres(axis.lengthMm)).join(' × ')} cm</dd></div>}
      {validExtent && <div><dt>Head-to-foot extent</dt><dd>{centimetres(superiorInferiorMm)} cm</dd></div>}
      {Number.isFinite(volume) && volume >= 0 && <div><dt>Outline volume</dt>
        <dd>{volume > 0 && volume < 0.01 ? '<0.01' : volume.toFixed(2)} mL</dd></div>}
    </dl>
    <p className="pw-fine">{validCalipers
      ? 'The two caliper distances describe the outline where it crosses the measured CT slice. Volume uses labeled voxels across the outline.'
      : 'Volume uses labeled voxels across the displayed prediction.'}</p>
    {dimensions?.caliperUnavailableReason && !validCalipers && <p className="pw-fine">{dimensions.caliperUnavailableReason}</p>}
    {validCalipers && calipers.plane && onInspect && <button type="button" className="pw-btn pw-btn--secondary pw-btn--sm"
      onClick={onInspect}>Show measured slice</button>}
  </>
}

export default function FindingAskPanel({ measurementState, finding, onInspect, literatureRequest, children }) {
  const [scope, setScope] = useState('literature')
  const group = useId()
  const measurement = measurementState?.status === 'ready' ? measurementState.measurement : null

  useEffect(() => {
    if (literatureRequest?.token != null) setScope('literature')
  }, [literatureRequest?.token])

  return <div className="pw-finding-ask">
    <div className="pw-segmented pw-finding-ask__scopes" role="group" aria-label="Ask PROWL sources">
      <button type="button" aria-pressed={scope === 'outline'} aria-controls={`${group}-outline`}
        onClick={() => setScope('outline')}>This outline</button>
      <button type="button" aria-pressed={scope === 'literature'} aria-controls={`${group}-literature`}
        onClick={() => setScope('literature')}>Published evidence</button>
    </div>
    <div id={`${group}-outline`} className="pw-finding-ask__outline" hidden={scope !== 'outline'}>
      {measurement && finding
        ? <SelectedOutline finding={finding} measurement={measurement} onInspect={onInspect} />
        : <>
          <h3>Displayed prediction</h3>
          {measurement
            ? <MeasurementReadout state={measurementState} compact showEvidence={false} />
            : <p role="status">{measurementState?.status === 'loading' ? 'Checking the displayed outline…'
              : measurementState?.reason || 'Show a verified prediction to review its measurements.'}</p>}
        </>}
    </div>
    <div id={`${group}-literature`} className="pw-finding-ask__literature" hidden={scope !== 'literature'}>{children}</div>
  </div>
}
