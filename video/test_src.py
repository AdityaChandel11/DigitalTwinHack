import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        wrapper_url = Path('video/slides/live_wrapper.html').resolve().as_uri()
        print("Loading wrapper with wait_until='load'...")
        await page.goto(wrapper_url, wait_until='load')
        await page.wait_for_timeout(2000)
        
        # Test 1: Load Clinic
        print('1. Setting iframe src to clinic...')
        await page.evaluate("document.getElementById('live-frame').src = 'https://chhaya-digital-twin.vercel.app/?theme=dark#clinic'")
        await page.wait_for_timeout(2500)
        frame = page.frame(name='live-frame') or page.frames[1]
        print('Clinic tr count:', await frame.locator('tr').count())
        
        # Test 2: Load Mrs R
        print('2. Setting iframe src to p-mrs-r...')
        await page.evaluate("document.getElementById('live-frame').src = 'https://chhaya-digital-twin.vercel.app/?theme=dark#p-mrs-r'")
        await page.wait_for_timeout(2500)
        frame = page.frame(name='live-frame') or page.frames[1]
        synth = await frame.locator("text=Synthetic").count()
        print('Mrs R Synthetic count:', synth)
        assert synth > 0, "Synthetic tag not found!"
        
        # Test 3: Load Evidence
        print('3. Setting iframe src to evidence...')
        await page.evaluate("document.getElementById('live-frame').src = 'https://chhaya-digital-twin.vercel.app/?theme=dark#evidence'")
        await page.wait_for_timeout(2500)
        frame = page.frame(name='live-frame') or page.frames[1]
        tally = await frame.locator(".tally").count()
        print('Evidence tally count:', tally)
        assert tally > 0, "Tally not found!"
        
        print('\n>>> SUCCESS: All 3 navigation states loaded cleanly via iframe src!')
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())
