# D-298 — synthetic physical-context profile

Quinton authorized continuing after D-297 on September 30. Owned slice: separate profiler,
its synthetic tests and operational evidence. Production model/configuration guards and data
consumers stay unchanged. No raw-data reads, cache build, production checkpoint or real training.

Compare 96³ and 144³ at nominal 2 mm spacing (192 and 288 mm input spans). Both use the exact
scratch SegResNet architecture, balanced CE/foreground Dice, AdamW at 0.0003 and seed 42.
Each process has eight synthetic updates (two warmup, six measured), two CPU-stitched MPS
sliding-window forwards of the same invented 192×160×192 volume, checkpoint save/reload,
and one resumed synthetic update. The synthetic center crop is intentionally separate from
the production sampler, whose 96³ guard must still reject 144³. No sampler qualification or
learning-quality comparison follows from timing this invented object.

Run 96 first, then 144 only if the smaller profile passes. Per process: 600 seconds, 16 GiB
RSS and MPS-driver limits, 256 MiB outputs, 100 GiB internal free-space floor, AC power,
no CPU fallback. Sequential aggregate at most 20 minutes/512 MiB outputs. Retain failures.
Report all timings and sampled allocated/driver memory, supervisor peak RSS, finite gradients,
shape checks and checkpoint probability parity (absolute tolerance 1e-5). Memory samples
are observations rather than allocator high-water instrumentation. Same-process reload is
not independent backup recovery. Any later cache/real profile requires its own frozen scope.

The result should select a practical patch candidate for the next adapter/cache implementation,
not launch training. Record all changed factors and preserve the D-297 cases/holds.
