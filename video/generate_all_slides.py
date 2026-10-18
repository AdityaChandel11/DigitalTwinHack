"""
Generates all presentation slide HTML templates in video/slides/.
Editorial publication design adhering to docs/Architecture_SynapseX.pdf
- Warm canvas #FAFAF8
- Rich ink typography #1A1A2E
- Generous card padding, zero box clipping or overflow
- Safe 200px bottom zone for captions
"""
import os
from pathlib import Path

SLIDES_DATA = [
    # Cold Open
    {
        "filename": "slide_hook.html",
        "category": "01  PROJECT FILM OVERVIEW",
        "body": """
      <div class="hook-hero">
        <div class="hook-logo-row">
          <div class="hook-icon">छा</div>
          <div class="hook-title">Chhaya</div>
        </div>
        <div class="hook-subtitle">
          A Type 2 diabetes digital twin that shows its work.
        </div>
        <div class="hook-pills">
          <div class="hook-pill">One Sensor Wear</div>
          <div class="hook-pill">Scored on Held-Out Patients</div>
          <div class="hook-pill">Misses Published Openly</div>
        </div>
      </div>
"""
    },
    {
        "filename": "slide_team.html",
        "category": "SYNAPSEX · D.B.S KANPUR",
        "body": """
      <div class="hook-hero">
        <div class="hook-icon" style="width: 72px; height: 72px; font-size: 38px;">SX</div>
        <div class="slide-title-hero" style="font-size: 68px; margin-bottom: 12px;">Team SynapseX</div>
        <div style="font-family: var(--font-sans); font-size: 34px; font-weight: 600; color: var(--purple);">
          D.B.S. College, Kanpur
        </div>
        <div style="font-family: var(--font-mono); font-size: 20px; color: var(--text-muted); margin-top: 12px; letter-spacing: 1px;">
          Happiest Health Digital Twin Challenge 2026 · Submission SynapseX_D.B.S Kanpur
        </div>
      </div>
"""
    },
    {
        "filename": "slide_scoreboard.html",
        "category": "PREREGISTERED SCOREBOARD",
        "body": """
      <div style="text-align: center; display: flex; flex-direction: column; align-items: center;">
        <div class="slide-title-hero" style="margin-bottom: 8px;">Nine Bars Written Before the Runs</div>
        <div class="slide-title-sub" style="margin-bottom: 28px;">
          Pre-registered evaluation protocol across Gates 1, 2, and 3.
        </div>
        <div class="score-hero-row">
          <div class="score-box pass">
            <div class="score-num">5 PASSED</div>
            <div class="score-label">Gate 2 Reveal & Fingersticks</div>
          </div>
          <div class="score-box miss">
            <div class="score-num">4 MISSED</div>
            <div class="score-label">Gate 3 Excursions & Record Prior</div>
          </div>
        </div>
      </div>
"""
    },
    {
        "filename": "slide_what_changed.html",
        "category": "WHAT THE MISSES CHANGED",
        "body": """
      <div style="width: 100%;">
        <div class="slide-title-hero" style="margin-bottom: 32px;">Consequences in the Clinical Product</div>
        <div class="cards-3-row">
          <div class="card-3">
            <div class="tag-chip tag-miss">Gate 3 Missed</div>
            <div class="card-3-title">No Meal Alert</div>
            <div class="card-3-desc">No excursion probability or alert shown anywhere in the interface.</div>
          </div>
          <div class="card-3">
            <div class="tag-chip tag-miss">Record Prior Missed</div>
            <div class="card-3-title">Fusion Added Nil</div>
            <div class="card-3-desc">Health record retained strictly as background context for clinician review.</div>
          </div>
          <div class="card-3">
            <div class="tag-chip tag-teal">Plain Baseline Won</div>
            <div class="card-3-title">Plain Average Used</div>
            <div class="card-3-desc">Converted fingerstick average drives patient summary in clinical practice.</div>
          </div>
        </div>
      </div>
"""
    },

    # The Problem
    {
        "filename": "slide_bignum.html",
        "category": "THE CLINICAL PROBLEM IN INDIA",
        "body": """
      <div class="bignum-center">
        <div class="tag-chip tag-purple" style="font-size: 15px; padding: 8px 18px;">HARDWARE ECONOMICS</div>
        <div class="bignum-val accent">₹ 4,400 to 5,100</div>
        <div class="bignum-lede">The cost of a single 14-day continuous glucose sensor in India.</div>
        <div class="bignum-sub">A patient wears one once and is treated from that report for months.</div>
      </div>
"""
    },
    {
        "filename": "slide_unmeasured_gap.html",
        "category": "THE UNMEASURED GAP",
        "body": """
      <div class="hook-hero">
        <div class="slide-title-hero" style="margin-bottom: 12px;">When the Sensor Comes Off</div>
        <div class="slide-title-sub" style="font-size: 32px; max-width: 1200px; margin-bottom: 24px;">
          The clinic has a static paper report, occasional fingersticks, and a meal log.
        </div>
        <div class="hook-pills">
          <div class="hook-pill">Static Paper PDF</div>
          <div class="hook-pill">Sparse Fingersticks</div>
          <div class="hook-pill">Patient Meal Diary</div>
        </div>
      </div>
"""
    },
    {
        "filename": "slide_core_questions.html",
        "category": "CLINICAL QUESTIONS",
        "body": """
      <div style="width: 100%;">
        <div class="slide-title-hero" style="margin-bottom: 30px;">What the Clinic Needs to Know</div>
        <div class="cards-4-grid">
          <div class="card-4">
            <div class="card-4-num">01</div>
            <div class="card-4-text">How long does the report stay true?</div>
          </div>
          <div class="card-4">
            <div class="card-4-num">02</div>
            <div class="card-4-text">Which readings should you not believe?</div>
          </div>
          <div class="card-4">
            <div class="card-4-num">03</div>
            <div class="card-4-text">What keeps the shadow true?</div>
          </div>
          <div class="card-4">
            <div class="card-4-num">04</div>
            <div class="card-4-text">When does the report go stale?</div>
          </div>
        </div>
      </div>
"""
    },
    {
        "filename": "slide_protocol.html",
        "category": "THE REVEAL PROTOCOL",
        "body": """
      <div style="width: 100%;">
        <div class="slide-title-hero" style="margin-bottom: 32px;">The Reveal Protocol</div>
        <div class="protocol-row">
          <div class="protocol-card">
            <div class="protocol-step">Step 01</div>
            <div class="protocol-title">1. Calibrate</div>
            <div class="protocol-desc">Fit seven parameters on k days of sensor wear.</div>
          </div>
          <div class="protocol-card">
            <div class="protocol-step">Step 02</div>
            <div class="protocol-title">2. Hide</div>
            <div class="protocol-desc">Conceal subsequent continuous sensor data.</div>
          </div>
          <div class="protocol-card">
            <div class="protocol-step">Step 03</div>
            <div class="protocol-title">3. Estimate</div>
            <div class="protocol-desc">Project shadow using meals and fingersticks.</div>
          </div>
          <div class="protocol-card">
            <div class="protocol-step">Step 04</div>
            <div class="protocol-title">4. Reveal</div>
            <div class="protocol-desc">Overlay ground truth sensor to score error.</div>
          </div>
        </div>
      </div>
"""
    },

    # How It Was Made
    {
        "filename": "slide_datasets.html",
        "category": "DATASETS & LICENCES",
        "body": """
      <div style="width: 100%;">
        <div class="slide-title-hero" style="margin-bottom: 32px;">Open Datasets & Licenses</div>
        <div class="cards-2-row">
          <div class="card-2">
            <div class="tag-chip tag-teal">SHANGHAIT2DM  CC BY 4.0</div>
            <div class="card-2-title">100 Patients, 109 Wears</div>
            <div class="card-2-desc">Inpatient care: 15-min sensor, fingersticks, diet text, drugs, laboratory panels.</div>
          </div>
          <div class="card-2">
            <div class="tag-chip tag-purple">CGMACROS  CC BY-NC-SA 4.0</div>
            <div class="card-2-title">45 Free-Living People</div>
            <div class="card-2-desc">Libre + Dexcom sensors, Fitbit wristband, and meal macronutrients.</div>
          </div>
        </div>
      </div>
"""
    },
    {
        "filename": "slide_split.html",
        "category": "SPLIT METHODOLOGY",
        "body": """
      <div class="hook-hero">
        <div class="slide-title-hero" style="margin-bottom: 16px;">Split by Patient, Never by Row</div>
        <div style="font-family: var(--font-mono); font-size: 26px; color: var(--purple); background: var(--purple-light); border: 1px solid var(--purple-border); padding: 10px 24px; border-radius: 12px; margin-bottom: 12px;">
          chhaya.config.is_dev_patient()
        </div>
        <div class="slide-title-sub" style="font-size: 32px; max-width: 1100px;">
          Priors and parameters tuned on dev patients.<br>Held-out test patients evaluated strictly once.
        </div>
      </div>
"""
    },
    {
        "filename": "slide_architecture.html",
        "category": "ONE-WAY PIPELINE",
        "body": """
      <div style="width: 100%; text-align: center;">
        <div class="slide-title-hero" style="margin-bottom: 12px;">One-Way Data Architecture</div>
        <div class="slide-title-sub" style="margin-bottom: 30px;">
          The browser computes nothing: every curve is precomputed in static JSON bundles.
        </div>
        <div style="display: flex; gap: 14px; justify-content: center; align-items: center; max-width: 1600px; margin: 0 auto; flex-wrap: wrap;">
          <div style="background: #FFFFFF; border: 1px solid var(--line); border-radius: 12px; padding: 18px 24px; font-family: var(--font-mono); font-size: 20px; font-weight: 700;">Loader</div>
          <div style="font-size: 22px; color: var(--purple); font-weight: 700;">➔</div>
          <div style="background: var(--teal-light); border: 1px solid var(--teal-border); color: var(--teal); border-radius: 12px; padding: 18px 24px; font-family: var(--font-mono); font-size: 20px; font-weight: 700;">Recording</div>
          <div style="font-size: 22px; color: var(--purple); font-weight: 700;">➔</div>
          <div style="background: #FFFFFF; border: 1px solid var(--line); border-radius: 12px; padding: 18px 24px; font-family: var(--font-mono); font-size: 20px; font-weight: 700;">build_inputs</div>
          <div style="font-size: 22px; color: var(--purple); font-weight: 700;">➔</div>
          <div style="background: #FFFFFF; border: 1px solid var(--line); border-radius: 12px; padding: 18px 24px; font-family: var(--font-mono); font-size: 20px; font-weight: 700;">fit_twin</div>
          <div style="font-size: 22px; color: var(--purple); font-weight: 700;">➔</div>
          <div style="background: #FFFFFF; border: 1px solid var(--line); border-radius: 12px; padding: 18px 24px; font-family: var(--font-mono); font-size: 20px; font-weight: 700;">simulate_ensemble</div>
          <div style="font-size: 22px; color: var(--purple); font-weight: 700;">➔</div>
          <div style="background: var(--purple-light); border: 1px solid var(--purple-border); color: var(--purple); border-radius: 12px; padding: 18px 24px; font-family: var(--font-mono); font-size: 20px; font-weight: 700;">metrics</div>
        </div>
      </div>
"""
    },
    {
        "filename": "slide_twin_core.html",
        "category": "PHYSIOLOGICAL MODEL",
        "body": """
      <div style="width: 100%;">
        <div class="slide-title-hero" style="margin-bottom: 32px;">Personalised Physiological Model</div>
        <div class="cards-2-row">
          <div class="card-2">
            <div class="tag-chip tag-purple">EXTENDED DES IN JAX (x64)</div>
            <div class="card-2-title">ODE System at 1-Min Steps</div>
            <div class="card-2-desc">Two-compartment gut absorption, circadian dawn sinusoid, and beta-cell response.</div>
          </div>
          <div class="card-2">
            <div class="tag-chip tag-teal">BAYESIAN ESTIMATION</div>
            <div class="card-2-title">MAP Mode + Laplace Band</div>
            <div class="card-2-desc">L-BFGS-B mode fitting with Hessian curvature giving the 80% uncertainty envelope.</div>
          </div>
        </div>
      </div>
"""
    },
    {
        "filename": "slide_blend.html",
        "category": "THE BLEND",
        "body": """
      <div style="width: 100%;">
        <div class="slide-title-hero" style="margin-bottom: 12px;">Estimate = 50% Physiology + 50% Average Day</div>
        <div class="slide-title-sub" style="margin-bottom: 28px;">
          Errors are only partly correlated: the blend beats both individual models.
        </div>
        <div class="cards-2-row">
          <div class="card-2">
            <div class="tag-chip tag-purple">PHYSIOLOGY (50%)</div>
            <div class="card-2-title">Metabolic Dynamics</div>
            <div class="card-2-desc">Knows exact meal grams and timings logged today.</div>
          </div>
          <div class="card-2">
            <div class="tag-chip tag-teal">AVERAGE DAY (50%)</div>
            <div class="card-2-title">Empirical Habits</div>
            <div class="card-2-desc">Knows persistent routine habits the meal log missed.</div>
          </div>
        </div>
      </div>
"""
    },

    # Results
    {
        "filename": "slide_results_gate2.html",
        "category": "GATE 2  THE REVEAL RESULT",
        "body": """
      <div class="bignum-center">
        <div class="tag-chip tag-pass" style="font-size: 15px; padding: 8px 18px;">BARS P1, P2, P3  PASSED</div>
        <div class="bignum-val accent" style="color: var(--pass-text);">1.4 mg/dL Closer</div>
        <div class="bignum-lede">6% gain over the patient's own average day (p = 4e-05, 19 held-out patients).</div>
        <div class="bignum-sub">Advantage does not fade over 7 unmeasured days (0.4 to 2.0 mg/dL).</div>
      </div>
"""
    },
    {
        "filename": "slide_results_sticks.html",
        "category": "FINGERSTICKS EVALUATION",
        "body": """
      <div style="width: 100%;">
        <div class="slide-title-hero" style="margin-bottom: 32px;">Fingersticks Evaluation</div>
        <div class="cards-2-row">
          <div class="card-2" style="border-top: 4px solid var(--pass);">
            <div class="tag-chip tag-pass">BAR F1  PASSED</div>
            <div class="card-2-title">2.8 mg/dL Closer Live</div>
            <div class="card-2-desc">Paired RMSE difference, 95% CI 1.6 to 4.7 mg/dL, 86% of patients, p = 4e-06.</div>
          </div>
          <div class="card-2" style="border-top: 4px solid var(--pass);">
            <div class="tag-chip tag-pass">BAR F2  PASSED</div>
            <div class="card-2-title">9.5 mg/dL In Hindsight</div>
            <div class="card-2-desc">Paired difference with 95% interval 4.6 to 12.1 mg/dL on held-out patients.</div>
          </div>
        </div>
      </div>
"""
    },
    {
        "filename": "slide_results_prior.html",
        "category": "RECORD PRIOR  FUSION RESULT",
        "body": """
      <div class="bignum-center">
        <div class="tag-chip tag-miss" style="font-size: 15px; padding: 8px 18px;">BAR P1  MISSED</div>
        <div class="bignum-val" style="color: var(--miss-text);">0.02 mg/dL</div>
        <div class="bignum-lede">Giving the twin fasting glucose as prior changed error by only 0.02 mg/dL (p = 0.16).</div>
        <div class="bignum-sub">The health record is not worth any sensor days. Fusion is built and measured: it is not a gain.</div>
      </div>
"""
    },
    {
        "filename": "slide_results_ladder.html",
        "category": "GATE 3  INFORMATION LADDER",
        "body": """
      <div style="width: 100%;">
        <div class="slide-title-hero" style="margin-bottom: 24px;">Sensor History Alone Beat the Twin</div>
        <div class="ladder-row">
          <div class="ladder-card">
            <div class="tag-chip tag-neutral">RECORD ONLY</div>
            <div class="ladder-val">0.566</div>
            <div class="ladder-sub">AUPRC</div>
          </div>
          <div class="ladder-card winner">
            <div class="tag-chip tag-teal">SENSOR HISTORY</div>
            <div class="ladder-val">0.626</div>
            <div class="ladder-sub">AUPRC (Winner)</div>
          </div>
          <div class="ladder-card">
            <div class="tag-chip tag-purple">FINGERSTICKS</div>
            <div class="ladder-val">0.642</div>
            <div class="ladder-sub">AUPRC</div>
          </div>
          <div class="ladder-card missed">
            <div class="tag-chip tag-miss">FUSED TWIN</div>
            <div class="ladder-val">0.596</div>
            <div class="ladder-sub">AUPRC (Missed)</div>
          </div>
        </div>
        <div class="ladder-footer-note">
          Calibration slope 0.482 vs target 0.8–1.2. Result: no meal alerts in the product.
        </div>
      </div>
"""
    },
    {
        "filename": "slide_results_baselines.html",
        "category": "EMPIRICAL TRUTH",
        "body": """
      <div style="width: 100%;">
        <div class="slide-title-hero" style="margin-bottom: 32px;">Empirical Truth & Baselines</div>
        <div class="cards-2-row">
          <div class="card-2">
            <div class="tag-chip tag-teal">REPORT LEVEL AVERAGE</div>
            <div class="card-2-title">6.4 vs 8.9 mg/dL</div>
            <div class="card-2-desc">Plain converted fingerstick average was closer than our twin in hindsight. Plain average is used.</div>
          </div>
          <div class="card-2">
            <div class="tag-chip tag-purple">STALENESS DRIFT PROMPT</div>
            <div class="card-2-title">AUROC 0.82 vs 0.82</div>
            <div class="card-2-desc">Cumulative surprise sum tied plain fingerstick average vs report (difference 0.00).</div>
          </div>
        </div>
      </div>
"""
    },

    # Limits & Close
    {
        "filename": "slide_limits.html",
        "category": "WHAT CHHAYA IS NOT",
        "body": """
      <div style="width: 100%;">
        <div class="slide-title-hero" style="margin-bottom: 30px;">Explicit Scientific Boundaries</div>
        <div class="cards-4-grid">
          <div class="card-4">
            <div class="card-4-num">01</div>
            <div class="card-4-text">No Indian patient dataset (Shanghai & US cohorts).</div>
          </div>
          <div class="card-4">
            <div class="card-4-num">02</div>
            <div class="card-4-text">Supervised inpatient care data.</div>
          </div>
          <div class="card-4">
            <div class="card-4-num">03</div>
            <div class="card-4-text">Hidden unmeasured windows at most 11 days.</div>
          </div>
          <div class="card-4">
            <div class="card-4-num">04</div>
            <div class="card-4-text">Physiology model advantage is ~2% over baseline.</div>
          </div>
        </div>
      </div>
"""
    },
    {
        "filename": "slide_close.html",
        "category": "TRY THE LIVE SYSTEM",
        "body": """
      <div class="hook-hero">
        <div class="hook-icon" style="width: 80px; height: 80px; font-size: 44px;">छा</div>
        <div class="slide-title-hero" style="font-size: 64px; margin-bottom: 8px;">Chhaya</div>
        <div style="font-family: var(--font-mono); font-size: 32px; font-weight: 700; color: var(--purple); background: var(--purple-light); border: 1px solid var(--purple-border); padding: 12px 36px; border-radius: 16px; margin: 10px 0;">
          chhaya-digital-twin.vercel.app
        </div>
        <div class="slide-title-sub" style="font-size: 26px; max-width: 1100px;">
          Code, tests, and decision records public on GitHub · Team SynapseX · D.B.S Kanpur
        </div>
      </div>
"""
    }
]

def generate():
    out_dir = Path("video/slides")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    for item in SLIDES_DATA:
        fn = item["filename"]
        cat = item["category"]
        body = item["body"]
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{fn}</title>
  <link rel="stylesheet" href="theme.css">
</head>
<body>
  <div class="slide">
    <div class="slide-header">
      <div class="header-brand">
        <div class="logo-badge">छा</div>
        <div class="brand-text">Chhaya</div>
        <div class="category-chip">{cat}</div>
      </div>
      <div class="team-badge">Team SynapseX · D.B.S Kanpur · Digital Twin Challenge 2026</div>
    </div>
    
    <div class="slide-body">
{body}
    </div>

    <div class="caption-bar" id="caption-bar" style="display: none;">
      <div class="caption-text" id="caption-text"></div>
    </div>
  </div>
</body>
</html>
"""
        with open(out_dir / fn, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Generated {fn}")

if __name__ == "__main__":
    generate()
