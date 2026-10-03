# Chhaya

**A Type 2 diabetes digital twin that keeps working after the glucose sensor comes off.**

Submission to the Happiest Health Digital Twin Challenge 2026.

| | |
|---|---|
| Team | SynapseX (solo) |
| College | IIT Kanpur |
| Submission folder | `SynapseX_IITK` |
| Status | Work in progress. No accuracy numbers are published until the evaluation in `docs/PREREGISTRATION.md` has been run. |

## Idea

A continuous glucose sensor in India costs about Rs 4,200 for 14 days, so almost nobody with T2D wears one
continuously. Chhaya (Hindi for "shadow") wears the sensor once: a physiological glucose-insulin model is
personalised to the patient from their health record (the prior) and the sensor fortnight (the evidence).
After the sensor is removed, the twin keeps estimating glucose from logged meals, a fitness band and
occasional fingersticks, always with an uncertainty band, and flags when it has gone stale.

The headline experiment is hide-and-reveal: calibrate on the first k days, hide the rest, estimate the
hidden days without the sensor, then lay the real trace on top.

## Repository map

- `src/chhaya/` the package: data loaders, the twin (ODE, calibration), evaluation
- `tests/` the test suite (synthetic patients with known true parameters)
- `docs/WAR_ROOM.md` why this concept, and what the competing entries do
- `docs/PREREGISTRATION.md` the pass bars, fixed before any real-data run
- `docs/superpowers/plans/` the roadmap and task-level plans
- `CLAUDE.md` project rules and conventions

## Run

```bash
uv sync
uv run pytest -q
uv run python -m chhaya.data.download shanghai cgmacros
uv run python -m chhaya.data.audit
uv run python -m chhaya.eval.gate2 --dataset cgmacros --k 3 5 7
```

## Data and licences

Code: MIT. Datasets are downloaded by the user and never redistributed: ShanghaiT2DM (CC BY 4.0, Zhao et al.,
Scientific Data 2023) and CGMacros (CC BY-NC-SA 4.0, PhysioNet, doi 10.13026/3z8q-x658; non-commercial use only).

To be completed at submission: results, limitations, architecture diagram, deck, video link.

---

## Developer guide: which model for which task (remove before submission)

This is a solo project, so spend model capacity where a wrong answer is expensive. Claude (the teammate)
names the model and effort before each task and says when to switch. Switch with the model picker in the app.

| Task | Model and effort | Why |
|---|---|---|
| Experiment design, leakage review, reading a Gate result, deciding a pivot | **Opus 5.5, max** | Rare, and a wrong call costs days |
| Changing the ODE, fitting, priors, event prediction, numerical bugs | **Opus 5.5, high** | Subtle; tests only catch part of it |
| Pre-merge review of model or evaluation code (`mle-reviewer`, `python-reviewer`) | **Opus 5.5, high** | Reviewer misses are silent |
| Clinical wording, alert thresholds, dashboard safety copy (`healthcare-reviewer`) | **Opus 5.5, high** | Patient-facing, safety-sensitive |
| Video script and pitch narrative | **Opus 5.5, high**, once | One high-leverage draft, then edit cheaply |
| Loaders, metrics, CLI glue, tests written from a spec | **Sonnet 5.5, medium** | Specified work; tests catch mistakes |
| Dashboard pages (Streamlit and Plotly) | **Sonnet 5.5, high** | Many visual iterations |
| README, deck text, figure polish, formatting | **Sonnet 5.5, medium** | Low risk |
| Running commands, renames, lint, git, downloads | **Sonnet 5.5, low** or **Haiku 4.5** | Mechanical |
| Quick lookups and questions | **Haiku 4.5, low** | Cheap and fast |

Rule of thumb: start on the cheapest model that is safe for the task, and escalate after one failed
attempt, not before. Anything that decides what we claim goes to Opus; anything that is already specified
goes to Sonnet.
