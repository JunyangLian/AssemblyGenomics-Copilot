"""Fallback public SRA subset download on local Windows, then scp bundle to server.

Requires a local fastq-dump executable. No model API or API key is used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from transfer import manifest, verify, write_json
from server.prepare_sources import prepare_sra


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))["sra"]
    if config.get("uploaded_subset_bundle"):
        parser.error("fallback download requires uploaded_subset_bundle=null")
    bundle = args.output_root.resolve() / "bundle"
    work = args.output_root.resolve() / "work"
    bundle.mkdir(parents=True, exist_ok=True); work.mkdir(parents=True, exist_ok=True)
    status = {"status": "blocked", "gaps": []}
    write_json(bundle / "config.json", {"sra": config})
    try:
        status["sra"] = prepare_sra(config, bundle, work)
        status["status"] = "complete"
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        status["gaps"].append(str(error))
    write_json(bundle / "STATUS.json", status)
    manifest(bundle); checked = verify(bundle)
    print(json.dumps({"bundle": str(bundle), **status, **checked}, ensure_ascii=False, indent=2))
    return 0 if status["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
