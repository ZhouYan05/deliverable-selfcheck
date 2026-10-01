# AI Usage Log — C5 GitHub Repository

> Structured English abstract of the full Chinese log in [`AI日志.md`](AI日志.md).
> Two names, one deliverable: the Chinese file name satisfies the platform's
> literal keyword `*AI日志*`, the English name matches the course template's
> `AI_LOG.md`. That duplication is itself an example of the naming trap this
> project guards against.

- **Challenge**: C5 GitHub Repository (Elite20)
- **Project**: `deliverable-selfcheck` — a zero-dependency pre-submission checker
- **Repository**: https://github.com/ZhouYan05/deliverable-selfcheck
- **Author**: ZhouYan05 (student id 2024102310451)
- **Date**: 2026-10-01

## 1. How AI was used

| Stage | What AI produced | What I decided |
| --- | --- | --- |
| Read the brief | The 5-dimension rubric (repo quality 25 / community 20 / artifacts 15 / AI usage 20 / reflection 20) and the three red flags (5-point cap each); the required deliverable keywords | Accepted as design constraints |
| Design | A rules-layer split: `CONTENT_RULES` (real credentials only) vs `METADATA_RULES` (credentials + `word: word`) | Accepted after AI **proved** the single-rule version false-positived on `runs-on: ubuntu-latest` |
| Implement | Package layout `src/deliverable_selfcheck/` (rules / checker / cli / `__main__`), `pyproject.toml`, entry point | Accepted; **rejected** AI's suggestion to use `pytest` — "zero dependency" is the product promise |
| Test | 24 `unittest` cases, stdlib only | Accepted |
| Verify | `examples/before` → BLOCKED (exit 1), `examples/after` → READY (exit 0) | Accepted |

## 2. Where AI was actually valuable

Twice it pushed back instead of obeying:

1. It ran the tests it had just written and reported that my blanket
   "colon + space" content rule produced false positives, then proposed the
   scope-based split. That is a better design than my original one.
2. It found that the first colon rule only matched ASCII keys
   (`[A-Za-z]...`) while the platform's *real* rejected title was Chinese
   (`C4 技能分享与传播: deliverable-selfcheck ...`). Fixed to a wide
   `\S:\s+\S` match, with the real rejected title added as a regression test.

## 3. What went wrong

- **Rule scope**: the first version scanned the whole repository with the
  colon rule. It flagged legitimate YAML and prose. Three rounds to stabilise.
- **Chinese keys**: an ASCII-only key pattern silently missed the exact case
  the tool was built for.
- **Literal matching**: I initially assumed fuzzy matching for the platform's
  deliverable keywords. It is a *literal filename substring* match.

## 4. What I would do differently

- Write a one-page "what the platform actually validates" note **before**
  coding. The rule-scope rework was really a boundary problem.
- Move the rules into an external data file so rule changes do not require a
  code change (tracked in the CHANGELOG roadmap).
- Build `examples/before` earlier — a reproducible failure is the cheapest
  test fixture there is.

## 5. Honest disclosure

- Every claim about platform behaviour comes from the author's own real
  submissions (C1–C5), not from documentation guesswork.
- This tool is an *approximation* of the platform's validation. It does not
  replace it; the platform's response is authoritative.
- This log was written by the author with AI assistance and reviewed line by
  line.
