import { useState } from 'react'
import { Check, ClipboardCopy } from 'lucide-react'
import { ANATOMY_STRUCTURES, contactCategoryLabel, rgb, structuredSummaryText } from '../lib/studyInsights.js'

const LOCATION = { head: 'Pancreatic head', body: 'Pancreatic body', tail: 'Pancreatic tail' }
const ATTENUATION = { hypoattenuating: 'Hypoattenuating', isoattenuating: 'Isoattenuating', hyperattenuating: 'Hyperattenuating' }
const colorOf = name => ANATOMY_STRUCTURES.find(item => item.name === name)?.color || [148, 163, 184]
const mm = value => (Number.isFinite(value) ? `${value.toFixed(1)} mm` : '—')

export function LesionCharacteristics({ insights }) {
  const lesion = insights?.lesion
  if (!lesion?.present) return null
  const share = lesion.location_share_pct || {}
  return (
    <section className="pw-insight-card" aria-label="Lesion characteristics">
      <header><h3>Lesion characteristics</h3><small>From the model outline</small></header>
      <dl className="pw-insight-grid">
        <div><dt>Axial long × short axis</dt><dd className="pw-num">{(lesion.long_axis_mm / 10).toFixed(1)} × {(lesion.short_axis_mm / 10).toFixed(1)} cm</dd></div>
        <div><dt>Location</dt><dd>{LOCATION[lesion.location] || '—'}{Number.isFinite(share[lesion.location]) ? <small> {share[lesion.location]}%</small> : null}</dd></div>
        <div><dt>Attenuation</dt><dd>{ATTENUATION[lesion.attenuation] || '—'}{Number.isFinite(lesion.attenuation_delta_hu)
          ? <small> {lesion.attenuation_delta_hu > 0 ? '+' : ''}{lesion.attenuation_delta_hu} HU vs pancreas</small> : null}</dd></div>
        <div><dt>Mean density</dt><dd className="pw-num">{lesion.lesion_mean_hu} HU <small>pancreas {lesion.parenchyma_mean_hu} HU</small></dd></div>
      </dl>
      <p className="pw-fine">Long axis measured on the axial slice with the largest lesion diameter. Location uses the dataset's head/body/tail reference regions.</p>
    </section>
  )
}

export function VesselRelationship({ insights }) {
  const anatomy = insights?.anatomy || []
  const vessels = anatomy.filter(item => item.kind !== 'duct')
  const ducts = anatomy.filter(item => item.kind === 'duct')
  const lesionPresent = Boolean(insights?.lesion?.present)
  if (!anatomy.length) return null
  // Without a predicted lesion there is nothing to relate vessels to: keep the duct
  // calibres (still informative) and drop rows that would only show dashes.
  const rows = lesionPresent ? vessels : []
  return (
    <section className="pw-insight-card" aria-label="Vessel relationship">
      <header><h3>{lesionPresent ? 'Vessel relationship' : 'Reference anatomy'}</h3><small>{lesionPresent ? 'Model lesion vs reference anatomy · for review' : 'Dataset annotation · for review'}</small></header>
      {!lesionPresent && <p className="pw-fine">No predicted lesion, so vessel contact is not assessed. Reference vessels are still shown in the viewer.</p>}
      <table className="pw-vessel-table">
        <thead><tr><th scope="col">Structure</th><th scope="col">{rows.length ? 'Closest' : 'Calibre'}</th><th scope="col">{rows.length ? 'Contact' : ''}</th></tr></thead>
        <tbody>
          {rows.map(item => (
            <tr key={item.name} className={item.contact_category ? `is-${item.contact_category}` : undefined}>
              <th scope="row"><i style={{ background: rgb(colorOf(item.name)) }} aria-hidden="true" />{item.label}</th>
              <td className="pw-num">{item.annotated === false ? 'Not annotated' : mm(item.min_distance_mm)}</td>
              <td>{item.annotated === false ? '—' : <span className={`pw-contact pw-contact--${item.contact_category}`}>
                {contactCategoryLabel(item.contact_category)}{item.contact_angle_deg > 0 ? ` · ${Math.round(item.contact_angle_deg)}°` : ''}</span>}</td>
            </tr>
          ))}
          {ducts.map(item => (
            <tr key={item.name}>
              <th scope="row"><i style={{ background: rgb(colorOf(item.name)) }} aria-hidden="true" />{item.label}</th>
              <td className="pw-num" colSpan={2}>{item.annotated === false ? 'Not annotated'
                : <>{mm(item.max_calibre_mm)} calibre {item.dilated ? <span className="pw-contact pw-contact--abutment">dilated</span> : <small>within {item.upper_normal_mm} mm</small>}</>}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {lesionPresent && <p className="pw-fine">Contact = share of the vessel's circumference within one voxel of the predicted lesion on the worst axial slice
        (≤ 180° abutment, &gt; 180° encasement). Reference anatomy is the dataset annotation, not a model output; this is not a resectability call.</p>}
    </section>
  )
}

export function StructuredSummary({ insights, studyLabel }) {
  const [copied, setCopied] = useState(false)
  if (!insights) return null
  const text = structuredSummaryText(insights, { studyLabel })
  return (
    <details className="pw-insight-card pw-insight-card--summary">
      <summary><strong>Structured summary draft</strong><small>SAR/APA-style fields</small></summary>
      <pre className="pw-structured-text">{text}</pre>
      <button type="button" className="pw-btn pw-btn--sm pw-btn--secondary" onClick={async () => {
        try { await navigator.clipboard?.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000) } catch { setCopied(false) }
      }}>{copied ? <Check size={13} aria-hidden="true" /> : <ClipboardCopy size={13} aria-hidden="true" />} {copied ? 'Copied' : 'Copy summary'}</button>
    </details>
  )
}
