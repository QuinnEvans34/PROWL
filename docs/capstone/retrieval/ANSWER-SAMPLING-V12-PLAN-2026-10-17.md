# V12 — publisher-recommended Qwen sampling

Inspection found a concrete configuration mismatch: every prior candidate uses temperature0
(greedy decoding). Qwen's official model card specifically advises against greedy decoding in
thinking mode because it can degrade performance or repeat indefinitely. This is a plausible
contributor, not a proven explanation for our failures or timeouts.

Primary source read October17: https://huggingface.co/Qwen/Qwen3-8B#best-practices (also confirmed
in https://huggingface.co/Qwen/Qwen3-30B-A3B-GGUF). Recommended thinking temperature0.6/top_p0.95,
non-thinking temperature0.7/top_p0.8; top_k20/min_p0 for both. Fixed seed42 remains. Other output
length recommendations are for broader tasks; our existing4096draft/1536review token and60s limits
remain, and truncation is still failure. No new weights/downloads or temperature sweep.

After v11 ends, run one fixed comparison using its exact 8B identity, v9 prompts, schemas and
canonical context, changing only sampling to the publisher settings. Same10 exposed questions,
max12 generation calls/15minutes, no retries. Save complete options/traces. Source-review each
answer, including missing qualifications, jargon, hallucinations and refusal correctness. Five
useful supported readable answers, correct gap/four scope blocks, no provider failures and no
unsupported displayed claims are required for a local preview. Report residual concept gaps;
this is not independent/clinical acceptance or a formal evaluation freeze. If unsuccessful,
retain the result rather than searching seeds or cherry-picking answers.
