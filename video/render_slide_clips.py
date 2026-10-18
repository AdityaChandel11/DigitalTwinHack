"""
Renders all slide segments (174 segments) to:
- video/out/clips/<id>.mp4 (with burned-in captions)
- video/out/clips_nocap/<id>.mp4 (without captions)
Uses ThreadPoolExecutor for fast parallel FFmpeg encoding.
"""
import os
import sys
import json
import time
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
from capture import SLIDE_MAP

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

async def capture_all_slides(force=True):
    with open(STORYBOARD_FILE, "r", encoding="utf-8") as f:
        sb = json.load(f)
        
    slide_segs = [s for s in sb if not s["visual"].startswith("SITE:")]
    print(f"Total slide segments to process: {len(slide_segs)} (force={force})")
    
    # Group segments by slide HTML template to minimize page reloads
    by_template = {}
    for s in slide_segs:
        sid = s["id"]
        tmpl, cat = SLIDE_MAP.get(sid, ("slide_hook.html", "OVERVIEW"))
        by_template.setdefault(tmpl, []).append(s)
        
    encode_tasks = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        for tmpl, segs in by_template.items():
            tmpl_url = (SLIDES_DIR / tmpl).resolve().as_uri()
            await page.goto(tmpl_url, wait_until="domcontentloaded")
            
            # First capture the uncaptioned frame for this template
            await page.evaluate("""
                (() => {
                    const bar = document.getElementById('caption-bar');
                    if (bar) bar.style.display = 'none';
                })()
            """)
            tmpl_nocap_png = FRAMES_DIR / f"{tmpl}_nocap.png"
            await page.screenshot(path=str(tmpl_nocap_png))
            
            for s in segs:
                sid = s["id"]
                cap = s["caption"]
                sec = s["seconds"]
                
                out_cap = CLIPS_CAP_DIR / f"{sid}.mp4"
                out_nocap = CLIPS_NOCAP_DIR / f"{sid}.mp4"
                
                # Captioned frame
                cap_png = FRAMES_DIR / f"{sid}_cap.png"
                if force or not cap_png.exists() or not out_cap.exists() or out_cap.stat().st_size < 10000:
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
                    await page.screenshot(path=str(cap_png))
                    
                encode_tasks.append((cap_png, sec, out_cap))
                encode_tasks.append((tmpl_nocap_png, sec, out_nocap))
                
            print(f"  Processed template {tmpl} ({len(segs)} segments)")
            
        await browser.close()
        
    print(f"\nCaptured all frames! Submitting {len(encode_tasks)} encoding jobs to thread pool...")
    t0 = time.time()
    
    # Parallel encoding with 6 threads
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(encode_single_clip, f_png, sec, out_mp4, force) for f_png, sec, out_mp4 in encode_tasks]
        for idx, fut in enumerate(futures):
            res = fut.result()
            if (idx + 1) % 25 == 0 or (idx + 1) == len(futures):
                print(f"    [{idx+1}/{len(futures)}] Encoded {res.name}")
                
    print(f"\nAll slide clips encoded in {time.time() - t0:.1f}s!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", default=True, help="Force re-rendering all frames and clips")
    args = parser.parse_args()
    
    import asyncio
    asyncio.run(capture_all_slides(force=args.force))
