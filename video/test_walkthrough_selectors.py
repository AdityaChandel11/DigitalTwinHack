import asyncio
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await page.goto("https://chhaya-digital-twin.vercel.app/?theme=dark", wait_until="networkidle")
        
        print("Page loaded. URL:", page.url)
        
        # 1. Clinic view
        clinic_table = await page.locator("#clinic-table, table, .clinic-table").count()
        print("Clinic table count:", clinic_table)
        rows = await page.locator("tr").count()
        print("TR count:", rows)
        mrs_r_link = await page.locator("a[href*='mrs-r']").count()
        print("Mrs R links count:", mrs_r_link)
        
        # 2. Go to #p-mrs-r
        await page.goto("https://chhaya-digital-twin.vercel.app/?theme=dark#p-mrs-r", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        print("\nNavigated to #p-mrs-r")
        synth = await page.locator("text=Synthetic").count()
        print("'Synthetic' text count:", synth)
        record_btn = await page.locator("#record-btn, a[href='#patient']").count()
        print("Record button count:", record_btn)
        reveal_btn = await page.locator("#reveal-btn").count()
        print("Reveal btn count:", reveal_btn)
        reveal_range = await page.locator("#reveal-range").count()
        print("Reveal range count:", reveal_range)
        whatif_input = await page.locator("#whatif-carbs, input[type='number']").count()
        print("What-if input count:", whatif_input)
        whatif_btn = await page.locator("#whatif-btn, button:has-text('Simulate')").count()
        print("What-if btn count:", whatif_btn)
        
        # 3. Evidence view
        await page.goto("https://chhaya-digital-twin.vercel.app/?theme=dark#evidence", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        print("\nNavigated to #evidence")
        tally = await page.locator(".tally-card, #tally, text=PASSED").count()
        print("Tally / PASSED text count:", tally)
        gate3 = await page.locator("text=Gate 3, text=Post-meal, [data-gate='gate3']").count()
        print("Gate 3 locator count:", gate3)
        cards = await page.locator(".evidence-card, .result-card, .gate-card, details").count()
        print("Details / cards count:", cards)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect())
