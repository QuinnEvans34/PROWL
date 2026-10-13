# UI dependency audit review — October 13

## Finding and scope

The retained full npm audit reports ten affected package entries: four moderate, four high,
two critical. All ten entries are marked development-only in the committed UI lockfile.
A fresh `npm audit --omit=dev --json` on October 13 exits 0 with zero reported vulnerabilities.
This narrows the affected dependency graph; it does not establish that development servers,
build tools or test workers are safe, or that shipped code has no vulnerabilities.

| Installed affected package | Version | Reported severity |
|---|---|---|
| @vitest/mocker | 3.2.7 | Moderate |
| baseline-browser-mapping | 2.10.43 | Moderate |
| browserslist | 4.28.6 | High |
| esbuild | 0.21.5 | Moderate |
| nanoid | 3.3.16 | High |
| postcss | 8.5.19 | Moderate |
| source-map-js | 1.2.1 | High |
| tinypool | 1.1.1 | Critical |
| vite | 5.4.21 | High |
| vitest | 3.2.7 | Critical |

These are npm advisory classifications, not ten verified exploitable PROWL paths. The reports
retain advisory identifiers, affected ranges and suggested fixes. Test configuration has no
explicit Vitest API listener; the browser fixture binds 127.0.0.1. The regular Vite config does
not override host, and its local evidence proxy points to 127.0.0.1:8011. These observations do
not dismiss development-server advisories or prove exploitability. No vulnerability demonstration
or external service access test was performed.

## Next implementation slice

Review a coordinated Vite/Vitest/React-plugin update in an isolated UI export. npm proposes
Vite 8.3.4 and Vitest 5.0.4; registry metadata confirms both accept the pinned Node 24.21.0.
The current React plugin 4.7.0 declares Vite 4–7 support, so upgrading Vite to 8 alone is not a
compatible declared peer set. Choose a compatible React plugin as part of that change, and review
the complete lock diff. Audit recommendations are candidates, not qualified replacements.

1. Resolve compatible tooling versions and inspect dependency changes without force flags.
2. Clean-install the proposed lock; require no unresolved peer conflicts and repeat full and
   production-only audits. Record any residual findings and applicability rather than hiding them.
3. Run all 37 UI tests, production build and synthetic browser checks. Also exercise the saved
   prediction development middleware and built-output preparation because Vite changes affect them.
4. Accept only after preserving viewer/evidence behavior and reviewing warnings. Keep the current
   lock available for rollback; update the runtime/reproduction record with measured results.

This review changes no package version, lock, running service or publication. The dependency
update remains the next independent implementation task; the corpus lookup remains paused.

## Evidence

`outputs/prowl/testing/reproduction-20261013/` retains `ui-audit.json`,
`ui-audit-production.json`, `vite-upgrade-metadata.json`, `vitest-upgrade-metadata.json`, and
`react-plugin-upgrade-metadata.json`. These are October 13 npm registry/audit observations.
The clean-environment and portability reports document the current passing baseline.
