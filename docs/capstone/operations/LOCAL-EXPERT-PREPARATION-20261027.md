# Local AI expert preparation — October 27

The Research and Workbench literature panels now provide **Prepare AI expert** and
**Check status**. This is a local Vite development control, not a hosted service.
Preparation mounts the configured volume UUID if connected/unlocked, verifies the existing
storage/configuration gates, starts Docker if absent, starts only the existing dedicated
literature container after checking its data mount, starts the current study/general-extract
search service if absent, and loads the reviewed qwen3:8b model if the training lock is free.
There is no model download, database creation, ingestion, container replacement, automatic
Docker restart, or teacher pause. Missing/encrypted/disconnected drives still need user action.
A stale Docker mount reports an explicit restart instruction because restart affects other projects.

While the teacher holds the GPU lock, preparation restores source search but skips model loading.
The local UI middleware rejects answer/rephrase requests during that reservation. Saved-mask
measurements and source search remain available. This is a local UI guard, not an authentication
boundary for direct calls to the separate loopback API. The existing teacher launcher also checks
its own exclusive-GPU admission. Full simultaneous teacher/answer-model operation is not qualified.

October27 incident: database container was stopped; Docker reported `invalid mount config`
although macOS had the correct drive. With explicit approval, Docker Desktop was restarted,
warpaths-neo4j restored and the dedicated literature database started. Database health and search
backend checks passed; teacher continued to advance. The button was exercised in the browser.

Validation: six Python checks cover exclusive lock, source-only preparation, mount mismatch,
stale Docker error, pinned-model warmup under lock and missing-model refusal. Sixty-seven UI/plugin
checks pass, including the existing literature and general-extract suites. Production Vite build
passes with existing large-chunk warnings. Actual model warmup is intentionally not exercised while
the teacher is active; that remains a live check after the next authorized teacher pause.
