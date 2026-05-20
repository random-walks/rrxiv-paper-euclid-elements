# Euclid's *Elements*, encoded as an rrxiv paper

A modern rrxiv encoding of Euclid's *Elements* — all thirteen books, with definitions, postulates, common notions, and propositions registered as first-class rrxiv `claim`s and the proof DAG made explicit via `\dependson` and `\supports` edges.

This is the first **reproducibility demo** on the rrxiv corpus: every proposition is an addressable claim, every proof is a sequence of edges to earlier claims, and the whole structure round-trips through `cir.schema.json` so software agents (and humans) can query the proof graph by claim.

## Scope

| Book | Subject | Status |
| ---- | ------- | ------ |
| I    | Plane geometry, Pythagoras | ✓ full — 23 defs, 5 postulates, 5 common notions, 48 propositions |
| II   | Geometric algebra | ✓ full — 2 defs, 14 propositions (Heath-density proofs, 4 TikZ figures) |
| III  | Circles            | ✓ full — 11 defs, 37 propositions (Heath-density, 3 TikZ figures including III.36 power-of-a-point) |
| IV   | Inscription / circumscription | encoded in this version (see `paper/books/book04.tex`) |
| V    | Eudoxean proportion | encoded — 18 defs, 25 propositions |
| VI   | Similar figures   | encoded — 33 propositions |
| VII  | Number theory (foundations) | encoded — 22 defs, 39 propositions |
| VIII | Continued proportion | encoded — 27 propositions |
| IX   | Number theory (advanced) | encoded — 36 propositions (IX.20 infinitude of primes, IX.36 perfect-number theorem) |
| X    | Incommensurables  | encoded — 16 defs, 115 propositions (longest book) |
| XI   | Solid geometry    | encoded — 28 defs, 39 propositions |
| XII  | Method of exhaustion | encoded — 18 propositions (XII.10 cone-cylinder, XII.18 sphere-volume ratio) |
| XIII | Platonic solids   | encoded — 5 defs, 18 propositions (XIII.18 enumerates the five Platonic solids) |

Books I + II + III carry the full Heath-density proof prose; Books IV–XIII are encoded with statements + condensed proof sketches + the full dependency-edge DAG. The canonical instance lives at [rrxiv.com/papers/rrxiv:2605.00009](https://rrxiv.com/papers/rrxiv:2605.00009).

## Source

The mathematical content is in the public domain (Euclid died ~270 BCE). The Greek-to-English rendering follows the structure of Heath's 1908 translation (*The Thirteen Books of Euclid's Elements*, also in the public domain), with modern wording where Heath's Edwardian English impedes machine-readability. Any modern rephrasing is the contribution of this repo's authors and is released under CC-BY-4.0.

## Why dogfood the *Elements*?

Three reasons:

1. **Stress-test the claim graph.** The *Elements* is the canonical example of a long-distance proof DAG: I.47 (Pythagoras) cites I.4, I.14, I.31, I.41, I.46, which themselves cite earlier propositions back to the postulates. If rrxiv can't encode this, it can't encode a real maths paper.
2. **Stress-test reproducibility.** Every proposition has a proof that depends only on earlier propositions and the five postulates. The whole text is a perfect reproducibility example because the dependencies are explicit and finite.
3. **Hard test case for the parser.** Book I alone has 48 propositions with 100+ inter-claim edges. If the rrxiv-python parser can extract a clean CIR from this, it's ready for normal scientific papers.

## Build

```sh
./scripts/build.sh
./scripts/extract-cir.sh
./scripts/verify.sh
```

## Layout

```
paper/
├── main.tex                # \include each book + the front matter
├── definitions.tex         # Book I definitions (23) + cross-book defs
├── postulates.tex          # The five postulates
├── common-notions.tex      # The five common notions
└── books/
    ├── book01.tex          # Plane geometry — full (48 props)
    ├── book02.tex          # scaffolded
    ├── ...
    └── book13.tex          # Platonic solids — scaffolded
```

## Status

- **Version**: v1
- **Protocol version**: 0.1.0
- **Licence**: CC-BY-4.0 (content) + MIT (build code)
- **Canonical instance**: [rrxiv.com/papers/rrxiv:2605.00009](https://rrxiv.com/papers/rrxiv:2605.00009)

## Contribute

PRs to fill in Books II–XIII are welcome. Each book should follow the conventions in `paper/books/book01.tex`:

- Number each proposition with `\rrxivid`-style stable IDs: `I.1`, `I.47`, `XIII.18`, etc.
- Wrap statements in `\begin{claim}[Proposition X.Y]…\end{claim}`.
- Wrap proofs in `\begin{evidence}…\end{evidence}` immediately after the claim.
- Connect dependencies with `\dependson{X.Y}{X.Z}` and `\supports{X.Y}{X.Z}` edges at the end of each proof.
- Postulates and common notions are `\rrxivremark[Postulate N]` and `\rrxivremark[Common Notion N]` so they're queryable but distinct from claims.
