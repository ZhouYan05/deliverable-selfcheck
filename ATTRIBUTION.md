# Attribution

> English version. The Chinese version is [`拿来说明.md`](拿来说明.md).

This repository follows the Elite20 "borrow-with-credit" principle: **borrowing
is fine — but say who you borrowed from, how you used it, and where the
boundary is.**

## 1. What was borrowed

| Item | Source | How it is used | Licence / compatibility |
| --- | --- | --- | --- |
| CLI conventions (`--dir`, `--required`, `--json`, exit codes 0/1/2) | Python standard library `argparse` + common Unix convention | Convention adopted as-is; no third-party code copied | Convention, no copyright |
| The *shape* of a local pre-flight checker (static check, CI-usable exit code, machine-readable JSON report) | General engineering practice shared by linters / pre-commit style tools | Shape and interaction contract only; implementation is entirely original | None |
| "Near-miss" filename warning | Textbook string matching (subsequence test) | Original subsequence check — not edit distance | Public algorithm, no patent/copyright issue |
| Keyword sets for secret detection (`sk-` style keys, GitHub tokens, AWS keys, private key blocks, credential assignments) | Public, widely documented "leaked credential" heuristics | Regular expressions written from scratch; no implementation copied | Public practice |
| MIT licence text | Standard MIT template | Only the copyright line was replaced | MIT permits it |

## 2. What was **not** borrowed (boundaries)

- **No third-party Python package** is used. Zero runtime dependencies, zero
  test dependencies (stdlib `unittest` only).
- **No code or test was copied from another open-source repository.**
- **No non-public platform implementation was used.** The two platform rules
  ("literal filename substring" and "colon + space false positive") were
  derived from the author's own black-box observations while submitting C1–C5.
  They are behaviour reproductions, not source-code reuse.
- **No third party's project is presented as ours.** Everything under
  `examples/before` and `examples/after` was newly written as demo scaffolding.

## 3. Provenance of the two platform observations

1. **Deliverable keywords are matched as a literal filename substring, not
   fuzzily.** `*AI日志*` looks for the four consecutive characters `AI日志` in
   the file name. `AI_工作日志与AAR.md` does **not** match because the
   underscore splits the phrase — a real rejection the author hit during C4.
2. **An ASCII colon followed by a space inside a submission field is read as a
   key/value pair by the sensitive-information filter and rejects the whole
   submission.** The real rejected title was
   `C4 技能分享与传播: deliverable-selfcheck 交付物自检器`; replacing the ASCII
   colon with a dash passes.

These are observations from a single author's samples. The rule set is
therefore *a collection of known traps*, not a complete replica of the
platform's specification.

## 4. How you may reuse this repository

- Copy `src/deliverable_selfcheck/` into your own project: MIT allows it, keep
  `LICENSE`.
- Swap `--required` for your own challenge keywords and use it before
  submitting: encouraged. No attribution required (a note in an Issue is
  welcome).
- Cite the **observations**: please cite them together with the source
  (repository URL + file name), because they are platform-version sensitive
  and easy to misread out of context.

## 5. If we missed an attribution

Open an Issue. **A missing attribution is the least acceptable defect in this
repository — worse than a functional bug.**
