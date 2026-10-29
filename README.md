# Attest — agentic verification layer

Attest checks claims about computation artifacts. It does not compute
numbers itself. A language model plans, routes, and explains; deterministic
check plugins read artifact files and issue a verdict, citing the check,
the artifact hash, and the code version.

Verdicts, in order of precedence for a ledger headline:

- `FAILED` — a check proved a claim false (for example, a sector gate
  failed, or the same energy disagrees across sources beyond tolerance).
- `REVIEW` / `UNRESOLVABLE` — a check could not settle a claim, or the
  artifact's own decision criteria were not met (for example, an engine
  abstained on budget). This is **not** a failure, and it is **not**
  a verification. A missing provenance entry is `REVIEW` or
  `UNRESOLVABLE`, not proven failure.
- `VERIFIED` — every applicable check passed, and no check abstained.
  Attest never upgrades an engine's own abstain to `VERIFIED`.

## What Attest is not

- Attest is not a quantum chemistry engine, and it is not ELSD.
  It never runs VQE, never recomputes an energy from a Hamiltonian,
  and never claims a result is decision-grade when the engine that
  produced it abstained.
- Attest does not give away ELSD. The Prometheus engine is a
  closed, black-box proving ground. Attest reads only its output
  artifacts (provenance, history, logs) — never its source, never
  proprietary inputs, molecule identifiers, Hamiltonian terms, or
  raw proprietary results.

## Disclosure — pre-existing work, hackathon delta

This repo was created for the Meta Global AI Developer Hackathon,
Startup Track, submissions due November 4, 2026, 9 PM ET / 6 PM PT.
Target submission: November 4, 2026, noon PT.

Pre-existing work, disclosed, not claimed as hackathon-built:

- **MuseDesk** — a Tauri Windows desktop agent, public repo
  github.com/amitb-gpu/musedesk, pre-existing and functional before
  the hackathon. Pre-hackathon base is tag `v0.1-pre-hackathon`
  at commit `d2358e9` (September 26, 2026). MuseDesk is one front
  end for Attest; it is not the entry itself.
- **MuseDesk Meta API backend** — live-tested September 29, 2026,
  before the hackathon. It was not first built during the hackathon.
  The hackathon delta for MuseDesk is Attest integration, the
  default switch to the Meta API backend, and the WSL bridge fix
  (commit `a660b04`, "Fix WSL bridge: use default distro unless
  MUSED_WSL_DISTRO set", which fixes the hardcoded `-d Ubuntu`
  that failed on machines whose default distro is `Ubuntu-26.04`).
- **Prometheus / ELSD engine** — closed, pre-existing, black-box.
  The engine version used for the proving-ground runs in this
  repo's examples is **v12.3.2**, file SHA-256
  `600b7727151147fb10e98f2e1bef4c17f5cf09c703d7f78479456b136fc57999`
  (435,969 bytes, modified October 9, 2026). Do not cite the
  earlier v12.2.1 version or any "signed v12.2.1 release" claim
  for v12.3.2 — v12.2.1 was the August 9, 2026 qualified version
  (40/40, engine SHA `0b7696f93dd7028f0c8a96620b3c8b62b8bf0852407d0058ed4d5a200a07648e`),
  and that qualification was not re-run for v12.3.2.
- **SpectraNS-3D** — a public, pre-existing second proving ground.
  Its Attest pack in MVP scope is 2 checks, not a full pack.

Hackathon-built, in this repo:

- The claim ledger schema, the deterministic check plugin API,
  the Meta API client wiring for explanation (not computation),
  the open reference adapter (PySCF, H2 — public, no ELSD),
  the ELSD artifact pack (starting with the sigma / source-agreement
  check), the Cu-SOD replay, the fault-injection benchmark,
  the CLI gate, and the report generator.

## Proving ground 1: H2O, spc-d6 — the hook

Two long H2O runs, both H2O_small_d6, spc, seed 1, long settings,
STO-3G, 10 electrons / 7 orbitals (full space, so CASCI = FCI =
exact reference, stated openly — this system is small enough to
verify exactly):

- `d400e878` — 3000/3000 iters, finished October 26, 2026, 12:03 PT.
  VQE physical -75.0125747036 Ha, error 0.0454 kcal/mol,
  correlation captured 99.854%, sector clean.
- `c3373b81` — 5000/5000 iters, finished October 26, 2026, 16:04 PT.
  This was a **fresh rerun with a larger budget, not a checkpoint
  resume**: changing `max_iterations` from 3000 to 5000 changed
  the run ID, so the engine looked for a `c3373b81` checkpoint,
  found none, and started from scratch. The original
  `d400e878` checkpoint was left untouched. Attest flags that
  resume-attempt / fresh-run mismatch as a provenance catch,
  it does not claim a checkpoint resume happened.
  VQE physical -75.01259016765118 Ha, error 0.0357 kcal/mol,
  correlation captured 99.885%, sector clean, truncation 0,
  SCF single converged root, statevector norm 1.000000.

Both runs print `[OK] Chemical accuracy achieved!` and both
report:

```
VERDICT=abstain decision_grade=False reasons=['optimizer_budget_exhausted']
```

That contradiction is the point. Chemical accuracy (error
< 1 kcal/mol) is achieved, but the engine's own decision-grade
criteria require convergence within budget, not just accuracy,
and the engine hit `max_iter`. Attest reports chemical
accuracy **and** the abstain, with headline `REVIEW`, not
`VERIFIED` and not `FAILED`.

Provenance note for `c3373b81`: the log print says
`engine_sha256=n/a`, but the provenance file itself contains
`engine_sha256_full = 600b7727…57999`, matching the verified
engine file. Attest cites the provenance file, not the log
print, and flags the log/provenance discrepancy. Do not cite
a log `n/a` as proof the engine hash is missing from the
artifacts.

## Cu-SOD replay — framing

The Cu-SOD 9.2x → 3.46x story is framed here as
**inconsistent-source detection / consistent-source
recomputation, not settled truth**. Sigma reconciliation
is still open (Warp thread parked), against a Zenodo v3
9.24x verified framing. Attest recomputes from a consistent
source and reports the source disagreement; it does not
present 3.46x as a settled physical truth.

## Prerequisites

- Python 3.10 or later, standard library only. No torch,
  no PySCF, no ELSD needed to run Attest itself.
- For the open reference adapter, PySCF is used separately
  (H2, public, no ELSD) — see `docs/reference-adapter.md`
  when that adapter lands; it is not required for the
  ledger / ELSD artifact checks in this MVP.

## Install

```sh
git clone https://github.com/amitb-gpu/attest.git
cd attest
python3 -m pytest -q
```

No build step, no API key needed to run the checks.
A Meta API key is needed only if you use a model front
end to explain a ledger; the checks themselves never
call a model.

## Usage

Check a single ELSD artifact set:

```sh
python3 -m attest check \
  --provenance examples/fixtures/c3373b81_provenance.json \
  --history examples/fixtures/c3373b81_history_tail.csv \
  --engine-sha 600b7727151147fb10e98f2e1bef4c17f5cf09c703d7f78479456b136fc57999 \
  --out /tmp/attest-ledger.json
cat /tmp/attest-ledger.json
```

Expected headline for the `c3373b81` fixture: `REVIEW`
— chemical accuracy passed, sector passed, truncation
passed, engine hash passed, budget check abstained
(engine hit `max_iter`, decision_grade False).

Run the full test suite:

```sh
python3 -m pytest -q
```

## Examples

- `examples/fixtures/c3373b81_provenance.json` — a fixture
  derived from the pasted log / provenance grep for run
  `c3373b81` (energies, error, correlation, sector,
  verdict, engine hash). It is **not** the full original
  provenance file. On Vermithor, run Attest against the
  original file in `~/musedesk-demo-h2o-resume/` to get
  the authoritative ledger.
- `examples/fixtures/c3373b81_history_tail.csv` — the
  last 5 history rows for `c3373b81`, as pasted. History
  is used only for trajectory shape, never as the
  authoritative energy source — that is provenance /
  statevector, the sigma lesson.

## Troubleshooting

- **Headline is REVIEW, not VERIFIED, even though error
  is 0.0357 kcal/mol.** Correct. The engine abstained on
  budget. Change the engine's convergence / budget criteria
  or run a larger budget that actually converges by the
  engine's own criteria; Attest will not overrule it.
- **Engine hash mismatch.** Compare the provenance file's
  `engine_sha256_full` to the verified engine file hash
  above. A log print of `n/a` is not the provenance file;
  check the file.
- **History.csv missing during a run.** History is only
  written at the end of an ELSD run. Checkpoints and
  process CPU time are the progress signals during a run,
  not history.csv.
- **A check says FAILED on source disagreement.** That
  means the same claim differs across log / provenance /
  history beyond tolerance. Fix the source, do not edit
  the artifact to make the check pass — editing an
  artifact changes its hash and its provenance.

## License

Apache-2.0. Copyright 2026 Amit Brahmbhatt. See `LICENSE`.
ELSD / Prometheus source is not in this repo and is not
covered by this license.
