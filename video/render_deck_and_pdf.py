"""
Renders each of the 20 presentation slides to video/out/slides/*.png (1920x1080)
and compiles them into video/out/Chhaya_Presentation.pdf.
"""
import os
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
SLIDES_DIR = BASE_DIR / "slides"
OUT_DIR = BASE_DIR / "out"
SLIDES_OUT_DIR = OUT_DIR / "slides"
SLIDES_OUT_DIR.mkdir(parents=True, exist_ok=True)

DECK_SLIDES = [
    ("01_slide_hook.png", "slide_hook.html"),
    ("02_slide_team.png", "slide_team.html"),
    ("03_slide_scoreboard.png", "slide_scoreboard.html"),
    ("04_slide_what_changed.png", "slide_what_changed.html"),
    ("05_slide_bignum.png", "slide_bignum.html"),
    ("06_slide_unmeasured_gap.png", "slide_unmeasured_gap.html"),
    ("07_slide_core_questions.png", "slide_core_questions.html"),
    ("08_slide_protocol.png", "slide_protocol.html"),
    ("09_slide_datasets.png", "slide_datasets.html"),
    ("10_slide_split.png", "slide_split.html"),
    ("11_slide_architecture.png", "slide_architecture.html"),
    ("12_slide_twin_core.png", "slide_twin_core.html"),
    ("13_slide_blend.png", "slide_blend.html"),
    ("14_slide_results_gate2.png", "slide_results_gate2.html"),
    ("15_slide_results_sticks.png", "slide_results_sticks.html"),
    ("16_slide_results_prior.png", "slide_results_prior.html"),
    ("17_slide_results_ladder.png", "slide_results_ladder.html"),
    ("18_slide_results_baselines.png", "slide_results_baselines.html"),
    ("19_slide_limits.png", "slide_limits.html"),
    ("20_slide_close.png", "slide_close.html"),
]

async def render_slides():
    print(f"Rendering {len(DECK_SLIDES)} presentation slides...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        rendered_images = []
        for out_name, html_file in DECK_SLIDES:
            file_url = (SLIDES_DIR / html_file).resolve().as_uri()
            await page.goto(file_url, wait_until="domcontentloaded")
            await page.evaluate("document.fonts.ready")
            
            # Ensure caption bar is hidden for the presentation deck
            await page.evaluate("""
                (() => {
                    const bar = document.getElementById('caption-bar');
                    if (bar) bar.style.display = 'none';
                })()
            """)
            
            out_png = SLIDES_OUT_DIR / out_name
            await page.screenshot(path=str(out_png))
            print(f"  [Rendered] {out_name} (1920x1080)")
            rendered_images.append(out_png)
            
        await browser.close()
        return rendered_images

def compile_pdf(images):
    pdf_path = OUT_DIR / "Chhaya_Presentation.pdf"
    print(f"\nCompiling PDF deck to {pdf_path}...")
    pil_images = [Image.open(p).convert("RGB") for p in images]
    
    first = pil_images[0]
    rest = pil_images[1:]
    first.save(pdf_path, save_all=True, append_images=rest, quality=95)
    print(f"Successfully generated {pdf_path.name} ({len(images)} pages, {pdf_path.stat().st_size} bytes)")

async def main():
    images = await render_slides()
    compile_pdf(images)

if __name__ == "__main__":
    asyncio.run(main())
