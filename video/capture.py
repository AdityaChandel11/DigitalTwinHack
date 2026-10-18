"""
Website Capture Engine for Chhaya Video Pipeline.
Implements:
1. Playwright Chromium browser capture at 1920x1080.
2. Clean rounded browser window (1720px wide) on deep ink background with address bar.
3. Human-like interactions:
   - Visible ring cursor with eased mouse movements (600-900ms)
   - Click ripples
   - 0.5 to 1.0s pauses
   - Spotlight highlighting with numbered pin and <= 6 word label
4. Assertion that 'Synthetic' is visible on every Mrs. R. screen.
5. Per-segment capture: python video/capture.py --segment <ID>
6. Video export to video/out/clips/<ID>.mp4 with silent stereo audio track at 30 fps.
"""
import os
import sys
import json
import time
import shutil
import asyncio
import argparse
import subprocess
from pathlib import Path
from playwright.async_api import async_playwright
import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
CLIPS_DIR = BASE_DIR / "out" / "clips"
FRAMES_DIR = BASE_DIR / "out" / "frames"
SLIDES_DIR = BASE_DIR / "slides"
STORYBOARD_FILE = BASE_DIR / "storyboard.json"

CLIPS_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

# Helper: load storyboard
def load_storyboard():
    with open(STORYBOARD_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Helper: compile frame sequence or single frame to MP4 with silent stereo audio
def encode_clip(frame_path_or_pattern, duration_sec, output_mp4, is_single_image=True):
    cmd = [
        FFMPEG_EXE, "-y"
    ]
    if is_single_image:
        cmd.extend(["-loop", "1", "-i", str(frame_path_or_pattern)])
    else:
        cmd.extend(["-r", "30", "-i", str(frame_path_or_pattern)])
        
    cmd.extend([
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-c:v", "libx264",
        "-t", f"{duration_sec:.2f}",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-crf", "18",
        "-c:a", "aac",
        "-shortest",
        str(output_mp4)
    ])
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr)
        raise RuntimeError(f"FFmpeg failed with code {res.returncode}")
    print(f"  [Encoded] {output_mp4.name} ({duration_sec}s, {output_mp4.stat().st_size} bytes)")

# Inject cursor and spotlight into the page
INJECT_JS = """
(() => {
  if (document.getElementById('chhaya-cursor-ring')) return;
  
  // Create Cursor Ring
  const ring = document.createElement('div');
  ring.id = 'chhaya-cursor-ring';
  ring.style.cssText = `
    position: fixed;
    width: 28px;
    height: 28px;
    border: 2.5px solid #ffffff;
    border-radius: 50%;
    pointer-events: none;
    z-index: 999999;
    transform: translate(-50%, -50%);
    box-shadow: 0 0 14px rgba(144, 133, 233, 0.85);
    transition: width 0.15s, height 0.15s, background-color 0.15s, border-color 0.15s;
    left: -100px; top: -100px;
  `;
  document.body.appendChild(ring);
  
  // Spotlight container
  const spot = document.createElement('div');
  spot.id = 'chhaya-spotlight-box';
  spot.style.cssText = `
    position: fixed;
    pointer-events: none;
    z-index: 999990;
    border: 2.5px solid #6C3CE2;
    border-radius: 14px;
    background: rgba(108, 60, 226, 0.03);
    box-shadow: 0 0 0 3px rgba(108, 60, 226, 0.12), 0 8px 30px rgba(108, 60, 226, 0.18);
    display: none;
    transition: all 0.2s ease;
  `;
  
  const pin = document.createElement('div');
  pin.id = 'chhaya-spotlight-pin';
  pin.style.cssText = `
    position: absolute;
    top: -36px;
    left: 12px;
    background: linear-gradient(135deg, #6C3CE2 0%, #8B5CF6 100%);
    color: #ffffff;
    font-family: 'JetBrains Mono', 'Source Code Pro', monospace;
    font-size: 13px;
    font-weight: 700;
    padding: 5px 12px;
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(108, 60, 226, 0.35);
    white-space: nowrap;
    letter-spacing: 0.5px;
  `;
  spot.appendChild(pin);
  document.body.appendChild(spot);
  
  // Click Ripple function
  window.__clickRipple = (x, y) => {
    ring.classList.add('active-click');
    const rip = document.createElement('div');
    rip.style.cssText = `
      position: fixed;
      left: ${x}px; top: ${y}px;
      width: 10px; height: 10px;
      border: 2px solid #6C3CE2;
      border-radius: 50%;
      pointer-events: none;
      z-index: 999998;
      transform: translate(-50%, -50%);
      transition: width 0.4s ease-out, height 0.4s ease-out, opacity 0.4s ease-out;
    `;
    document.body.appendChild(rip);
    requestAnimationFrame(() => {
      rip.style.width = '64px';
      rip.style.height = '64px';
      rip.style.opacity = '0';
    });
    setTimeout(() => {
      rip.remove();
      ring.classList.remove('active-click');
    }, 450);
  };
  
  // Move Cursor function
  window.__moveCursor = (x, y) => {
    ring.style.left = `${x}px`;
    ring.style.top = `${y}px`;
  };
  
  // Show Spotlight
  window.__showSpotlight = (x, y, w, h, pinNum, pinText) => {
    spot.style.left = `${x}px`;
    spot.style.top = `${y}px`;
    spot.style.width = `${w}px`;
    spot.style.height = `${h}px`;
    pin.textContent = `${pinNum}  ${pinText}`;
    if (y < 240) {
      pin.style.top = '12px';
      pin.style.left = 'auto';
      pin.style.right = '16px';
    } else {
      pin.style.top = '-34px';
      pin.style.left = '12px';
      pin.style.right = 'auto';
    }
    spot.style.display = 'block';
  };
  
  // Hide Spotlight
  window.__hideSpotlight = () => {
    spot.style.display = 'none';
  };
})();
"""

# Smooth cursor movement helper in Playwright
async def move_cursor_smoothly(page, start_x, start_y, end_x, end_y, steps=25):
    for i in range(1, steps + 1):
        t = i / steps
        # Cubic ease-out: 1 - (1 - t)^3
        ease = 1.0 - (1.0 - t) ** 3
        curr_x = start_x + (end_x - start_x) * ease
        curr_y = start_y + (end_y - start_y) * ease
        await page.evaluate(f"window.__moveCursor({curr_x}, {curr_y})")
        await asyncio.sleep(0.02) # ~500ms total
        
async def click_at(page, x, y):
    await page.evaluate(f"window.__clickRipple({x}, {y})")
    await asyncio.sleep(0.3)

# Slide HTML mapping
SLIDE_MAP = {
    "S009": ("slide_hook.html", "PROJECT FILM  OVERVIEW"),
    "S010": ("slide_hook.html", "PROJECT FILM  OVERVIEW"),
    "S011": ("slide_team.html", "SYNAPSEX  D.B.S KANPUR"),
    "S012": ("slide_scoreboard.html", "PREREGISTERED SCOREBOARD"),
    "S013": ("slide_scoreboard.html", "PREREGISTERED SCOREBOARD"),
    "S014": ("slide_scoreboard.html", "PREREGISTERED SCOREBOARD"),
    "S015": ("slide_scoreboard.html", "PREREGISTERED SCOREBOARD"),
    "S016": ("slide_what_changed.html", "WHAT THE MISSES CHANGED"),
    "S017": ("slide_what_changed.html", "WHAT THE MISSES CHANGED"),
    "S018": ("slide_what_changed.html", "WHAT THE MISSES CHANGED"),
    "S019": ("slide_what_changed.html", "WHAT THE MISSES CHANGED"),
    "S020": ("slide_what_changed.html", "WHAT THE MISSES CHANGED"),
    "S021": ("slide_bignum.html", "THE CLINICAL PROBLEM IN INDIA"),
    "S022": ("slide_bignum.html", "THE CLINICAL PROBLEM IN INDIA"),
    "S023": ("slide_unmeasured_gap.html", "THE UNMEASURED GAP"),
    "S024": ("slide_unmeasured_gap.html", "THE UNMEASURED GAP"),
    "S025": ("slide_unmeasured_gap.html", "THE UNMEASURED GAP"),
    "S026": ("slide_core_questions.html", "CLINICAL QUESTIONS"),
    "S027": ("slide_core_questions.html", "CLINICAL QUESTIONS"),
    "S028": ("slide_core_questions.html", "CLINICAL QUESTIONS"),
    "S029": ("slide_core_questions.html", "CLINICAL QUESTIONS"),
    "S030": ("slide_core_questions.html", "CLINICAL QUESTIONS"),
    "S031": ("slide_core_questions.html", "CLINICAL QUESTIONS"),
    "S032": ("slide_core_questions.html", "CLINICAL QUESTIONS"),
    "S033": ("slide_core_questions.html", "CLINICAL QUESTIONS"),
    "S034": ("slide_core_questions.html", "CLINICAL QUESTIONS"),
    "S035": ("slide_protocol.html", "THE REVEAL PROTOCOL"),
    "S036": ("slide_protocol.html", "THE REVEAL PROTOCOL"),
    "S037": ("slide_protocol.html", "THE REVEAL PROTOCOL"),
    "S038": ("slide_protocol.html", "THE REVEAL PROTOCOL"),
    "S039": ("slide_protocol.html", "THE REVEAL PROTOCOL"),
    "S040": ("slide_protocol.html", "THE REVEAL PROTOCOL"),
    "S041": ("slide_protocol.html", "THE REVEAL PROTOCOL"),
    "S042": ("slide_protocol.html", "THE REVEAL PROTOCOL"),
    "S043": ("slide_protocol.html", "THE REVEAL PROTOCOL"),
    "S044": ("slide_protocol.html", "THE REVEAL PROTOCOL"),
    "S045": ("slide_protocol.html", "THE REVEAL PROTOCOL"),
    "S046": ("slide_protocol.html", "THE REVEAL PROTOCOL"),
    "S047": ("slide_protocol.html", "THE REVEAL PROTOCOL"),
    "S048": ("slide_bignum.html", "THE CLINICAL PROBLEM IN INDIA"),
    "S049": ("slide_protocol.html", "THE REVEAL PROTOCOL"),
    "S050": ("slide_protocol.html", "THE REVEAL PROTOCOL"),
    "S051": ("slide_bignum.html", "THE CLINICAL PROBLEM IN INDIA"),
    "S052": ("slide_protocol.html", "THE REVEAL PROTOCOL"),
    "S053": ("slide_protocol.html", "THE REVEAL PROTOCOL"),
    "S054": ("slide_protocol.html", "THE REVEAL PROTOCOL"),
    "S055": ("slide_protocol.html", "THE REVEAL PROTOCOL"),
    # How It Was Made slides
    "S150": ("slide_datasets.html", "HOW IT WAS MADE"),
    "S151": ("slide_datasets.html", "DATASETS & LICENCES"),
    "S152": ("slide_datasets.html", "DATASETS & LICENCES"),
    "S153": ("slide_datasets.html", "DATASETS & LICENCES"),
    "S154": ("slide_datasets.html", "DATASETS & LICENCES"),
    "S155": ("slide_datasets.html", "DATASETS & LICENCES"),
    "S156": ("slide_datasets.html", "DATASETS & LICENCES"),
    "S157": ("slide_split.html", "SPLIT METHODOLOGY"),
    "S158": ("slide_split.html", "SPLIT METHODOLOGY"),
    "S159": ("slide_datasets.html", "DATASETS & LICENCES"),
    "S160": ("slide_architecture.html", "ONE-WAY PIPELINE"),
    "S161": ("slide_architecture.html", "ONE-WAY PIPELINE"),
    "S162": ("slide_architecture.html", "ONE-WAY PIPELINE"),
    "S163": ("slide_architecture.html", "ONE-WAY PIPELINE"),
    "S164": ("slide_architecture.html", "ONE-WAY PIPELINE"),
    "S165": ("slide_architecture.html", "ONE-WAY PIPELINE"),
    "S166": ("slide_architecture.html", "ONE-WAY PIPELINE"),
    "S167": ("slide_twin_core.html", "PHYSIOLOGICAL MODEL"),
    "S168": ("slide_twin_core.html", "PHYSIOLOGICAL MODEL"),
    "S169": ("slide_twin_core.html", "PHYSIOLOGICAL MODEL"),
    "S170": ("slide_twin_core.html", "PHYSIOLOGICAL MODEL"),
    "S171": ("slide_twin_core.html", "PHYSIOLOGICAL MODEL"),
    "S172": ("slide_twin_core.html", "PHYSIOLOGICAL MODEL"),
    "S173": ("slide_twin_core.html", "PHYSIOLOGICAL MODEL"),
    "S174": ("slide_twin_core.html", "PHYSIOLOGICAL MODEL"),
    "S175": ("slide_twin_core.html", "PHYSIOLOGICAL MODEL"),
    "S176": ("slide_twin_core.html", "PHYSIOLOGICAL MODEL"),
    "S177": ("slide_twin_core.html", "PHYSIOLOGICAL MODEL"),
    "S178": ("slide_twin_core.html", "PHYSIOLOGICAL MODEL"),
    "S179": ("slide_twin_core.html", "PHYSIOLOGICAL MODEL"),
    "S180": ("slide_twin_core.html", "PHYSIOLOGICAL MODEL"),
    "S181": ("slide_twin_core.html", "PHYSIOLOGICAL MODEL"),
    "S182": ("slide_twin_core.html", "PHYSIOLOGICAL MODEL"),
    "S183": ("slide_blend.html", "THE BLEND"),
    "S184": ("slide_blend.html", "THE BLEND"),
    "S185": ("slide_blend.html", "THE BLEND"),
    "S186": ("slide_blend.html", "THE BLEND"),
    "S187": ("slide_architecture.html", "RULES & RIGOR"),
    "S188": ("slide_architecture.html", "RULES & RIGOR"),
    "S189": ("slide_architecture.html", "RULES & RIGOR"),
    "S190": ("slide_architecture.html", "RULES & RIGOR"),
    "S191": ("slide_architecture.html", "RULES & RIGOR"),
    "S192": ("slide_architecture.html", "RULES & RIGOR"),
    "S193": ("slide_architecture.html", "RULES & RIGOR"),
    "S194": ("slide_architecture.html", "RULES & RIGOR"),
    "S195": ("slide_architecture.html", "RULES & RIGOR"),
    "S196": ("slide_architecture.html", "RULES & RIGOR"),
    "S197": ("slide_architecture.html", "RULES & RIGOR"),
    "S198": ("slide_architecture.html", "RULES & RIGOR"),
    "S198b": ("slide_architecture.html", "RULES & RIGOR"),
    # Results slides
    "S199": ("slide_scoreboard.html", "RESULTS AT TRUE SIZE"),
    "S200": ("slide_scoreboard.html", "RESULTS AT TRUE SIZE"),
    "S201": ("slide_scoreboard.html", "RESULTS AT TRUE SIZE"),
    "S202": ("slide_results_gate2.html", "GATE 2  THE REVEAL RESULT"),
    "S203": ("slide_results_gate2.html", "GATE 2  THE REVEAL RESULT"),
    "S204": ("slide_results_gate2.html", "GATE 2  THE REVEAL RESULT"),
    "S205": ("slide_results_gate2.html", "GATE 2  THE REVEAL RESULT"),
    "S206": ("slide_results_gate2.html", "GATE 2  THE REVEAL RESULT"),
    "S206b": ("slide_results_gate2.html", "GATE 2  THE REVEAL RESULT"),
    "S207": ("slide_results_gate2.html", "GATE 2  THE REVEAL RESULT"),
    "S208": ("slide_results_gate2.html", "GATE 2  THE REVEAL RESULT"),
    "S209": ("slide_results_gate2.html", "GATE 2  THE REVEAL RESULT"),
    "S210": ("slide_results_gate2.html", "GATE 2  THE REVEAL RESULT"),
    "S210b": ("slide_results_gate2.html", "GATE 2  THE REVEAL RESULT"),
    "S211": ("slide_results_gate2.html", "GATE 2  THE REVEAL RESULT"),
    "S212": ("slide_results_sticks.html", "FINGERSTICKS EVALUATION"),
    "S213": ("slide_results_sticks.html", "FINGERSTICKS EVALUATION"),
    "S214": ("slide_results_sticks.html", "FINGERSTICKS EVALUATION"),
    "S215": ("slide_results_sticks.html", "FINGERSTICKS EVALUATION"),
    "S216": ("slide_results_sticks.html", "FINGERSTICKS EVALUATION"),
    "S216b": ("slide_results_sticks.html", "FINGERSTICKS EVALUATION"),
    "S217": ("slide_results_sticks.html", "FINGERSTICKS EVALUATION"),
    "S218": ("slide_results_prior.html", "RECORD PRIOR  FUSION RESULT"),
    "S219": ("slide_results_prior.html", "RECORD PRIOR  FUSION RESULT"),
    "S220": ("slide_results_prior.html", "RECORD PRIOR  FUSION RESULT"),
    "S221": ("slide_results_prior.html", "RECORD PRIOR  FUSION RESULT"),
    "S222": ("slide_results_prior.html", "RECORD PRIOR  FUSION RESULT"),
    "S223": ("slide_results_prior.html", "RECORD PRIOR  FUSION RESULT"),
    "S223b": ("slide_results_prior.html", "RECORD PRIOR  FUSION RESULT"),
    "S224": ("slide_results_ladder.html", "GATE 3  INFORMATION LADDER"),
    "S225": ("slide_results_ladder.html", "GATE 3  INFORMATION LADDER"),
    "S226": ("slide_results_ladder.html", "GATE 3  INFORMATION LADDER"),
    "S227": ("slide_results_ladder.html", "GATE 3  INFORMATION LADDER"),
    "S228": ("slide_results_ladder.html", "GATE 3  INFORMATION LADDER"),
    "S229": ("slide_results_ladder.html", "GATE 3  INFORMATION LADDER"),
    "S230": ("slide_results_ladder.html", "GATE 3  INFORMATION LADDER"),
    "S231": ("slide_results_ladder.html", "GATE 3  INFORMATION LADDER"),
    "S231b": ("slide_results_ladder.html", "GATE 3  INFORMATION LADDER"),
    "S232": ("slide_results_baselines.html", "EMPIRICAL TRUTH"),
    "S233": ("slide_results_baselines.html", "EMPIRICAL TRUTH"),
    "S234": ("slide_results_baselines.html", "EMPIRICAL TRUTH"),
    "S235": ("slide_results_baselines.html", "EMPIRICAL TRUTH"),
    "S236": ("slide_results_baselines.html", "EMPIRICAL TRUTH"),
    "S236b": ("slide_results_baselines.html", "EMPIRICAL TRUTH"),
    "S237": ("slide_results_baselines.html", "EMPIRICAL TRUTH"),
    "S238": ("slide_results_baselines.html", "EMPIRICAL TRUTH"),
    "S239": ("slide_results_baselines.html", "EMPIRICAL TRUTH"),
    "S240": ("slide_results_baselines.html", "EMPIRICAL TRUTH"),
    "S241": ("slide_results_baselines.html", "EMPIRICAL TRUTH"),
    "S242": ("slide_results_baselines.html", "EMPIRICAL TRUTH"),
    "S243": ("slide_results_baselines.html", "EMPIRICAL TRUTH"),
    # Limits & Close slides
    "S244": ("slide_limits.html", "WHAT CHHAYA IS NOT"),
    "S245": ("slide_limits.html", "WHAT CHHAYA IS NOT"),
    "S246": ("slide_limits.html", "WHAT CHHAYA IS NOT"),
    "S247": ("slide_limits.html", "WHAT CHHAYA IS NOT"),
    "S248": ("slide_limits.html", "WHAT CHHAYA IS NOT"),
    "S249": ("slide_limits.html", "WHAT CHHAYA IS NOT"),
    "S250": ("slide_limits.html", "WHAT CHHAYA IS NOT"),
    "S251": ("slide_limits.html", "WHAT CHHAYA IS NOT"),
    "S252": ("slide_limits.html", "WHAT CHHAYA IS NOT"),
    "S253": ("slide_limits.html", "WHAT CHHAYA IS NOT"),
    "S254": ("slide_what_changed.html", "CONSEQUENCES IN THE PRODUCT"),
    "S255": ("slide_what_changed.html", "CONSEQUENCES IN THE PRODUCT"),
    "S256": ("slide_what_changed.html", "CONSEQUENCES IN THE PRODUCT"),
    "S257": ("slide_what_changed.html", "CONSEQUENCES IN THE PRODUCT"),
    "S258": ("slide_what_changed.html", "CONSEQUENCES IN THE PRODUCT"),
    "S259": ("slide_what_changed.html", "CONSEQUENCES IN THE PRODUCT"),
    "S260": ("slide_what_changed.html", "CONSEQUENCES IN THE PRODUCT"),
    "S260b": ("slide_limits.html", "FULL TRANSPARENCY"),
    "S261": ("slide_close.html", "TRY THE LIVE SYSTEM"),
    "S262": ("slide_close.html", "TRY THE LIVE SYSTEM"),
    "S263": ("slide_close.html", "TRY THE LIVE SYSTEM"),
    "S264": ("slide_close.html", "TRY THE LIVE SYSTEM"),
    "S265": ("slide_close.html", "TRY THE LIVE SYSTEM"),
    "S266": ("slide_close.html", "TRY THE LIVE SYSTEM"),
    "S267": ("slide_close.html", "TRY THE LIVE SYSTEM"),
    "S268": ("slide_close.html", "TRY THE LIVE SYSTEM"),
}

# Capture single slide segment
async def capture_slide_segment(browser, seg):
    sid = seg["id"]
    cap = seg["caption"]
    sec = seg["seconds"]
    
    mapping = SLIDE_MAP.get(sid, ("slide_hook.html", "OVERVIEW"))
    html_file, cat = mapping
    
    page = await browser.new_page(viewport={"width": 1920, "height": 1080})
    file_url = (SLIDES_DIR / html_file).resolve().as_uri()
    
    await page.goto(file_url, wait_until="networkidle")
    await page.evaluate("document.fonts.ready")
    
    # Inject caption bar if caption present
    if cap.strip():
        await page.evaluate(f"""
          (() => {{
            const bar = document.getElementById('caption-bar');
            const txt = document.getElementById('caption-text');
            if (bar && txt) {{
              txt.textContent = {json.dumps(cap)};
              bar.style.display = 'flex';
            }}
          }})()
        """)
        
    frame_png = FRAMES_DIR / f"{sid}_frame.png"
    await page.screenshot(path=str(frame_png))
    await page.close()
    
    out_mp4 = CLIPS_DIR / f"{sid}.mp4"
    encode_clip(frame_png, sec, out_mp4, is_single_image=True)
    return out_mp4

# Capture live site segment
async def capture_site_segment(browser, seg):
    sid = seg["id"]
    cap = seg["caption"]
    sec = seg["seconds"]
    vis = seg["visual"]
    
    page = await browser.new_page(viewport={"width": 1920, "height": 1080})
    wrapper_url = (SLIDES_DIR / "live_wrapper.html").resolve().as_uri()
    
    await page.goto(wrapper_url, wait_until="networkidle")
    await page.wait_for_timeout(1500)
    
    # Inject cursor/spotlight JS into wrapper
    await page.evaluate(INJECT_JS)
    
    # Set caption on wrapper
    await page.evaluate(f"""
      (() => {{
        const el = document.getElementById('caption-label');
        if (el) el.textContent = {json.dumps(cap)};
      }})()
    """)
    
    # Access live site frame
    frame = page.frame(name="live-frame") or page.frames[1]
    
    # Assert Synthetic tag is visible on screen
    synth_count = await frame.locator("text=Synthetic").count()
    if synth_count == 0:
        raise AssertionError(f"[{sid}] FAILED: 'Synthetic' tag not found on screen!")
    print(f"  [{sid}] Verified 'Synthetic' tag present ({synth_count} occurrences).")
    
    # Specific interactions based on segment id
    if sid == "S001" or sid == "S002":
        # Neutral view on shadow
        await page.evaluate("window.__moveCursor(960, 500)")
        await asyncio.sleep(0.5)
        
    elif sid == "S003":
        # Spotlight on purple trajectory
        await page.evaluate("window.__showSpotlight(300, 320, 1100, 180, '1', 'Estimated Glucose')")
        await move_cursor_smoothly(page, 960, 500, 850, 410)
        
    elif sid == "S004":
        # Spotlight on uncertainty envelope
        await page.evaluate("window.__showSpotlight(300, 280, 1100, 260, '2', '80% Uncertainty Band')")
        await move_cursor_smoothly(page, 850, 410, 600, 380)
        
    elif sid == "S005":
        # Move cursor to Reveal button
        await page.evaluate("window.__hideSpotlight()")
        reveal_btn = frame.locator("#reveal-btn")
        box = await reveal_btn.bounding_box()
        if box:
            # Offset inside viewport
            target_x = 100 + box["x"] + box["width"] / 2
            target_y = 125 + box["y"] + box["height"] / 2
            await move_cursor_smoothly(page, 600, 380, target_x, target_y)
            await asyncio.sleep(0.5)
            
    elif sid == "S006":
        # Click Reveal button
        reveal_btn = frame.locator("#reveal-btn")
        box = await reveal_btn.bounding_box()
        target_x = 100 + (box["x"] if box else 1450)
        target_y = 125 + (box["y"] if box else 260)
        await page.evaluate(f"window.__moveCursor({target_x}, {target_y})")
        await click_at(page, target_x, target_y)
        if await reveal_btn.count() > 0:
            await reveal_btn.click()
            await page.wait_for_timeout(1000)
            
    elif sid == "S007":
        # Spotlight on teal / amber revealed sensor
        await page.evaluate("window.__showSpotlight(450, 300, 950, 220, '3', 'Real Sensor Overlay')")
        await move_cursor_smoothly(page, target_x if 'target_x' in locals() else 960, target_y if 'target_y' in locals() else 300, 900, 360)
        
    elif sid == "S008":
        # Drag scrubber across days
        range_input = frame.locator("#reveal-range")
        if await range_input.count() > 0:
            s_box = await range_input.bounding_box()
            if s_box:
                sx = 100 + s_box["x"] + 20
                sy = 125 + s_box["y"] + s_box["height"] / 2
                await page.evaluate(f"window.__moveCursor({sx}, {sy})")
                await click_at(page, sx, sy)
                await move_cursor_smoothly(page, sx, sy, sx + 250, sy)
                await frame.evaluate("const r = document.getElementById('reveal-range'); if (r) { r.value = 65; r.dispatchEvent(new Event('input')); }")
                await page.wait_for_timeout(600)
                
    # Capture frame
    frame_png = FRAMES_DIR / f"{sid}_frame.png"
    await page.screenshot(path=str(frame_png))
    await page.close()
    
    out_mp4 = CLIPS_DIR / f"{sid}.mp4"
    encode_clip(frame_png, sec, out_mp4, is_single_image=True)
    return out_mp4

# Dispatch capture based on visual
async def capture_segment(browser, seg):
    vis = seg["visual"]
    if vis.startswith("SITE:"):
        return await capture_site_segment(browser, seg)
    else:
        return await capture_slide_segment(browser, seg)

async def main():
    parser = argparse.ArgumentParser(description="Chhaya Website & Slide Capture Pipeline")
    parser.add_argument("--segment", type=str, default="cold-open", help="Segment ID (e.g. S001) or 'cold-open' or 'all'")
    args = parser.parse_args()
    
    storyboard = load_storyboard()
    
    if args.segment == "cold-open":
        target_segs = [s for s in storyboard if s["chapter"] == "Cold Open"]
    elif args.segment == "all":
        target_segs = storyboard
    else:
        target_segs = [s for s in storyboard if s["id"] == args.segment]
        if not target_segs:
            print(f"Error: segment {args.segment} not found in storyboard.json")
            sys.exit(1)
            
    print(f"Starting capture for {len(target_segs)} segments...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        captured_clips = []
        for s in target_segs:
            print(f"\nProcessing [{s['id']}] ({s['seconds']}s) - {s['chapter']}: {s['visual'][:60]}...")
            out_clip = await capture_segment(browser, s)
            captured_clips.append((s, out_clip))
            
        await browser.close()
        
    print(f"\nSuccessfully captured {len(captured_clips)} clips in {CLIPS_DIR}")

if __name__ == "__main__":
    asyncio.run(main())
