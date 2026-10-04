# D-284 checkpoint storage verification

Use the existing D-273 checkpoint/backup-verification capability (independent pin
`e2651188827877d11888d13e7e0e3555b83b97816c9f10d0db6820ab002d3486`) under D-284's continuation
request. Existing registered APFS roots, identity checks, 96-MiB artifact ceiling, 1-GiB/domain
increment and internal20-GiB quota/free-space floor remain in force. No real optimizer updates,
source aliases, new roots or altered storage capability. Catalogs retain D-273 as the underlying
storage permission; this document records the D-284 expanded-checkpoint application.

Publish exactly the synthetic step3 checkpoint and the completed real-input forward profile's
step0 checkpoint, only after each local receipt/probe is verified. Each payload is four files:
identity, inputs, progress, tensor state. Use the expanded CPU semantic validator through the
existing generic artifact/backup hooks. Copy to the independent internal keeper store, then
invoke recovery-only stores and restore to a new destination without a primary-store argument.
Require byte-identical payload and exact completed step. Preserve failed attempts. No promotion
to model keeper quality or claim of training-readiness from a step0 checkpoint.
