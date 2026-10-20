// The original PROWL panther (repository-root PROWL_LOGO.png, copied unchanged to
// public/brand). The file is a padded square; framing is done with CSS only —
// the artwork itself is never cropped, recolored, or regenerated.
export const PANTHER_SRC = '/brand/prowl-panther.png'

export function PantherBadge({ size = 'sm', pulse = false, className = '' }) {
  return (
    <span className={`pw-panther pw-panther--${size}${pulse ? ' pw-panther--pulse' : ''} ${className}`} aria-hidden="true">
      <img src={PANTHER_SRC} alt="" draggable="false" />
    </span>
  )
}

export function Wordmark({ onClick }) {
  return (
    <a className="pw-wordmark" href="/" onClick={onClick} aria-label="PROWL — Studies">
      <span className="pw-wordmark__name">PROWL</span>
      <span className="pw-wordmark__divider" aria-hidden="true" />
      <span className="pw-wordmark__descriptor">Pancreatic review</span>
    </a>
  )
}
