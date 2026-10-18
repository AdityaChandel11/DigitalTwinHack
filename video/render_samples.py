"""
Renderer for Phase 2 sample slides.
Uses Playwright to render each slide HTML at 1920x1080 into video/out/samples/.
"""
import os
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

SAMPLE_SLIDES = [
    ("sample_hook.html", "sample_hook.png"),
    ("sample_bignum.html", "sample_bignum.png"),
    ("sample_build_state1.html", "sample_build_state1.png"),
    ("sample_build_state2.html", "sample_build_state2.png"),
    ("sample_score.html", "sample_score.png"),
    ("sample_site_frame.html", "sample_site_frame.png"),
]

async def render():
    base_dir = Path(__file__).resolve().parent
    slides_dir = base_dir / "slides"
    out_dir = base_dir / "out" / "samples"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    rendered_paths = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1
        )
        page = await context.new_page()
        
        for html_file, out_file in SAMPLE_SLIDES:
            html_path = (slides_dir / html_file).resolve()
            out_path = (out_dir / out_file).resolve()
            
            file_url = html_path.as_uri()
            print(f"Rendering {html_file} -> {out_file}...")
            
            await page.goto(file_url, wait_until="networkidle")
            # Wait for web fonts to load
            await page.evaluate("document.fonts.ready")
            # Small settling pause for layout stability
            await page.wait_for_timeout(200)
            
            await page.screenshot(
                path=str(out_path),
                type="png",
                clip={"x": 0, "y": 0, "width": 1920, "height": 1080}
            )
            print(f"  Saved: {out_path} ({out_path.stat().st_size} bytes)")
            rendered_paths.append(str(out_path))
            
        await browser.close()
        
    print("\n--- PHASE 2 DESIGN GATE SAMPLES RENDERED ---")
    for pth in rendered_paths:
        print(f"Path: {pth}")

if __name__ == "__main__":
    asyncio.run(render())
