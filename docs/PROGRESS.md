# Progress map (read this first in a new chat)

Last updated: 3 Oct 2026. Project: Chhaya, team SynapseX (IIT Kanpur), solo. Deadline 20 Oct 2026, 19:00 IST.
Claude is the teammate: propose, push back, name the model and effort before each task (README developer guide).

## Where we are

| Milestone | State |
|---|---|
| M1 Data truth (scaffold, twin, loaders, audit, Gate 1) | Done. Gate 1 GO |
| M2 Core twin and the reveal (Gate 2) | Done as registered, **corrected re-run pending** |
| M3 Accuracy and fusion | Not started. Wait for the re-run |
| M4 Product (dashboard, live mode) | Not started |
| M5 Ship (README, deck, 20-minute video, submit by noon 20 Oct) | Not started |

## What was done, in order (details in docs/decisions/)

1. Concept chosen in docs/WAR_ROOM.md. Verified code built and tested (now 128 tests).
2. Both datasets downloaded (data/, git-ignored). Gate 1 GO: 106 usable Shanghai recordings; 65 of 109 on insulin.
3. Gate 2 first run NO-GO (twin tied the average day). Diagnosed, fixed meal inputs, added a blend of
   physiology and the patient's average day. Gate 2 on 20 held-out patients: GO as registered.
4. Break test: no leakage, results reproduce bit for bit, but the honest effect is about 0.4 mg/dL against a fair
   physiology-free control, carried by the meal log. Inputs and gate logic fixed; Amendment 2 committed.

## Next steps, in order

1. Re-run the test split with the fixes: `uv run python -m chhaya.eval.gate2 --dataset cgmacros --split test --k 3 5 7 --jobs 6`
   (about 20 minutes), compare with `results/gate2/cgmacros-test-registered/`, write the decision record.
2. Milestone 3 in the roadmap order (food table, fingerstick correction, insulin input, ...). The primary
   comparator is now the physiology-free control (half average day, half mean).
3. Then M4 (dashboard with live mode) and M5.

## The claim to quote (and nothing bigger)

On 20 held-out patients, 5 days after the sensor comes off, Chhaya is 1.5 mg/dL (7 %) closer than the patient's
average day (p = 3e-05) and about 0.4 mg/dL closer than a no-meals control (p = 0.03). The gain comes from the
meal log and lasts about five days. Time-in-range is not a strength. See docs/decisions/2026-10-03-break-test.md.

## Where things are

- Rules and conventions: CLAUDE.md. Plan and status: docs/superpowers/plans/2026-10-02-chhaya-roadmap.md.
- Pre-registered bars and amendments: docs/PREREGISTRATION.md. Decisions: docs/decisions/.
- Code: src/chhaya/. Tests: tests/. Break-test scripts: scripts/break_test/. Results: results/.
- Not committed: .claude/, .agents/, skills-lock.json (local tooling), data/ (datasets), .venv/.
- Git: branches main, core-twin, break-test all at the same commit. Remote origin is on GitHub.
