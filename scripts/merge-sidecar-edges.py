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
ROOT = Path(__file__).resolve().parent.parent
CIR_PATH = ROOT / "build" / "main.cir.json"
AUX_PATH = ROOT / "build" / "main.rrxiv.aux"
META_PATH = ROOT / "rrxiv-meta.json"

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

    # Rewrite the canonical paper-level fields. The parser sets paper_id /
    # claim.id prefixes to the rrxiv-meta slug ("rrxiv-paper-euclid-elements")
    # which is fine for build artefacts but the deployed instance keys
    # everything off the canonical UUID. Patch both top-level + each
    # claim so re-ingest finds them by paper_id.
    cir["id"] = PAPER_ID
    cir.setdefault("id_slug", "rrxiv:2605.00009")

    # Overlay structured authors + based_on + license + topics from
    # rrxiv-meta.json. The parser captures the LaTeX \author{} arg
    # verbatim — for Euclid that includes a \\\and\small annotation
    # we want kept in the rendered PDF but cleaned out of the CIR.
    # rrxiv-meta.json carries the canonical structured author list
    # (one entry per author, with orcid + is_agent + agent_handle),
    # so use it as the source of truth here.
    if META_PATH.is_file():
        meta = json.loads(META_PATH.read_text())
        if isinstance(meta.get("authors"), list) and meta["authors"]:
            cir["authors"] = meta["authors"]
        for key in ("license", "topics", "based_on"):
            if key in meta and meta[key] is not None:
                cir[key] = meta[key]
        # `version` from meta is authoritative too (e.g. "v2" after a
        # revision); fall back to whatever the parser set otherwise.
        if meta.get("version"):
            cir["version"] = meta["version"]
    for c in cir.get("claims", []):
        c["paper_id"] = PAPER_ID
        # `id` may be either parser-shape ("rrxiv-paper-euclid-elements:prop:I.1")
        # or already canonical. Normalise to canonical.
        idx = c["id"].rfind(":prop:")
        if idx >= 0:
            short = c["id"][idx + len(":prop:") :]
            c["id"] = f"{PAPER_ID}:prop:{short}"
        # Same rewriting for any inter-claim edges already on the claim.
        for key in ("depends_on", "supports", "contradicts", "extends"):
            c.setdefault(key, [])
            c[key] = [
                t if ":prop:" not in t
                else f"{PAPER_ID}:prop:{t.rsplit(':prop:', 1)[1]}"
                for t in c[key]
            ]

    claims_by_short: dict[str, dict] = {}
    for c in cir.get("claims", []):
        idx = c["id"].rfind(":prop:")
        if idx >= 0:
            short = c["id"][idx + len(":prop:") :]
            claims_by_short[short] = c

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
