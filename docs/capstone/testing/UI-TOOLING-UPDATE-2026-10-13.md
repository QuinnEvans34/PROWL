# UI tooling update — October 13

## Delivered

Pinned Vite **8.3.4**, Vitest **5.0.4**, and `@vitejs/plugin-react` **6.1.2** with a regenerated
npm lockfile. Node **24.21.0** / npm **11.19.0** remain the verified runtime. No application
component, Vite/Vitest configuration or production dependency version changed.

The React plugin update supplies declared Vite 8 compatibility. The lock comparison records
156 added/removed/version-changed package entries, all in development dependencies, including
platform-specific optional packages. The Vite transition replaces its older bundling toolchain;
there is no force override or hidden peer conflict. `npm ls --all` and clean `npm ci` pass.

The full npm audit now reports **zero vulnerabilities**, compared with ten affected package
entries before the update. This describes the registry audit at verification time; it is not a
claim that every possible security issue is absent. Original audit findings remain in the prior
[review](UI-DEPENDENCY-REVIEW-2026-10-13.md).

## Verification

Tested in an isolated source export before applying the exact package files to the working tree:

| Check | Result |
|---|---|
| Clean `npm ci` and complete dependency tree | Pass; no invalid peer dependencies |
| Full npm audit | Zero reported vulnerabilities; exit 0 |
| UI unit tests | 37 passed across four files |
| Production build plus output preparation | Pass |
| Synthetic fixture/API browser tests | 2 passed |
| Existing saved native-prediction browser tests | 3 passed, 21.7 seconds |
| Saved-package middleware | GET manifest and HEAD CT/prediction return 200/no-store; unapproved file and POST return 404 |
| Generated hosting output | Hosting metadata matches; asset response and SPA fallback pass; no NIfTI payload in build |
| Working-tree install | Clean `npm ci` passes using the verified lock; expected direct versions installed |

Saved-viewer checks cover NiiVue overlays, layer controls, provenance, reload isolation, missing
files, failed results and geometry disagreement. They reuse the existing prepared local package;
no source-data export, model run, data download or remote publication occurred. The owned local
server was stopped and reaped after verification. Browser binaries and the existing Python fixture
environment were reused; this is not a fresh browser/Python installation claim.

The existing warning for bundles over 500 kB remains (NiiVue/compression modules); no threshold
was raised to hide it. Playwright's color-environment warning is also retained. No Python source
changed, so the preceding 5,021-test Python qualification was not rerun for this UI-only update.

## Reproduction and evidence

From `ui/`, select the `.nvmrc` version, verify npm, then:

```sh
nvm use
npm ci
npm ls --all
npm audit
npm run test:run
npm run build
npm run test:e2e
```

For the three saved-prediction checks, follow
[the local viewer instructions](../imaging/SAVED-PREDICTION-VIEWER.md), bind the owned server to
127.0.0.1:5180, then run `npx --no-install playwright test --config playwright.saved.config.js`.
Stop the server afterward. A permitted existing saved package is required for that additional lane.

Evidence: `outputs/prowl/testing/ui-upgrade-20261013/` contains the isolated source, install/clean
install logs, full audit, dependency tree, lock comparison, unit/build/browser logs, saved-route
receipt and server log. Previous package files are preserved in the source archive and Git parent.
Rollback would restore both package files and run `npm ci`; it also restores the old audit findings.
The citation lookup remains paused. This closes the identified npm audit follow-up, not the other
Week 2 source-provenance, cross-machine, hours or Sunday review items.
