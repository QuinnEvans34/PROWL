# Plan07 M1–M6 pending checkpoint

**Proposed exact scope; no commit/push authorization.** Base is local `main`
`5856fdc9d4f6b2318c918505576244f324247f12` (625file preservation, already committed).
This is a new checkpoint proposal, not a rewrite of its committed scope or V2 manifests.
Authority for current implementation/setup/cleanup is Quinton's M1–M6 dispatch/D-341–345.

The accompanying [JSON list](PLAN07-PENDING-CHECKPOINT-FILES-2026-10-04.json) lists every proposed
file with byte size, mode and SHA-256, and S2's expected handback hashes. Its own path is listed
separately to avoid a self-referential hash. Include the current Claude RUNNING-LOG delta as a
preserved input; Codex did not write it. Include21S2code/test/fixturefiles, its original handback
and R2handoff, S1code/tests/fixtures, new scoped documents and shared decision/navigation changes.
All Claude pins must still match at any future staging. Do not add unrelated untracked files.

Exclude Git-ignored local S1 capabilities/approval/native/cleanup/image-metadata receipts under
`outputs/prowl/PLAN07-S1-SETUP-20261004/`, external invented probe/receipt areas, all original
datasets/models/literature, local roots/secrets, binary draft documents and every previous unrelated
exclusion. The two approved deleted leftovers were untracked/ignored and never part of the prior
625file commit. No historical result, difficult case, failed experiment or hold was deleted.

Verification evidence:49S1tests;131nativeS2/313retrievalpasses;21S2pins/exactcodeidentity; native
APFS setup/durability/lock/fallback; two exact deletion receipts; registry and all previously tracked
imaging/P3producer/test/schema bytes unchanged. Scoped whitespace and relative-document links
checked. No full expanded-project gate claimed. Future commit review must recheck this list against
the then-current working tree and explicit authorization; future public push is another decision.
