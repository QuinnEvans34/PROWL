# V15 — bounded local instruction-model comparison

User authorizes autonomous improvements until engineering confidence. R8 recovers useful evidence,
but v6.2/v9–v14 repeatedly lose qualifiers, overgeneralize anatomy or fail readability. V14's two
plain-text canaries also fail. Stop further prompt variants on those models. This recorded scope
amendment permits ONE additional inference-model download for this comparison; it does not open
training, the full selector, cloud inference or an unbounded model sweep. Earlier completion-spec
exclusion of new downloads is superseded only for this named, bounded candidate.

Candidate: Ollama qwen2.5:14b (Qwen2.5-14B-Instruct, Q4_K_M, Apache2.0), exact registry manifest
SHA2567cdf5a0187d5c58cc5d369b255592f7841d1c4696d45a8c8a9489440385b22f6. Publisher metadata:
https://ollama.com/library/qwen2.5:14b and https://huggingface.co/Qwen/Qwen2.5-14B-Instruct.
Registry manifest downloaded before weights:8,988,123,581layer bytes. This is a practical comparison
of instruction-following behavior, not a claim that an older/larger model is inherently better.

Storage: separate /Volumes/PROWL-Data/PROWL/scratch/answer-model-v15-20261017/ollama store, max12GiB,
external free floor100GiB; internal floor104GiB, no model bytes intentionally written internally.
Admission112,178,634,752internal/2,112,779,743,232external free bytes. Verify registered drive identity.
No model/cache/database deletion, relocation, or changes to the existing model store. Stop only
resident experimental models before loading the candidate, not the existing Ollama service.
Separate owned loopback11435 server, cloud disabled, one loaded model/one request, no pruning.
Download max20minutes, no retry/reset; hash-verify registry manifest and every stored blob before use.
Retain failures/partial download. Monitor owned inference memory, stop if above18GiB RSS or host
storage floors crossed; max60s per request. No duplicate worker or concurrent inference.

First compare two fixed exposed canaries (head-size/published-volume) using exact v9 evidence and
v9 prompts/schema, but non-thinking mode because this model has no native thinking mode. Fixed
seed42/temperature0/context16384; maximum2calls per case and4generationcalls total/4minutes.
Use same exact-quote/number/qualifier guards and separate source review. No repair/retry or supplied
expected answers. Pin model/code before execution. Both must give useful supported readable answers
with appropriate qualifications before a separately documented continuation or live integration.
Every source claim is inspected as engineering review; formal/protected/clinical acceptance stays open.
