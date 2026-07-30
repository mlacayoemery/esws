"""Map every InVEST model to its cached sample data.

The sample archives ship InVEST *datastack* files (``*.invs.json``) that record
a complete, known-good set of args for a model. Those are what drive the model
tests, so this walks the cache, resolves each datastack's ``model_name`` (a
pyname) to a model id, and reports which models have data and which do not.

    python3 scripts/invest_sample_manifest.py            # human-readable table
    python3 scripts/invest_sample_manifest.py --json     # machine-readable

Env: INVEST_DATA_ROOT (default /store/invest)
"""
import argparse
import json
import os
import sys

ROOT = os.environ.get("INVEST_DATA_ROOT", "/store/invest")
SAMPLES = os.path.join(ROOT, "samples")

# Models we deliberately do not exercise, and why.
EXCLUDED = {
    "recreation": "needs NatCap's remote recreation server",
}


def _model_registry():
    """{model_id: pyname} from the installed natcap.invest."""
    from natcap.invest import models
    return dict(models.model_id_to_pyname)


def _datastacks():
    """[(path, pyname, args)] for every cached datastack."""
    out = []
    for dirpath, _dirnames, filenames in os.walk(SAMPLES):
        for fn in filenames:
            # Recognised by content rather than name. At least three conventions
            # ship in the archives -- <name>.invs.json,
            # <model>_datastack.invest.json and invest_<model>_args.json -- and
            # matching on the suffix missed the third, which is the only sample
            # data urban_mental_health has.
            if not fn.endswith(".json"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path) as fh:
                    d = json.load(fh)
            except Exception:  # noqa: BLE001 - a bad datastack is just skipped
                continue
            if not isinstance(d, dict) or not isinstance(d.get("args"), dict):
                continue
            pyname = d.get("model_name") or d.get("model_id") or ""
            if not pyname:
                continue
            out.append((path, pyname, d["args"]))
    return sorted(out)


def build():
    registry = _model_registry()
    stacks = _datastacks()

    # Datastacks record a pyname, but InVEST has repackaged modules over time
    # (models became packages in 3.18), so match on the trailing component
    # rather than the full dotted path.
    by_tail = {}
    for model_id, pyname in registry.items():
        by_tail.setdefault(pyname.split(".")[-1], model_id)

    entries = {model_id: {"model_id": model_id, "pyname": pyname,
                          "datastacks": [], "excluded": EXCLUDED.get(model_id)}
               for model_id, pyname in registry.items()}

    unmatched = []
    for path, pyname, args in stacks:
        tail = pyname.split(".")[-1]
        model_id = by_tail.get(tail) or (tail if tail in entries else None)
        if model_id is None:
            unmatched.append((path, pyname))
            continue
        entries[model_id]["datastacks"].append({
            "path": path,
            "dir": os.path.dirname(path),
            "args": args,
        })

    return entries, unmatched


def _stack_name(path):
    base = os.path.basename(path)
    for suffix in (".invs.json", ".invest.json"):
        if base.endswith(suffix):
            return base[:-len(suffix)]
    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    opts = ap.parse_args()

    if not os.path.isdir(SAMPLES):
        sys.exit("no sample cache at %s -- run scripts/fetch_invest_samples.sh" % SAMPLES)

    entries, unmatched = build()

    if opts.json:
        json.dump(entries, sys.stdout, indent=2, sort_keys=True)
        return

    have = [e for e in entries.values() if e["datastacks"] and not e["excluded"]]
    excluded = [e for e in entries.values() if e["excluded"]]
    missing = [e for e in entries.values() if not e["datastacks"] and not e["excluded"]]

    print("%-38s %s" % ("MODEL", "SAMPLE DATA"))
    for e in sorted(have, key=lambda e: e["model_id"]):
        names = ", ".join(_stack_name(d["path"]) for d in e["datastacks"])
        print("  %-36s %s" % (e["model_id"], names))
    for e in sorted(excluded, key=lambda e: e["model_id"]):
        print("  %-36s EXCLUDED -- %s" % (e["model_id"], e["excluded"]))
    for e in sorted(missing, key=lambda e: e["model_id"]):
        print("  %-36s no datastack in the sample archives" % e["model_id"])

    print("\n%d runnable, %d excluded, %d without sample args (of %d models)"
          % (len(have), len(excluded), len(missing), len(entries)))
    for path, pyname in unmatched:
        print("  unmatched datastack: %s (%s)" % (os.path.basename(path), pyname))


if __name__ == "__main__":
    main()
