// The original PROWL panther (repository-root PROWL_LOGO.png, copied unchanged to
// public/brand). The file is never edited; the UI uses its transparent shape as a
// CSS mask so the panther shows as a light silhouette on the dark interface
// (approved by Quinton, 2026-10-29). Colour comes from --pw-panther-ink.
export const PANTHER_SRC = '/brand/prowl-panther.png'

export function PantherBadge({ size = 'sm', pulse = false, className = '' }) {
  return (
    <span className={`pw-panther pw-panther--${size}${pulse ? ' pw-panther--pulse' : ''} ${className}`} aria-hidden="true">
      <span className="pw-panther__mark" />
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
