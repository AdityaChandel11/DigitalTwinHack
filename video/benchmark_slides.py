import time
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def benchmark():
    t0 = time.time()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        slide_url = (Path("video/slides/slide_bignum.html")).resolve().as_uri()
        await page.goto(slide_url)
        
        for i in range(5):
            t_start = time.time()
            await page.evaluate(f"""
                document.getElementById('caption-text').textContent = 'Test caption {i} for benchmark';
                document.getElementById('caption-bar').style.display = 'flex';
            """)
            await page.screenshot(path=f"video/out/test_{i}.png")
            print(f"Slide {i} took {time.time() - t_start:.3f}s")
            
        await browser.close()
    print(f"Total time for 5 slides: {time.time() - t0:.3f}s")

if __name__ == "__main__":
    asyncio.run(benchmark())
