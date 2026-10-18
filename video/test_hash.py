import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        wrapper_url = Path('video/slides/live_wrapper.html').resolve().as_uri()
        await page.goto(wrapper_url, wait_until='domcontentloaded')
        await page.wait_for_timeout(3000)
        
        frame = page.frame(name='live-frame') or page.frames[1]
        print('Initial iframe URL:', frame.url)
        
        # Switch to clinic
        await frame.evaluate("location.hash = '#clinic'")
        await page.wait_for_timeout(1000)
        print('Switched to #clinic. Text:', (await frame.locator('body').text_content())[:100])
        
        # Switch to evidence
        await frame.evaluate("location.hash = '#evidence'")
        await page.wait_for_timeout(1000)
        print('Switched to #evidence. Heading:', await frame.locator('h1').text_content())
        
        # Switch back to p-mrs-r
        await frame.evaluate("location.hash = '#p-mrs-r'")
        await page.wait_for_timeout(1000)
        print('Switched to #p-mrs-r. Heading:', await frame.locator('h1').text_content())
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())
