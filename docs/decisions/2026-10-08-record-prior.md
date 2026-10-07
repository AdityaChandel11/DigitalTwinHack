# The record as the twin's prior (section P), 8 Oct 2026

**Verdict: P1 NOT PASSED. The record made no measurable difference to the estimate.** With one day of sensor
data, giving the twin the record's fasting glucose as its prior changed the error by a median of 0.02 mg/dL
(p = 0.16). With three or more days it changed nothing. Published as registered (Amendment 3, section P).

Commands, each run once on the CGMacros test split:

```bash
python -m chhaya.eval.gate2 --dataset cgmacros --split test --k 1 3 5 7 --jobs 6 --prior record --tag ksweep-prior-record
python -m chhaya.eval.gate2 --dataset cgmacros --split test --k 1 3 5 7 --jobs 5 --prior population --tag ksweep-prior-population
python -m chhaya.eval.fusion --record results/gate2/cgmacros-test-ksweep-prior-record --population results/gate2/cgmacros-test-ksweep-prior-population
```

Provenance: both sweeps started at commit `9bd8617`; their provenance files record `d1a06b6`, the commit that
was current when they finished. No file on the Gate 2 code path changed between the two. No failed fits in
either sweep; the same 4 recording-and-k rows are skipped in both. Results: `results/fusion/`.

**Checks the plan asked for.** `results/gate2/cgmacros-test/` is unchanged. The record-prior sweep reproduces
the confirmatory Gate 2 run row by row at k = 3, 5 and 7 (largest difference in any patient's RMSE: 0.0), so
k = 5 reads 21.9 mg/dL as before.

## What "the record prior" is

One number. `record_prior` takes the record's fasting plasma glucose and sets the prior mean of one of the
twin's seven parameters (basal glucose), with a tight spread. The other six parameters keep the population
prior. The "learned record-to-parameter map" that the code comment promises was never built. Fasting insulin
enters the twin as a fixed input in both arms, so it is not part of this comparison.

## Result: RMSE against the hidden sensor, median over patients (mg/dL)

| k (days) | Patients | Estimate, record prior | Estimate, population prior | Median paired difference | Record better in | p |
|---|---|---|---|---|---|---|
| 1 | 20 | 30.32 | 30.80 | -0.022 | 65 % | 0.156 |
| 3 | 19 | 23.80 | 23.79 | -0.000 | 58 % | 0.187 |
| 5 | 19 | 21.95 | 21.67 | -0.001 | 63 % | 0.078 |
| 7 | 18 | 22.01 | 22.01 | -0.000 | 56 % | 0.351 |

**P1** (at k = 1: median paired difference below 0 and p < 0.05): difference -0.022, p = 0.156. **Missed.**

Also reported, as registered:

| k (days) | Physiology alone, record prior | Population prior | Median paired difference | Record better in | p |
|---|---|---|---|---|---|
| 1 | 29.91 | 31.99 | -0.084 | 75 % | 0.029 |
| 3 | 24.23 | 24.21 | -0.007 | 58 % | 0.113 |
| 5 | 23.27 | 23.27 | -0.007 | 63 % | 0.044 |
| 7 | 23.23 | 23.21 | -0.002 | 61 % | 0.234 |

- **The physiology alone shows the right sign and nothing of size.** Two of eight uncorrected tests fall
  below 0.05, for differences of 0.08 and 0.007 mg/dL. That is consistent in direction and of no clinical
  meaning.
- **"Sensor days the population prior needs to match the record prior at k = 1": 3.** This registered figure
  must not be read as three sensor days saved. It compares two cohort medians (30.32 against 30.80); patient
  by patient the two priors are not distinguishable at k = 1. The report prints it with that caveat.

## What the rows show (descriptive)

- At k = 1, 16 of 20 patients differ by less than 0.25 mg/dL between the two priors.
- **The record can mislead.** For one T2D patient the record prior was 10.4 mg/dL worse at k = 1 (45.6 against
  35.3). That patient's lab fasting glucose is 144 mg/dL; the sensor averaged 91 on the first day and 114 over
  the hidden days. The lab value and the first sensor day disagree by about 50 mg/dL, and with the tight
  record prior the fit ended against a bound. Why that costs 10 mg/dL was not investigated. On average over
  patients the record prior is 0.34 mg/dL *worse* at k = 1 because of that one patient; the median is 0.02
  better.
- At k = 1 the fit ends against a bound for 5 of 20 patients with the record prior and 2 of 20 with the
  population prior. A lab fasting value and a sensor baseline are different measurements, and a tight prior
  built from one fights the other.
- By k = 3 the sensor data has overwritten the prior either way.

## What it means, and what it does not

- **The Gate 2 claim does not rest on the record.** Every Gate 2 number was produced with the record prior. At
  the Gate 2 calibration lengths (k = 3, 5, 7) the population prior gives cohort medians within 0.3 mg/dL of
  them, and at k = 5 its median is the lower one (21.67 against 21.95).
- **This is a null for a thin prior, not for health records in general.** One lab value on one parameter was
  tested, on 20 patients, in a dataset whose record has no medication data. A prior that maps the whole record
  to all seven parameters was planned and not built, so it is untested. It is not being built now: it would
  be designed after seeing this result, on about 25 development patients, with two science days left.
- **Both registered fusion tests are now null.** Gate 3 (M1): fusing record, sensor week and fingersticks did
  not beat the best single stream. P1: the record as the twin's prior did not improve the estimate. Roadmap
  failure 3 named this result as "the second fusion test"; it does not rescue the first.

## Consequences

- **How fusion may be described.** The twin does fuse the two streams the brief asks for: the record sets a
  prior and the sensor data is the likelihood. What may not be said is that this fusion improves anything
  we measured. The supported sentence is: "we fused the record and the sensor two ways and measured both; once
  a sensor week exists the record added nothing detectable."
- **What does add something** is a second dynamic stream, the meal log (Gate 2: closer than the patient's
  average day, p = 4e-05, and than a control with no meals, p = 0.04).
- **The brief's adverse-event requirement** ("ingests these two streams and predicts an adverse event") is met
  by the sensor-on arm of Gate 3, which uses record, sensor week, fingersticks and live sensor: AUPRC 0.76,
  AUROC 0.82 on held-out patients. It is a baseline table, not the headline.
- **Dashboard (M4):** no "sensor days saved by the record" figure. The record screen shows the record as the
  twin's starting point and says its measured effect is nil.
- **CLAUDE.md** now says, beside "Fusion is Bayesian", that the measured effect is nil.

## The claim to quote

On 20 held-out CGMacros patients with one day of sensor data, giving the twin the record's fasting glucose as
its prior changed the error of the estimate by a median of 0.02 mg/dL (p = 0.16), and with three or more days
by nothing measurable: the record, as it enters the twin today, is not worth any sensor days.
