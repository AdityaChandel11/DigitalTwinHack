import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        wrapper_url = (Path("video/slides/live_wrapper.html")).resolve().as_uri()
        await page.goto(wrapper_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        frame = page.frame(name="live-frame") or page.frames[1]
        print("Frame URL 1:", frame.url)
        print("Synthetic count 1:", await frame.locator("text=Synthetic").count())
        
        # Switch to clinic
        print("\nSwitching to clinic...")
        await frame.evaluate("location.hash = '#clinic'")
        await page.wait_for_timeout(1500)
        print("Frame URL 2:", frame.url)
        print("Clinic heading:", await frame.locator("h1, thead").first.text_content())
        
        # Now click on Mrs. R. row in clinic table
        print("\nClicking on Mrs. R. row...")
        row = frame.locator("tr[data-id='mrs-r']")
        print("Row count:", await row.count())
        if await row.count() > 0:
            await row.click()
            await page.wait_for_timeout(2000)
            print("Frame URL 3 after click:", frame.url)
            print("Synthetic count 3:", await frame.locator("text=Synthetic").count())
        else:
            print("Row not found! Checking trs...")
            trs = await frame.locator("tr").all_text_contents()
            print("TRs:", trs)
            
        await page.screenshot(path="video/out/debug_switch.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug())
