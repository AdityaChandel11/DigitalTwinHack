"""
Render publication-grade Problem Statement and Healthcare Use Case PDF:
  - docs/Chhaya_Problem_and_Use_Case.pdf
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"
OUT_PDF = DOCS_DIR / "Chhaya_Problem_and_Use_Case.pdf"

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Chhaya — Problem Statement & Healthcare Use Case</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&display=swap');

  @page {
    size: A4 portrait;
    margin: 10mm 12mm 10mm 12mm;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: #ffffff;
    color: #15141f;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 8.8pt;
    line-height: 1.42;
    -webkit-font-smoothing: antialiased;
  }

  .container {
    max-width: 100%;
    margin: 0 auto;
  }

  /* Header */
  .header {
    border-bottom: 2px solid #15141f;
    padding-bottom: 8px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }

  .brand-title {
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 23pt;
    font-weight: 700;
    line-height: 1.1;
    color: #15141f;
  }

  .brand-subtitle {
    font-size: 10.5pt;
    color: #4a3aa7;
    font-weight: 600;
    margin-top: 1px;
  }

  .meta-box {
    text-align: right;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 7.2pt;
    color: #4b4a5e;
    line-height: 1.35;
  }

  /* Section Styling */
  .section {
    margin-bottom: 9px;
  }

  .section-header {
    font-family: 'JetBrains Mono', monospace;
    font-size: 7.5pt;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #4a3aa7;
    margin-bottom: 3px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .section-header::after {
    content: "";
    flex: 1;
    height: 1px;
    background: #e6e6ee;
  }

  .section-title {
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 12.5pt;
    font-weight: 700;
    color: #15141f;
    margin-bottom: 4px;
  }

  p {
    margin-bottom: 4px;
    text-align: justify;
    color: #2c2b3d;
  }

  /* Stat cards */
  .grid-4 {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 7px;
    margin: 6px 0;
  }

  .stat-card {
    background: #f8f8fb;
    border: 1px solid #e6e6ee;
    padding: 6px 8px;
    border-radius: 4px;
  }

  .stat-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 6.5pt;
    color: #6b6a80;
    text-transform: uppercase;
    font-weight: 600;
  }

  .stat-value {
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 13pt;
    font-weight: 700;
    color: #15141f;
    margin: 1px 0;
  }

  .stat-desc {
    font-size: 6.8pt;
    color: #4b4a5e;
    line-height: 1.2;
  }

  /* Callout box */
  .callout-box {
    background: #f8f8fb;
    border: 1px solid #e6e6ee;
    border-left: 3.5px solid #4a3aa7;
    padding: 7px 10px;
    border-radius: 3px;
    margin: 6px 0;
    font-size: 8.5pt;
  }

  .callout-box.teal {
    border-left-color: #0e9aa7;
    background: rgba(14, 154, 167, 0.04);
  }

  .bullet-list {
    margin-left: 14px;
    margin-bottom: 4px;
  }

  .bullet-list li {
    margin-bottom: 2px;
    color: #2c2b3d;
  }

  /* Copy box */
  .copy-box {
    background: #f4f4f8;
    border: 1px dashed #b5a9ff;
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 8.4pt;
    line-height: 1.38;
    color: #15141f;
    margin: 4px 0;
  }

  /* Footer */
  .footer {
    border-top: 1px solid #e6e6ee;
    padding-top: 6px;
    margin-top: 8px;
    display: flex;
    justify-content: space-between;
    font-size: 7.2pt;
    color: #6b6a80;
    font-family: 'JetBrains Mono', monospace;
  }
</style>
</head>
<body>

<div class="container">

  <!-- Header -->
  <div class="header">
    <div>
      <div class="brand-title">Chhaya</div>
      <div class="brand-subtitle">Problem Statement &amp; Healthcare Use Case</div>
    </div>
    <div class="meta-box">
      <strong>HAPPIEST HEALTH DIGITAL TWIN CHALLENGE 2026</strong><br>
      Team: <strong>SynapseX</strong> (Solo Entry · Aditya Singh Chandel)<br>
      College: <strong>D.B.S. College, Kanpur</strong> (SynapseX_D.B.S Kanpur)<br>
      Status: Official Submission Deliverable
    </div>
  </div>

  <!-- 1. Problem Statement -->
  <div class="section">
    <div class="section-header">01 · Clinical Context &amp; Epidemiological Need</div>
    <div class="section-title">Problem Statement</div>
    
    <p>
      About 101 million people in India live with diabetes (ICMR-INDIAB, 2023). Continuous glucose monitoring could guide their care, but one 14-day sensor costs roughly Rs 4,400 to 5,100. Wearing sensors all year would take about 26 of them, over Rs 1.1 lakh. So for many patients a sensor is worn once, a report is made, and the doctor treats from that report for months. Nobody tells the doctor how old the report has become, which of its readings not to believe, or what the patient’s glucose probably did after the sensor came off.
    </p>

    <!-- Key Metrics Strip -->
    <div class="grid-4">
      <div class="stat-card">
        <div class="stat-label">Diabetic Burden</div>
        <div class="stat-value">101 Million</div>
        <div class="stat-desc">+136M prediabetes; 2nd highest in world (ICMR-INDIAB)</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">14-Day Sensor Cost</div>
        <div class="stat-value">₹4,400–5,100</div>
        <div class="stat-desc">Single-use disposables; 100% out-of-pocket for families</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Full Annual Wear</div>
        <div class="stat-value">&gt; ₹1.1 Lakh</div>
        <div class="stat-desc">26 sensors/yr; financially out of reach for &gt;95% households</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">The Clinical Blind Spot</div>
        <div class="stat-value">351 Days</div>
        <div class="stat-desc">Over 96% of year unmonitored; doctors treat from stale reports</div>
      </div>
    </div>

    <p style="margin-top: 6px;">
      Given a health record and one sensor wear, Chhaya <strong>(1)</strong> estimates the patient’s glucose after the sensor is removed, with an honest uncertainty band, <strong>(2)</strong> labels sensor lows that a fingerstick did not confirm, <strong>(3)</strong> prompts when the report has probably stopped describing the patient, and <strong>(4)</strong> proves every claim on patients the model never saw.
    </p>
  </div>

  <!-- 2. Healthcare Use Case -->
  <div class="section">
    <div class="section-header">02 · Clinical Delivery &amp; Operational Workflow</div>
    <div class="section-title">Healthcare Use Case</div>
    
    <p>
      The setting is outpatient follow-up of Type 2 diabetes, where the doctor holds a one-time sensor report and occasional fingersticks. The user is the treating clinician. The decision supported is whether the existing sensor report can still be relied on, or whether to consider a new sensor wear.
    </p>

    <div class="callout-box teal">
      <strong>This is “proactive, not reactive” scoped to what we measured. On the dashboard the doctor sees:</strong>
      <ul class="bullet-list" style="margin-top: 4px;">
        <li><strong>The patient’s shadow:</strong> an estimate with an 80% credible band drawn without the sensor, with the real sensor revealed on top;</li>
        <li><strong>Fingerstick-updated estimates:</strong> running Bayesian innovation updates and the health record that sets the twin’s prior;</li>
        <li><strong>The patient’s own meal-excursion history:</strong> empirical risk patterns during the calibration wear;</li>
        <li><strong>Scientific integrity ledger:</strong> every result displayed directly beside the bar written before it was run.</li>
      </ul>
      <div style="font-family: 'JetBrains Mono', monospace; font-size: 7.8pt; color: #b3311f; font-weight: 700; margin-top: 4px;">
        SAFE CLINICAL RESTRAINT: Chhaya gives no dose advice, no low-glucose estimate, and no automated alarm.
      </div>
    </div>
  </div>

  <!-- 3. What it does today -->
  <div class="section">
    <div class="section-header">03 · Verified Outcomes on Held-Out Patients</div>
    <div class="section-title">What It Does Today</div>
    
    <p>
      <strong>What it does today:</strong> Scored once on held-out patients against bars written beforehand, the estimate was <strong>1.4 mg/dL closer</strong> to the hidden sensor than the patient’s own average day, five days after the sensor came off (19 CGMacros participants, 7 with type 2 diabetes, p = 4e-05). Fingersticks brought it <strong>2.8 mg/dL closer</strong> (29 Shanghai patients in supervised care, about six fingersticks a day). Of nine pre-registered bars, five passed and four missed, and all nine are published. The evidence comes from a Chinese and a US cohort; no Indian patient data was used. This is a research prototype, not for dosing.
    </p>
  </div>

  <!-- 4. Short Version for Character-Limited Submissions -->
  <div class="section">
    <div class="section-header">04 · Executive Summary for Portal Entry</div>
    <div style="display: flex; justify-content: space-between; align-items: baseline;">
      <div class="section-title">Short Version (If There’s a Character Limit)</div>
      <div style="font-family: 'JetBrains Mono', monospace; font-size: 7.2pt; color: #6b6a80;">68 words · 495 characters</div>
    </div>
    
    <div class="copy-box">
      “101 million Indians live with diabetes, but a 14-day glucose sensor costs about Rs 4,400 to 5,100, so most patients wear one once and are treated from that report for months. Chhaya, a Type 2 diabetes digital twin, turns that one wear into a continuing estimate with an honest uncertainty band, labels unconfirmed sensor lows, and prompts the doctor when the report has probably gone stale. Every claim was scored once on held-out patients, and all nine pre-registered bars, passed and missed, are published.”
    </div>
  </div>

  <!-- 5. Verification Notes & Official Links -->
  <div class="section" style="margin-bottom: 0;">
    <div class="callout-box" style="padding: 6px 10px; font-size: 8pt; margin: 4px 0;">
      <strong>Retail Price Verification Note:</strong> Sensor prices checked October 2026. Abbott FreeStyle Libre 1: MRP ₹4,671 / selling ₹4,437 on Truemeds. FreeStyle Libre 2: ₹4,624 to ₹5,138 in Amazon India price history. Used consistently across presentation deck, architecture, and video walkthrough.
    </div>
  </div>

  <!-- Footer -->
  <div class="footer">
    <div>Repository: github.com/AdityaChandel11/DigitalTwinHack</div>
    <div>Live Demo: digital-twin-hack.vercel.app</div>
    <div>Walkthrough Video: youtu.be/TOn2xY_z5L8</div>
  </div>

</div>

</body>
</html>
"""

async def render_pdf():
    print(f"Rendering Problem Statement & Healthcare Use Case PDF to {OUT_PDF}...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(HTML_CONTENT, wait_until="networkidle")
        await page.evaluate("document.fonts.ready")
        
        await page.pdf(
            path=str(OUT_PDF),
            format="A4",
            print_background=True,
            margin={"top": "12mm", "right": "12mm", "bottom": "12mm", "left": "12mm"}
        )
        await browser.close()
    print(f"Successfully generated: {OUT_PDF} ({OUT_PDF.stat().st_size} bytes)")

def main():
    asyncio.run(render_pdf())

if __name__ == "__main__":
    main()
