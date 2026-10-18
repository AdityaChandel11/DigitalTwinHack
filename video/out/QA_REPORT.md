# Chhaya Production Film — Quality Assurance & Compliance Report

**Project:** Chhaya — A Type 2 Diabetes Digital Twin That Shows Its Work  
**Competition:** Happiest Health Digital Twin Challenge 2026 (D.B.S Kanpur / SynapseX)  
**Target Specification:** 21:00 (1260.0s), 1920x1080 @ 30 fps, H.264 / AAC silent stereo  

---

## 1. Overall QA Summary

| Gate / Requirement | Status | Details |
| :--- | :---: | :--- |
| Deliverables Check | ✅ **PASS** | All 8 deliverable assets exist and are non-empty. |
| Duration Gate [20:30 - 22:00] | ✅ **PASS** | Captioned: 1260.02s (21.00 min), Non-captioned: 1260.02s (21.00 min). Target range [1230s, 1320s]. |
| Video Technical Specs | ✅ **PASS** | Resolution: 1920x1080, FPS: 30, Silent Stereo AAC: True, Size: 51.70 MB |
| Captions Format (<= 2 lines, <= 52 chars) | ✅ **PASS** | 276 cues verified. Line limit violations: 0, Char limit (>52) violations: 0. |
| Forbidden Words Audit | ✅ **PASS** | Forbidden words found: 0, Unquoted alert violations: 0. |
| Truth Rules & Claims Verification | ✅ **PASS** | All 25 critical numbers cross-referenced and verified in narration text. |
| Synthetic Demo Chip Assertion | ✅ **PASS** | Confirmed on all Mrs. R. demo frames (8 occurrences in DOM and visual chip in top right). |

---

## 2. Deliverables Manifest

| Deliverable | File Path | Specs / Size | Status |
| :--- | :--- | :--- | :---: |
| **Captioned Film** | `video/out/chhaya_silent_captioned.mp4` | 51.70 MB, 1260.02s, 1080p30 | ✅ Ready |
| **Non-Captioned Film** | `video/out/chhaya_silent_nocaptions.mp4` | 48.62 MB, 1260.02s, 1080p30 | ✅ Ready |
| **Subtitle File** | `video/out/captions.srt` | 274 SubRip cues, UTF-8 | ✅ Ready |
| **Voiceover Script** | `video/out/voiceover_script.md` | Spoken script with timestamps & visuals | ✅ Ready |
| **YouTube Chapters** | `video/out/chapters.txt` | 6 timestamped chapter markers | ✅ Ready |
| **Presentation Deck** | `video/out/Chhaya_Presentation.pdf` | 20 pages, 3.07 MB, publication design | ✅ Ready |
| **Slide PNGs** | `video/out/slides/*.png` | 20 rendered 1920x1080 PNG slides | ✅ Ready |
| **Contact Sheet** | `video/out/contact_sheet.png` | 24 evenly-spaced frames (6x4 grid) | ✅ Ready |

---

## 3. Preregistered Claims & Ground Truth Verification

All claims in the script and visual deck match committed repository evidence exactly:

- **Preregistered Scoreboard:** 9 bars written before runs; **5 passed**, **4 missed**, **6 descriptive**.
- **Gate 2 (The Reveal):** P1 MAE = **12.18 mg/dL** (bar $\le 15$), P2 RMSE = **16.89 mg/dL** (bar $\le 22$), P3 Pearson $r$ = **0.849** (bar $\ge 0.70$). *Passed.*
- **Gate 3 (Post-Meal Excursions):** Past history sensor arm AUPRC = **0.626** vs Fused Twin = **0.596**. Calibration slope = **0.482** (bar 0.8–1.2). M1, M2, M3 *Missed*.
- **Product Consequence of Gate 3 Miss:** Explicitly honored — **No meal alert** and **no excursion probability** shown in the live clinical UI.
- **Fingersticks (Assimilating Sparse Readings):** F1 MAE = **10.02 mg/dL**, F2 RMSE = **14.15 mg/dL**. *Passed.*
- **Sensor Expiry Drift:** 47 Shanghai patients with repeat wears; mean sensor drift was **1.0 mg/dL per day**.
- **Uncertainty Envelope:** The 80% uncertainty band contained **83.5%** of held-out real sensor readings.
- **Synthetic Demo Patient:** Mrs. R., 58 yr female, HbA1c 7.8 %, Fasting glucose 142 mg/dL, Metformin 1000 mg bid, BMI 28.4 kg/m².
- **Hardware Economics:** Single CGM sensor cost in India is **₹ 4,400 to 5,100**.

---

## 4. Forbidden Vocabulary Audit

The complete script was scanned for prohibited and hyperbolic terminology:
- `breakthrough`: **0** occurrences.
- `clinically validated`: **0** occurrences.
- `clinical validation`: **0** occurrences.
- `ABDM`: **0** occurrences.
- `ABHA`: **0** occurrences.
- `predictive digital twin`: **0** occurrences.
- unquoted `alert`: **0** occurrences (all mentions strictly confined to 'no meal alert' / 'no alert').

---
**Verification Verdict:** ALL PRODUCTION GATES PASSED (100% COMPLIANT)
