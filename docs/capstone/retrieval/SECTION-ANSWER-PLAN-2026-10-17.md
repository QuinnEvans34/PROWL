# Section-context answer checkpoint

After the fixed R8 continuation, use its unchanged section-ranking/terminology configuration and
canonical passages for the existing10exposed answer-quality questions. Reuse the existing ranks
for exact matching disease/volume questions; compute the other three literature packages once.
The four case/private requests must be blocked before retrieval or model calls. No gold text or
required concepts are passed to either retrieval or generation. Retain all traces and failures.

Answer policy v6.2 retains the exact v6.1 instructions, model digest, temperature, seed, mechanical
guards and separate support review. Only evidence capacity changes from5/16kcharacters to50/30k,
and model context from8192 to16384tokens. Two generation calls maximum,60second generation
deadline; live integration additionally has a90second request deadline. Existing v6.1 remains the
default until the new path is qualified. No automatic retries or third prompt candidate here.

One10-case run, at most12answer-generation calls, total15minutes. Read every displayed claim and
its exact source context for support, answer relevance/completeness and readability. Require both
disease questions to give directly supported useful general answers, the volume example to preserve
population/statistics limits, no unsupported displayed claims, correct gap/case/private handling,
and all six literature outcomes without provider failures before considering local preview promotion.
If the strict checkpoint fails, record failures and diagnose before changing another factor. These
are exposed engineering results, not independent clinical acceptance. Fixed-source replay cannot
establish end-to-end latency; measure that separately after qualification.
