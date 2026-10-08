# Which model for which task

Moved out of the README on 8 Oct 2026. This is a solo project, so model capacity is spent where a wrong answer
is expensive. Claude (the teammate) names the model and effort before each task and says when to switch.
Switch with the model picker in the app.

| Task | Model and effort | Why |
|---|---|---|
| Experiment design, leakage review, reading a Gate result, deciding a pivot | **Opus 5.5, max** | Rare, and a wrong call costs days |
| Changing the ODE, fitting, priors, event prediction, numerical bugs | **Opus 5.5, high** | Subtle; tests only catch part of it |
| Pre-merge review of model or evaluation code (`mle-reviewer`, `python-reviewer`) | **Opus 5.5, high** | Reviewer misses are silent |
| Clinical wording, alert thresholds, dashboard safety copy (`healthcare-reviewer`) | **Opus 5.5, high** | Patient-facing, safety-sensitive |
| The dashboard's design system and its hero chart | **Opus 5.5, high** | The judges' first look; taste and correctness both matter |
| Video script and pitch narrative | **Opus 5.5, high**, once | One high-leverage draft, then edit cheaply |
| Loaders, metrics, CLI glue, tests written from a spec | **Sonnet 5.5, medium** | Specified work; tests catch mistakes |
| Dashboard pages once the design system exists | **Sonnet 5.5, high** | Many visual iterations |
| README, deck text, figure polish, formatting | **Sonnet 5.5, medium** | Low risk |
| Running commands, renames, lint, git, downloads | **Sonnet 5.5, low** or **Haiku 4.5** | Mechanical |
| Quick lookups and questions | **Haiku 4.5, low** | Cheap and fast |

Rule of thumb: start on the cheapest model that is safe for the task, and escalate after one failed attempt,
not before. Anything that decides what we claim goes to Opus; anything that is already specified goes to
Sonnet.
