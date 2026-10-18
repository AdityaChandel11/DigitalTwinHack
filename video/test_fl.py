import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        wrapper_url = Path('video/slides/live_wrapper.html').resolve().as_uri()
        await page.goto(wrapper_url, wait_until='load')
        await page.wait_for_timeout(2000)
        
        # Switch to clinic
        await page.evaluate("document.getElementById('live-frame').src = 'https://chhaya-digital-twin.vercel.app/?theme=dark#clinic'")
        await page.wait_for_timeout(2500)
        clinic_fl = page.frame_locator('#live-frame')
        print('Clinic trs via frame_locator:', await clinic_fl.locator('tr').count())
        
        # Switch to mrs-r
        await page.evaluate("document.getElementById('live-frame').src = 'https://chhaya-digital-twin.vercel.app/?theme=dark#p-mrs-r'")
        await page.wait_for_timeout(2500)
        mrs_fl = page.frame_locator('#live-frame')
        synth_cnt = await mrs_fl.locator("text=Synthetic").count()
        print('Mrs R synth via frame_locator:', synth_cnt)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())
