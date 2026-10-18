# Live answer quality v8: bounded follow-up

The first v7 candidate was rejected, not promoted: its displayed volume answer introduced “healthy
control group” where the cited passage only used an undefined abbreviation; its function answer
retained unexplained specialist labels despite a positive readability review. One draft exhausted
the token limit. All six attempts, including failures, remain under the v7 local replay directory.

This is one follow-up candidate, not an automatic sweep. Retain exact citation binding, numeric and
mandatory-strength checks and the four explicit review dimensions. Add a conservative mechanical
check against introducing healthy/normal-person/control-group descriptors absent from cited text.
This is a narrow lexical backstop, not semantic proof, and can reject legitimate paraphrases.
Use a shorter generic instruction and non-reasoning draft mode to reduce generation overhead.
Do not encode question-specific answers or disease facts in either prompt.

Replay the same six old top5 evidence sets once, max12 generation calls,600seconds, no retries.
Pin source/config/input/producer before invocation; preserve every outcome locally. Judge support,
relevance, source qualifications, readable language and failures separately. The v7 promotion
criteria remain unchanged: no observed unsupported displayed claim, removal of the known failure,
at least one readable supported answer, and offline tests passing. This small exposed run cannot
establish general quality. If it fails, retain the candidate as unpromoted and stop policy iteration
in this checkpoint. Do not relax checks to obtain an answer.

If qualified, integrate the policy pin and UI failure/insufficiency wording and run the two previously
selected live smoke questions once each. Preserve all live outcomes; a retrieval-limited abstention
does not count as a complete answer. Formal human/protected evaluation and retrieval comparison
remain open. This work is authorized by Quinton's request to move to live answer quality; it does
not infer acceptance of pending labels or change corpus/ranking/model identity.
