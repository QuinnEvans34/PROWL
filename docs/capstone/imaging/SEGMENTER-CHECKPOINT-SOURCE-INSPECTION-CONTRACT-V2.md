# Metadata source boundary v2 — Darwin descriptor-volume repair

October6: Quinton requested iteration through every readiness step now. New four-file reader2
scope: source/test/this contract/dated result. Preserve reader1/A/dispatcher1 and failed B01. All
reader1 format, restricted fake load,83signature, tuples, no-value I/O and worker limits unchanged.
No source acceptance/training authority. Read-only metadata repair follows the native diagnostic.

Versioned copy of reader1, independently pinned; never monkeypatch its guards or imports. API
unchanged; control/report schemas end in -2. Source volume now has exactly mount,uuid,filesystem,
device,fsid,method. Invented record is mount/uuid/filesysteminvented,device=source root device,
fsid=[0,0],methodinvented. Actual requires filesystemapfs,valid UUID,device equal pinned source/root,
fsid two signed32-bit integers,methoddarwin_fstatfs_diskutil,mount absolute. Never use path ancestry
as evidence of a volume identity: Darwin firmlinks may map a logical source to another mount path.

Actual observer opens the directory through no-follow ancestors; no source leaf is opened. Bind
directory device/inode/mode/owner before/after observation. Use Darwin64-bit fstatfs layout from
installed SDK sys/mount.h:2168bytes/8byte alignment,MAXPATHLEN1024,fsidtwo int32. Fail other
platforms/architectures/ABI. Kernel filesystem must be apfs; open the returned physical mount
through no-follow directories, require directory/device/fsid equal original descriptor. Kernel
mount name and filesystem are reobserved on both descriptors before/after bounded tool call.

Only `/usr/sbin/diskutil info -plist <kernel mount>`;3s/64KiB stdout/4KiB stderr,50ms parent+child
sampled3GiB stop, monitor available before spawn, exclusive owned group cleanup. Parse only APFS
mount/UUID/filesystem. On nonzero decode bounded ErrorMessage/ErrorString from plist stdout or
stderr for a bounded refusal; no unfiltered hardware plist retained. Require tool mount equal
kernel physical mount and filesystemapfs; no guessed slash/device, symlink or permissive fallback.
Snapshot directory/mount/fsid/device before/after and compare source/root current volume with
frozen control before/after metadata inspection. Remount/drift/refusal never enables another path.

Qualification: new invented fixtures/actual-envelope denials without actual candidate access;
300s/3GiB aggregate pytest+owned children50ms. Existing source-reader tests may be versioned into
the new test file to qualify dependency change, not rerun old suites. Add actual kernel observer
on newly created private temporary directory (filesystem metadata only) and independent ABI
oracle from installed header, tool return/error/limits, same-device/fsid and firmlink policy cases.

After pass, new dispatcher2 four-file scope freezes one actual B02 attempt; the fixed original
candidate/path/SHA/namespace and64,889,231B/60s worker/90s attempt/3GiB/4MiB bounds remain.
No actual hash/metadata decode occurs in reader unit tests. All actual attempts are one-use.
