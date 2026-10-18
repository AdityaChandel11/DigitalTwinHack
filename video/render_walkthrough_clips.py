"""
Renders all Live Walkthrough segments (S056-S149) plus Cold Open S001-S008 (nocap & cap):
- video/out/clips/<id>.mp4 (with burned-in captions)
- video/out/clips_nocap/<id>.mp4 (without captions)
Uses Playwright dynamic bounding boxes on natural semantic card containers with 12px padding.
Eliminates text clipping and harsh blackout shadows.
Uses ThreadPoolExecutor for fast parallel FFmpeg encoding.
"""
import os
import sys
import json
import time
import asyncio
import argparse
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from playwright.async_api import async_playwright
import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

BASE_DIR = Path(__file__).resolve().parent
STORYBOARD_FILE = BASE_DIR / "storyboard.json"
SLIDES_DIR = BASE_DIR / "slides"
OUT_DIR = BASE_DIR / "out"
CLIPS_CAP_DIR = OUT_DIR / "clips"
CLIPS_NOCAP_DIR = OUT_DIR / "clips_nocap"
FRAMES_DIR = OUT_DIR / "frames"

CLIPS_CAP_DIR.mkdir(parents=True, exist_ok=True)
CLIPS_NOCAP_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BASE_DIR))
from capture import INJECT_JS

def encode_single_clip(frame_png, duration_sec, output_mp4, force=False):
    if not force and output_mp4.exists() and output_mp4.stat().st_size > 10000:
        return output_mp4
        
    cmd = [
        FFMPEG_EXE, "-y",
        "-loop", "1", "-i", str(frame_png),
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-c:v", "libx264",
        "-t", f"{duration_sec:.2f}",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-crf", "18",
        "-c:a", "aac",
        "-shortest",
        str(output_mp4)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg failed for {output_mp4}: {res.stderr}")
    return output_mp4

async def setup_page(browser):
    page = await browser.new_page(viewport={"width": 1920, "height": 1080})
    page.set_default_navigation_timeout(60000)
    wrapper_url = (SLIDES_DIR / "live_wrapper.html").resolve().as_uri()
    await page.goto(wrapper_url, wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_selector("#live-frame", timeout=30000)
    await page.wait_for_timeout(2000)
    await page.evaluate(INJECT_JS)
    fl = page.frame_locator("#live-frame")
    try:
        await fl.locator("body").evaluate("el => el.style.paddingBottom = '500px'")
    except Exception:
        pass
    return page

async def set_wrapper_header(page, url_text, tag_text):
    await page.evaluate(f"""
        (() => {{
            const u = document.getElementById('browser-url');
            if (u) u.textContent = {json.dumps(url_text)};
            const t = document.getElementById('browser-tag');
            if (t) t.textContent = {json.dumps(tag_text)};
        }})()
    """)

async def highlight_clean_card(page, selector, pin_num, pin_text, pad=16, scroll_block="nearest"):
    fl = page.frame_locator("#live-frame")
    el = fl.locator(selector).first
    if await el.count() == 0:
        await page.evaluate("window.__hideSpotlight()")
        return
        
    try:
        if selector == "#hero-chart":
            await fl.locator(".hero").first.scroll_into_view_if_needed()
            await page.wait_for_timeout(200)
        else:
            await el.evaluate("""el => {
                const rect = el.getBoundingClientRect();
                const headerH = 100;
                const delta = rect.top - (headerH + 20);
                window.scrollBy({ top: delta, behavior: 'instant' });
            }""")
            await page.wait_for_timeout(200)
    except Exception:
        pass
    
    box = await el.bounding_box()
    if not box:
        await page.evaluate("window.__hideSpotlight()")
        return
        
    iframe = page.locator("#live-frame")
    if_box = await iframe.bounding_box() or {"x": 100, "y": 125, "width": 1720, "height": 706}
    
    x = max(if_box["x"] + 8, box["x"] - pad)
    y = max(if_box["y"] + 8, box["y"] - pad)
    avail_w = (if_box["x"] + if_box["width"] - 8) - x
    avail_h = (if_box["y"] + if_box["height"] - 8) - y
    w = min(avail_w, box["width"] + pad * 2)
    h = min(avail_h, box["height"] + pad * 2)
    
    cx = x + w / 2
    cy = y + h / 2
    
    await page.evaluate(f"""
        window.__showSpotlight({x}, {y}, {w}, {h}, {json.dumps(str(pin_num))}, {json.dumps(str(pin_text))});
        window.__moveCursor({cx}, {cy});
    """)

async def capture_current_state(page, sid, cap, sec, encode_tasks, force=False):
    out_cap = CLIPS_CAP_DIR / f"{sid}.mp4"
    out_nocap = CLIPS_NOCAP_DIR / f"{sid}.mp4"
    
    cap_png = FRAMES_DIR / f"{sid}_cap.png"
    nocap_png = FRAMES_DIR / f"{sid}_nocap.png"
    
    # 1. No-caption frame
    if force or not nocap_png.exists() or not out_nocap.exists() or out_nocap.stat().st_size < 10000:
        await page.evaluate("""
            (() => {
                const b = document.getElementById('live-caption-bar') || document.querySelector('.caption-bar');
                if (b) b.style.display = 'none';
            })()
        """)
        await page.screenshot(path=str(nocap_png))
        
    # 2. Captioned frame
    if force or not cap_png.exists() or not out_cap.exists() or out_cap.stat().st_size < 10000:
        await page.evaluate(f"""
            (() => {{
                const b = document.getElementById('live-caption-bar') || document.querySelector('.caption-bar');
                const t = document.getElementById('caption-label');
                if (b && t) {{
                    t.textContent = {json.dumps(cap)};
                    b.style.display = 'flex';
                }}
            }})()
        """)
        await page.screenshot(path=str(cap_png))
        
    encode_tasks.append((cap_png, sec, out_cap))
    encode_tasks.append((nocap_png, sec, out_nocap))

async def run_walkthrough_capture(force=False):
    with open(STORYBOARD_FILE, "r", encoding="utf-8") as f:
        sb = json.load(f)
        
    cold_site = [s for s in sb if s["chapter"] == "Cold Open" and s["visual"].startswith("SITE:")]
    walk_site = [s for s in sb if s["chapter"] == "Live Walkthrough"]
    
    print(f"Cold open site segments: {len(cold_site)}")
    print(f"Live walkthrough segments: {len(walk_site)}")
    print(f"Force re-render: {force}")
    
    encode_tasks = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await setup_page(browser)
        fl = page.frame_locator("#live-frame")
        
        # ----------------------------------------------------
        # PART A: Cold Open site segments (S001 - S008)
        # ----------------------------------------------------
        print("\n--- Capturing Cold Open site segments ---")
        for s in cold_site:
            sid = s["id"]
            cap = s["caption"]
            sec = s["seconds"]
            
            if sid in ["S001", "S002"]:
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(960, 500)")
            elif sid == "S003":
                await highlight_clean_card(page, "#hero-chart", "1", "Estimated Glucose")
            elif sid == "S004":
                await highlight_clean_card(page, "#hero-chart", "2", "80% Uncertainty Band")
            elif sid == "S005":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(1500, 280)")
            elif sid == "S006":
                reveal_btn = fl.locator("#reveal-btn")
                if await reveal_btn.count() > 0:
                    await reveal_btn.click()
                await page.wait_for_timeout(600)
                await page.evaluate("window.__moveCursor(1500, 280)")
            elif sid == "S007":
                await highlight_clean_card(page, "#hero-chart", "3", "Real Sensor Overlay")
            elif sid == "S008":
                await page.evaluate("window.__hideSpotlight()")
                scrubber = fl.locator("#reveal-range")
                if await scrubber.count() > 0:
                    await scrubber.evaluate("r => { r.value = 65; r.dispatchEvent(new Event('input')); }")
                await page.wait_for_timeout(400)
                
            await capture_current_state(page, sid, cap, sec, encode_tasks, force=force)
            print(f"  [Cold Open] Processed {sid}")
            
        # ----------------------------------------------------
        # PART B: Live Walkthrough (S056 - S149)
        # ----------------------------------------------------
        print("\n--- Capturing Live Walkthrough segments (S056 - S149) ---")
        
        # 1. Clinic view (S056 - S060)
        await set_wrapper_header(page, "🔒 https://chhaya-digital-twin.vercel.app/#clinic", "Held-out clinic roster")
        await fl.locator('a[data-view="clinic"]').click()
        await fl.locator('table').first.wait_for(timeout=10000)
        await page.wait_for_timeout(400)
        
        for s in walk_site[:5]: # S056 - S060
            sid = s["id"]
            cap = s["caption"]
            sec = s["seconds"]
            
            if sid == "S056":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(960, 450)")
            elif sid == "S057":
                await highlight_clean_card(page, "table thead", "1", "Roster Columns")
            elif sid == "S058":
                await highlight_clean_card(page, "table tbody tr:first-child", "2", "Patient Cohorts")
            elif sid == "S059":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(700, 335)")
            elif sid == "S060":
                await highlight_clean_card(page, 'tr[data-id="mrs-r"]', "3", "Synthetic Demo Patient")
                
            await capture_current_state(page, sid, cap, sec, encode_tasks, force=force)
            print(f"  [Clinic] Processed {sid}")
            
        # 2. Open Mrs. R. & Health Record (S061 - S073)
        await set_wrapper_header(page, "🔒 https://chhaya-digital-twin.vercel.app/#p-mrs-r", "Synthetic demo patient")
        await fl.locator('a[data-view="patient"]').click()
        await fl.locator('.summary').first.wait_for(timeout=10000)
        await page.wait_for_timeout(400)
        
        synth_cnt = await fl.locator("text=Synthetic").count()
        print(f"  --> Verified 'Synthetic' tag present ({synth_cnt} occurrences).")
        
        for s in walk_site[5:18]: # S061 - S073
            sid = s["id"]
            cap = s["caption"]
            sec = s["seconds"]
            
            if sid == "S061":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(700, 335); window.__clickRipple(700, 335)")
            elif sid == "S062":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(960, 250)")
            elif sid == "S063":
                await highlight_clean_card(page, ".summary", "1", "Synthetic Patient Demo")
            elif sid == "S064":
                await highlight_clean_card(page, ".summary", "2", "Sensor & Wear Summary")
            elif sid == "S065":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(960, 250)")
            elif sid == "S066":
                await highlight_clean_card(page, "#record-panel", "1", "Health Record Panel")
            elif sid == "S067":
                await highlight_clean_card(page, "#record-panel", "1", "Demographics & Diagnosis")
            elif sid == "S068":
                await highlight_clean_card(page, "#record-panel", "2", "Glycemic Baselines")
            elif sid == "S069":
                await highlight_clean_card(page, "#record-panel", "3", "Treatment & BMI")
            elif sid == "S070":
                await highlight_clean_card(page, "#record-panel", "4", "Lifestyle Context")
            elif sid == "S071":
                await highlight_clean_card(page, "#record-panel", "5", "Renal Function")
            elif sid == "S072":
                await highlight_clean_card(page, "#record-panel", "6", "Lipid Panel")
            elif sid == "S073":
                await highlight_clean_card(page, "#record-panel", "7", "Record Prior Note")
                
            await capture_current_state(page, sid, cap, sec, encode_tasks, force=force)
            print(f"  [Mrs R Header & Record] Processed {sid}")
            
        # 3. Chart area & Reveal (S074 - S088)
        # Scroll the hero section cleanly into start view so the full chart, controls and legend are visible
        await fl.locator(".hero").first.evaluate("el => el.scrollIntoView({block: 'start', behavior: 'instant'})")
        await page.wait_for_timeout(300)
        
        for s in walk_site[18:33]: # S074 - S088
            sid = s["id"]
            cap = s["caption"]
            sec = s["seconds"]
            
            if sid == "S074":
                await highlight_clean_card(page, "#hero-chart", "1", "Days 1-3 Calibration")
            elif sid == "S075":
                await highlight_clean_card(page, "#hero-chart", "2", "Days 4-9 Sensor Removed")
            elif sid == "S076":
                await highlight_clean_card(page, "#hero-chart", "1", "Running Estimate")
            elif sid == "S077":
                await highlight_clean_card(page, "#hero-chart", "2", "80% Uncertainty Band")
            elif sid == "S078":
                # Meal log markers along bottom axis of chart: highlight entire chart card, move cursor to bottom axis
                await highlight_clean_card(page, "#hero-chart", "3", "Meal Log Markers")
                box = await fl.locator("#hero-chart").bounding_box()
                if box:
                    await page.evaluate(f"window.__moveCursor({box['x'] + box['width']/2}, {box['y'] + box['height'] - 30})")
            elif sid == "S079":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(850, 400)")
            elif sid == "S080":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(1500, 280)")
            elif sid == "S081":
                await page.evaluate("window.__clickRipple(1500, 280)")
                reveal_btn = fl.locator("#reveal-btn")
                if await reveal_btn.count() > 0:
                    await reveal_btn.click()
                await page.wait_for_timeout(600)
            elif sid == "S082":
                await highlight_clean_card(page, "#hero-chart", "1", "Real Sensor Overlay")
            elif sid == "S083":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(600, 530)")
            elif sid == "S084":
                await fl.locator("#reveal-range").evaluate("r => { r.value = 40; r.dispatchEvent(new Event('input')); }")
                await page.wait_for_timeout(300)
                await page.evaluate("window.__moveCursor(700, 530)")
            elif sid == "S085":
                await fl.locator("#reveal-range").evaluate("r => { r.value = 55; r.dispatchEvent(new Event('input')); }")
                await page.wait_for_timeout(300)
                await highlight_clean_card(page, "#hero-chart", "1", "Day 5 Peak Match")
            elif sid == "S086":
                await page.evaluate("window.__hideSpotlight()")
                await fl.locator("#reveal-range").evaluate("r => { r.value = 75; r.dispatchEvent(new Event('input')); }")
                await page.wait_for_timeout(300)
                await page.evaluate("window.__moveCursor(1000, 530)")
            elif sid == "S087":
                await fl.locator("#reveal-range").evaluate("r => { r.value = 90; r.dispatchEvent(new Event('input')); }")
                await page.wait_for_timeout(300)
                await page.evaluate("window.__moveCursor(1200, 530)")
            elif sid == "S088":
                await highlight_clean_card(page, "#hero-chart", "1", "Error & Coverage")
                
            await capture_current_state(page, sid, cap, sec, encode_tasks, force=force)
            print(f"  [Chart & Reveal] Processed {sid}")
            
        # 4. Fingersticks & Staleness Prompt (S089 - S099)
        for s in walk_site[33:44]: # S089 - S099
            sid = s["id"]
            cap = s["caption"]
            sec = s["seconds"]
            
            if sid == "S089":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(720, 380)")
            elif sid == "S090":
                await highlight_clean_card(page, "#hero-chart", "1", "Fingerstick Check")
            elif sid == "S091":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(770, 400)")
            elif sid == "S092":
                await highlight_clean_card(page, "#hero-chart", "1", "Band Narrows")
            elif sid == "S093":
                await highlight_clean_card(page, "#hero-chart", "2", "Widening Uncertainty")
            elif sid == "S094":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(550, 280)")
                day_btn = fl.locator("#day-seg button").nth(5)
                if await day_btn.count() > 0:
                    await day_btn.click()
                await page.wait_for_timeout(400)
            elif sid == "S095":
                await highlight_clean_card(page, "#day-seg", "1", "Day 6 Prompt")
            elif sid == "S096":
                await page.evaluate("window.__clickRipple(450, 590)")
                await page.wait_for_timeout(300)
            elif sid == "S097":
                await highlight_clean_card(page, "#day-seg", "2", "10% False Alarm Threshold")
            elif sid == "S098":
                await highlight_clean_card(page, "#day-seg", "3", "Not Advice / Diagnosis")
            elif sid == "S099":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(500, 600)")
                
            await capture_current_state(page, sid, cap, sec, encode_tasks, force=force)
            print(f"  [Fingersticks & Prompt] Processed {sid}")
            
        # 5. Meal Excursions & What-If Simulator (S100 - S113)
        await fl.locator(".wi-ctl, #wi-chart").first.evaluate("el => el.scrollIntoView({block: 'center', behavior: 'instant'})")
        await page.wait_for_timeout(400)
        
        for s in walk_site[44:58]: # S100 - S113
            sid = s["id"]
            cap = s["caption"]
            sec = s["seconds"]
            
            if sid == "S100":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(960, 450)")
            elif sid == "S101":
                await highlight_clean_card(page, ".wi-ctl", "1", "Observed Meals")
            elif sid == "S102":
                await highlight_clean_card(page, ".wi-ctl", "1", "Breakfast 45g -> 48 mg/dL")
            elif sid == "S103":
                await highlight_clean_card(page, ".wi-ctl", "2", "Dinner 70g -> 68 mg/dL")
            elif sid == "S104":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(960, 450)")
            elif sid == "S105":
                await highlight_clean_card(page, "#wi-chart", "1", "Meal What-If Simulator")
            elif sid == "S106":
                await fl.locator("#wi-range").evaluate("r => { r.value = 60; r.dispatchEvent(new Event('input')); }")
                await page.wait_for_timeout(300)
                await highlight_clean_card(page, "#wi-range", "1", "Input: 60g Carbs")
            elif sid == "S107":
                await page.evaluate("window.__clickRipple(1050, 430)")
            elif sid == "S108":
                await highlight_clean_card(page, "#wi-chart", "2", "Simulated Trajectory")
            elif sid == "S109":
                await highlight_clean_card(page, "#wi-chart", "1", "Simulation Only Badge")
            elif sid == "S110":
                await highlight_clean_card(page, "#wi-chart", "2", "Not Advice / Prediction")
            elif sid == "S111":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(1100, 450)")
            elif sid == "S112":
                await fl.locator("#wi-range").evaluate("r => { r.value = 30; r.dispatchEvent(new Event('input')); }")
                await page.wait_for_timeout(300)
                await highlight_clean_card(page, "#wi-range", "1", "Compare: 30g Carbs")
            elif sid == "S113":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(960, 450)")
                
            await capture_current_state(page, sid, cap, sec, encode_tasks, force=force)
            print(f"  [What-If Simulator] Processed {sid}")
            
        # 6. Health Record Modal (S114 - S118)
        for s in walk_site[58:63]: # S114 - S118
            sid = s["id"]
            cap = s["caption"]
            sec = s["seconds"]
            
            if sid == "S114":
                await fl.locator("body").evaluate("() => window.scrollTo(0, 0)")
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(1400, 220)")
            elif sid == "S115":
                await highlight_clean_card(page, "#record-panel", "1", "Structured Health Record")
            elif sid == "S116":
                await highlight_clean_card(page, "#record-panel", "2", "Lab Tests & Renal Panel")
            elif sid == "S117":
                await highlight_clean_card(page, "#record-panel", "3", "Provenance: Synthetic")
            elif sid == "S118":
                await fl.locator("body").evaluate("() => window.scrollTo(0, 0)")
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(960, 250)")
                
            await capture_current_state(page, sid, cap, sec, encode_tasks, force=force)
            print(f"  [Health Record Modal] Processed {sid}")
            
        # 7. Evidence Screen (S119 - S134)
        await set_wrapper_header(page, "🔒 https://chhaya-digital-twin.vercel.app/#evidence", "Preregistered Evidence Tally")
        await fl.locator('a[data-view="evidence"]').click()
        await fl.locator("#ev-gate3").first.wait_for(timeout=10000)
        await page.wait_for_timeout(400)
        
        for s in walk_site[63:79]: # S119 - S134
            sid = s["id"]
            cap = s["caption"]
            sec = s["seconds"]
            
            if sid == "S119":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(820, 80); window.__clickRipple(820, 80)")
            elif sid == "S120":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(960, 300)")
            elif sid == "S121":
                await highlight_clean_card(page, "section:first-of-type", "1", "Preregistered Scoreboard")
            elif sid == "S122":
                await highlight_clean_card(page, "section:first-of-type", "2", "5 Passed  4 Missed")
            elif sid == "S123":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(960, 450)")
            elif sid == "S124":
                await highlight_clean_card(page, "#ev-gate3", "1", "Gate 3 Card")
            elif sid == "S125":
                await page.evaluate("window.__clickRipple(450, 380)")
            elif sid == "S126":
                await highlight_clean_card(page, "#ev-gate3", "1", "Missed Bars: M1, M2, M3")
            elif sid == "S127":
                await highlight_clean_card(page, "#ev-gate3", "2", "AUPRC Information Ladder")
            elif sid == "S128":
                await highlight_clean_card(page, "#ev-gate3", "3", "History 0.626 vs Fused 0.596")
            elif sid == "S129":
                await highlight_clean_card(page, "#ev-gate3", "4", "Calibration Slope 0.482")
            elif sid == "S130":
                await highlight_clean_card(page, "#ev-gate3", "5", "Clinical Consequence")
            elif sid == "S131":
                await highlight_clean_card(page, "#ev-gate3", "6", "No Meal Alert In Product")
            elif sid == "S132":
                await highlight_clean_card(page, "#ev-expiry", "1", "Expiry Analysis Card")
            elif sid == "S133":
                await highlight_clean_card(page, "#ev-expiry", "2", "Shanghai Drift: 1.0 mg/dL/d")
            elif sid == "S134":
                await highlight_clean_card(page, "#ev-band", "1", "Band Coverage: 83.5%")
                
            await capture_current_state(page, sid, cap, sec, encode_tasks, force=force)
            print(f"  [Evidence Screen] Processed {sid}")
            
        # 8. Return to Clinic & Conclusion (S135 - S149)
        await set_wrapper_header(page, "🔒 https://chhaya-digital-twin.vercel.app/#clinic", "Held-out clinic roster")
        await fl.locator('a[data-view="clinic"]').click()
        await fl.locator("table").first.wait_for(timeout=10000)
        await page.wait_for_timeout(400)
        
        for s in walk_site[79:]: # S135 - S149
            sid = s["id"]
            cap = s["caption"]
            sec = s["seconds"]
            
            if sid == "S135":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(680, 80)")
            elif sid == "S136":
                await page.evaluate("window.__clickRipple(680, 80); window.__moveCursor(960, 450)")
            elif sid in ["S137", "S138"]:
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(960, 450)")
            elif sid == "S139":
                await highlight_clean_card(page, "table", "1", "Zero-Redistribution Audit")
            elif sid == "S140":
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(960, 450)")
            else: # S141 - S149
                await page.evaluate("window.__hideSpotlight(); window.__moveCursor(960, 450)")
                
            await capture_current_state(page, sid, cap, sec, encode_tasks, force=force)
            print(f"  [Walkthrough Close] Processed {sid}")
            
        await browser.close()
        
    print(f"\nCaptured all walkthrough frames! Submitting {len(encode_tasks)} encoding jobs to thread pool...")
    t0 = time.time()
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(encode_single_clip, f_png, sec, out_mp4, force) for f_png, sec, out_mp4 in encode_tasks]
        for idx, fut in enumerate(futures):
            res = fut.result()
            if (idx + 1) % 25 == 0 or (idx + 1) == len(futures):
                print(f"    [{idx+1}/{len(futures)}] Encoded {res.name}")
                
    print(f"\nAll walkthrough clips encoded in {time.time() - t0:.1f}s!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Force re-rendering of frames and clips")
    args = parser.parse_args()
    asyncio.run(run_walkthrough_capture(force=args.force))
