# Progress map (read this first in a new chat)

Last updated: 7 Oct 2026. Project: Chhaya, team SynapseX (IIT Kanpur), solo. Deadline 20 Oct 2026, 19:00 IST;
internal deadline 18 Oct; feature freeze 15 Oct; **science stops at midnight on 10 Oct**.
Claude is the teammate: propose, push back, name the model and effort before each task (README developer guide).

## Where we are

| Milestone | State |
|---|---|
| M1 Data truth | Done. Gate 1 GO |
| M2 Core twin and the reveal | Done and closed. Gate 2 GO on the corrected run |
| M3 Evidence (label check, excursions, record prior, fingersticks) | **Planned, bars committed, no code yet. Start here** |
| M4 Product (three screens, one decision) | Not started |
| M5 Ship (README, deck, 20-minute video, submit by noon 20 Oct) | Not started |

## Start here

1. Open `docs/superpowers/plans/2026-10-07-chhaya-plan-2-excursions.md` and execute Task 1.
   Model: Sonnet 5.5, medium, for Tasks 1 to 3 (specified, tests catch mistakes); Opus 5.5, high, for Tasks 4 and
   5 and for reading the Gate 3 result.
2. Then `2026-10-07-chhaya-plan-3-prior-and-fingersticks.md`. Its two Gate 2 runs take about 25 minutes each in
   the background; start them first.
3. Plan 4 (expiry, band, staleness) is written the day Plan 3 finishes. Cut order if 10 Oct arrives first:
   staleness, band, by-day expiry.

## What was done, in order (details in docs/decisions/)

1. Concept chosen in docs/WAR_ROOM.md. Core twin built and tested (128 tests).
2. Gate 1 GO: 106 usable Shanghai recordings; 65 of 109 on insulin.
3. Gate 2: first run NO-GO, inputs fixed, blend added; GO on 20 held-out patients; break test; corrected re-run
   on 4 Oct, still GO (19 patients, one skipped by the coverage guard).
4. Research round, 4 Oct: sensor lows in Shanghai are 12 % confirmed by fingerstick, so the overnight-low
   fallback was withdrawn; exploratory probes showed fingersticks add little reading by reading; the headline
   was changed; Amendment 3 fixes the Milestone 3 bars.
5. 7 Oct: roadmap rebuilt from today, Plans 2 and 3 written.

## What Chhaya is now (the headline)

The shadow of one sensor wear: **how long that sensor report stays true, what keeps it true, and when to wear a
sensor again**, with an honest band, and a post-meal excursion prediction that works without the sensor. It
does not replace a sensor and has no low-glucose alarm.

## The claims to quote (and nothing bigger)

- Gate 2: on 19 held-out patients, 5 days after the sensor comes off, Chhaya's estimate is 1.4 mg/dL (6 %)
  closer to the hidden sensor than the patient's own average day (p = 4e-05) and about 0.35 mg/dL closer than a
  control that uses no meals (p = 0.04). The gain comes from the meal log and lasts about five days.
- Nothing from the 4 Oct research round is quotable yet. Its counts become quotable when Plan 2, Task 1
  regenerates them; its fingerstick numbers are exploratory and are replaced by the confirmatory run of Plan 3.

## Where things are

- Rules and conventions: CLAUDE.md. Roadmap, calendar and the twelve failure guards:
  docs/superpowers/plans/2026-10-02-chhaya-roadmap.md. Design: docs/superpowers/specs/2026-10-04-chhaya-m3-design.md.
- Bars and amendments: docs/PREREGISTRATION.md. Decisions: docs/decisions/.
- Code: src/chhaya/. Tests: tests/. Results: results/. Research scripts as run: scripts/research_2026-10-04/.
- Not committed: .claude/, .agents/, skills-lock.json (local tooling), data/ (datasets), .venv/.

## Waiting on the team lead

- Three questions to the organisers (rubric; video minimum and live Q&A; non-commercial data).
- Read the RSSDI glucose-monitoring consensus before it is cited.
- One clinician to look at the dashboard on 13 or 14 Oct.
- Whether competitor names stay in the public War Room doc.
