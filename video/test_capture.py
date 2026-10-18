import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        url = "https://chhaya-digital-twin.vercel.app/?theme=dark#p-mrs-r"
        print("Navigating to:", url)
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(1000)
        
        # Check Synthetic tag
        synth_count = await page.locator("text=Synthetic").count()
        print("Synthetic tag count:", synth_count)
        assert synth_count > 0, "Synthetic tag not found on Mrs. R screen!"
        
        # Check controls
        reveal_btn = page.locator("#reveal-btn")
        has_reveal = await reveal_btn.count() > 0
        print("Reveal btn present:", has_reveal)
        
        # Take a test screenshot
        await page.screenshot(path="video/test_mrs_r.png")
        print("Saved video/test_mrs_r.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
