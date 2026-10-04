"""D-320 exact-bundle restriction atop the unchanged D-269 APFS cohort gate."""
import json
from src.data.manifest_records import digest
from src.data.source_inventory_records import require
from src.operations.storage_roots import cohort_store


class ExactStore:
    def __init__(self,store,artifact_id):
        self.store=store; self.artifact_id=artifact_id; self.root=store.root

    def publish(self,artifact_id,**kwargs):
        require(artifact_id==self.artifact_id,'Capability permits only the exact segmenter bundle')
        return self.store.publish(artifact_id,**kwargs)

    def resolve(self,artifact_id,**kwargs):
        require(artifact_id==self.artifact_id,'Capability permits only the exact segmenter bundle')
        return self.store.resolve(artifact_id,**kwargs)


def segmenter_store(registry,capability,*,trusted_capability_sha256,artifact_id,
                    provider_capability, trusted_provider_sha256):
    require(digest(capability)==trusted_capability_sha256,'Independent segmenter capability pin differs')
    cap=json.loads(capability);provider=json.loads(provider_capability)
    expected=dict(schema_version='1.0.0',approval='D-320',root_alias='prowl_artifacts',area='cohorts',
        operation='publish_and_resolve_exact_segmenter_cohort',artifact_id=artifact_id,
        scientific_runs_enabled=False,registry_sha256=provider['registry_sha256'],
        volume_uuid=provider['volume_uuid'],provider_capability_sha256=trusted_provider_sha256,
        max_bytes=96*1024**2,deadline_seconds=1800,peak_rss_bytes=2*1024**3,
        source_access=False,model_updates=False)
    require(cap==expected,'Unsupported or widened segmenter storage capability')
    store=cohort_store(registry,provider_capability,trusted_capability_sha256=trusted_provider_sha256,create=False)
    return ExactStore(store,artifact_id)
