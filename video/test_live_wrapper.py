import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        wrapper_url = Path("video/slides/live_wrapper.html").resolve().as_uri()
        print("Loading wrapper:", wrapper_url)
        await page.goto(wrapper_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)
        
        # Access iframe
        frame = page.frame(name="live-frame") or page.frames[1]
        print("Found frame:", frame.url)
        
        # Verify "Synthetic" tag inside frame
        synth_count = await frame.locator("text=Synthetic").count()
        print("Inside frame, Synthetic count:", synth_count)
        assert synth_count > 0, "Synthetic tag not found in frame!"
        
        # Test clicking reveal button inside frame
        reveal_btn = frame.locator("#reveal-btn")
        if await reveal_btn.count() > 0:
            print("Clicking reveal button...")
            await reveal_btn.click()
            await page.wait_for_timeout(1000)
            
        await page.screenshot(path="video/test_wrapper_capture.png")
        print("Saved video/test_wrapper_capture.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
