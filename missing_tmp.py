import sys, os
sys.path.insert(0, "/app/scripts")
import run_model_jobs as R
import invest_sample_manifest as manifest
from load_demo import layer_name
manifest.SAMPLES = R.SAMPLES
entries, _ = manifest.build()
files = manifest.build()  # (entries, unmatched)
# which rasters does the manifest actually collect?
collected = set()
for mid, entry in entries[0].items() if isinstance(entries, tuple) else entries.items():
    pass
