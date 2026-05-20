#!/usr/bin/env python3
"""Merge edges from build/main.rrxiv.aux into build/main.cir.json.

The rrxiv-python parser only extracts claim-to-claim edges where the
\\dependson{}{} arguments are already in the canonical paper:label
form. This paper uses short-form labels (I.1, I.47, etc.) because
the proof DAG is dense and short labels keep the source readable.

This post-processor reads the sidecar, filters to claim-to-claim
edges only (drops post:*, def:*, cn:* targets), and prefixes them
with the canonical paper id.

Usage:
  scripts/merge-sidecar-edges.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

PAPER_ID = "01923f8e-0009-7c4d-9e1f-3a2b1c0d4e5f"
CIR_PATH = Path(__file__).resolve().parent.parent / "build" / "main.cir.json"
AUX_PATH = Path(__file__).resolve().parent.parent / "build" / "main.rrxiv.aux"

# Claim labels in book*.tex are uppercase Roman.Arabic — I.1, II.12, etc.
# (Not post:N, cn:N, def:I.N — those are postulates/common notions/defs.)
CLAIM_LABEL_RE = re.compile(r"^[IVXLC]+\.\d+(\.\d+)?$")
EDGE_RE = re.compile(r"^RRXIV:edge:(depends_on|supports|contradicts|extends):([^|]+)\|(.+)$")


def main() -> int:
    if not CIR_PATH.is_file():
        raise SystemExit(f"missing {CIR_PATH}")
    if not AUX_PATH.is_file():
        raise SystemExit(f"missing {AUX_PATH}")

    cir = json.loads(CIR_PATH.read_text())
    claims_by_short: dict[str, dict] = {}
    for c in cir.get("claims", []):
        # Canonical id ends with ":prop:<label>" — extract short label.
        idx = c["id"].rfind(":prop:")
        if idx >= 0:
            short = c["id"][idx + len(":prop:") :]
            claims_by_short[short] = c
            for key in ("depends_on", "supports", "contradicts", "extends"):
                c.setdefault(key, [])

    merged = 0
    skipped = 0
    for line in AUX_PATH.read_text().splitlines():
        m = EDGE_RE.match(line)
        if not m:
            continue
        kind, src, tgt = m.group(1), m.group(2).strip(), m.group(3).strip()
        # Only claim → claim edges.
        if not (CLAIM_LABEL_RE.match(src) and CLAIM_LABEL_RE.match(tgt)):
            skipped += 1
            continue
        claim = claims_by_short.get(src)
        if claim is None:
            skipped += 1
            continue
        full_target = f"{PAPER_ID}:prop:{tgt}"
        if full_target not in claim[kind]:
            claim[kind].append(full_target)
            merged += 1

    CIR_PATH.write_text(json.dumps(cir, indent=2) + "\n")
    print(f"merged {merged} claim-to-claim edges; skipped {skipped} non-claim edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
