"""
Render the 10-slide presentation from docs/Chhaya_Final_Deck.html
to PNGs (1920x1080) in docs/slides_png/ and compile to docs/Chhaya_Phase1_Presentation.pdf
"""
import os
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
HTML_PATH = BASE_DIR / "Chhaya_Final_Deck.html"
OUT_PNG_DIR = BASE_DIR / "slides_png"
OUT_PNG_DIR.mkdir(parents=True, exist_ok=True)
OUT_PDF_PATH = BASE_DIR / "Chhaya_Phase1_Presentation.pdf"

async def render():
    print(f"Loading {HTML_PATH.as_uri()} in Playwright headless Chromium...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Create a page matching the 1920x1080 slide dimensions
        page = await browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        
        await page.goto(HTML_PATH.as_uri(), wait_until="networkidle")
        await page.evaluate("document.fonts.ready")
        
        slides = await page.locator(".slide").all()
        print(f"Found {len(slides)} slides.")
        
        rendered_images = []
        for i, slide in enumerate(slides, start=1):
            out_name = f"slide_{i:02d}.png"
            out_png = OUT_PNG_DIR / out_name
            await slide.screenshot(path=str(out_png))
            print(f"  [Rendered PNG] {out_name} (1920x1080)")
            rendered_images.append(out_png)
            
        # Also render high-res PDF via page.pdf with print CSS
        print(f"Compiling vector PDF via Playwright print-to-pdf to {OUT_PDF_PATH}...")
        await page.emulate_media(media="print")
        await page.pdf(
            path=str(OUT_PDF_PATH),
            width="1920px",
            height="1080px",
            print_background=True,
            margin={"top": "0px", "right": "0px", "bottom": "0px", "left": "0px"}
        )
        print(f"Successfully generated vector PDF: {OUT_PDF_PATH} ({OUT_PDF_PATH.stat().st_size} bytes)")
        
        await browser.close()
        return rendered_images

def main():
    images = asyncio.run(render())
    print("\nAll 10 slides rendered successfully to:")
    for img in images:
        print(f"  - {img}")
    print(f"PDF deck generated: {OUT_PDF_PATH}")

if __name__ == "__main__":
    main()
