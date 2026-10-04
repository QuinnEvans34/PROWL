# Retained diagnostic metadata fixture

This is a hash-checked subset of project-generated diagnostic metadata from retained real
experiments. It is not synthetic data, a fresh verification of source files, or permission to
execute a historical request. It contains no scan, mask, tensor, checkpoint, cache or probe payload.
The parent probe record contains only its previously sealed path and SHA-256.

Portable tests exercise candidate, identity, coverage, and request guards with these records.
Explicit `local_evidence` tests compare them with the original local evidence and its verified
metadata readers; missing local evidence fails those tests. Production consumers are unchanged.
The manifest records the source paths/hashes and verified readers used during extraction.
