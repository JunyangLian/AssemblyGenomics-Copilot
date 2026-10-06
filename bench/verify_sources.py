"""Run locally after scp, before opening any source bundle for case construction."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from transfer import verify, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--receipt", required=True, type=Path,
                        help="Write the receipt OUTSIDE the immutable bundle")
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    receipt = args.receipt.resolve()
    if receipt == bundle or bundle in receipt.parents:
        parser.error("receipt must be outside bundle")
    try:
        result = verify(bundle)
        status = json.loads((bundle / "STATUS.json").read_text(encoding="utf-8"))
        result.update({"bundle": str(bundle), "preparation_status": status["status"],
                       "usable_for_cases": status["status"] == "complete"})
        # Never leave a stale success receipt if a later verification fails.
        write_json(receipt, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["usable_for_cases"] else 2
    except (OSError, ValueError, KeyError, TypeError) as error:
        write_json(receipt, {"bundle": str(bundle), "usable_for_cases": False,
                             "error": str(error)})
        print(f"BLOCKED: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
