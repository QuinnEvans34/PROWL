# Candidate header preflight — D-280

Exact input: candidate receipt `3e961f4c3285107d765d2176050c2d57aeb29d0ab8d5893ba1fa3b6db97a26e1`,
16 train / 12 validation studies, 56 CT/pancreas paths. Existing descriptive selection is unchanged.
Purpose: determine dimensions, declared spatial units, affine agreement and likely content-audit
cost before designing the full voxel qualification job. This is not qualification or training.

Read only the first 348 decompressed NIfTI-1 header bytes per selected file, at most 64 KiB compressed
per file / 4 MiB total. No CT/mask arrays, lesion files or publisher-test payloads. Verify registered
external UUID/mount, exact pinned registry, retained inventory path/size/device/inode/time fields,
regular non-symlink paths and before/after file stability. No global alias activation or source write.
Budget: 300 s, 512 MiB process RSS, 4 MiB output, internal free floor 100 GiB. Stop on unsafe path,
changed identity, cap or malformed header; preserve incomplete attempt. Report per-case header
concerns without inferring anatomical quality or excluding difficult scans. Full decompression,
content hashes, gzip CRC, target encoding/presence, physical-unit evidence, alignment and duplicate
checks remain mandatory in the later qualification job. Header affine agreement alone is insufficient.
