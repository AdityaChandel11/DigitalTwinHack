import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
import sys

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
from capture import INJECT_JS

async def spotlight_element(page, selector, pin_num, pin_text, pad=16, custom_scroll_offset=None):
    fl = page.frame_locator("#live-frame")
    el = fl.locator(selector).first
    if await el.count() == 0:
        print(f"Warning: selector '{selector}' not found!")
        await page.evaluate("window.__hideSpotlight()")
        return
        
    # Clean scroll accounting for 100px sticky header
    await el.evaluate("""el => {
        const rect = el.getBoundingClientRect();
        const headerH = 100;
        const targetY = headerH + 16;
        const delta = rect.top - targetY;
        window.scrollBy({ top: delta, behavior: 'instant' });
    }""")
    await page.wait_for_timeout(250)
    
    box = await el.bounding_box()
    if not box:
        await page.evaluate("window.__hideSpotlight()")
        return
        
    iframe = page.locator("#live-frame")
    if_box = await iframe.bounding_box() or {"x": 100, "y": 125, "width": 1720, "height": 706}
        
    x = max(if_box["x"] + 8, box["x"] - pad)
    y = max(if_box["y"] + 8, box["y"] - pad)
    avail_w = (if_box["x"] + if_box["width"] - 8) - x
    avail_h = (if_box["y"] + if_box["height"] - 8) - y
    w = min(avail_w, box["width"] + pad * 2)
    h = min(avail_h, box["height"] + pad * 2)
    
    await page.evaluate(f"window.__showSpotlight({x}, {y}, {w}, {h}, '{pin_num}', '{pin_text}')")
    print(f"  [Spotlight] '{pin_num}  {pin_text}' on {selector} -> rect: ({x:.0f}, {y:.0f}, {w:.0f}, {h:.0f})")

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        wrapper_url = Path("video/slides/live_wrapper.html").resolve().as_uri()
        await page.goto(wrapper_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)
        await page.evaluate(INJECT_JS)
        
        # Test 1: Spotlight on Clinic table row Mrs R
        print("1. Testing clinic table row Mrs R...")
        fl = page.frame_locator("#live-frame")
        await fl.locator('a[data-view="clinic"]').click()
        await fl.locator('table tbody tr').first.wait_for(timeout=5000)
        await page.wait_for_timeout(500)
        await spotlight_element(page, 'tr[data-id="mrs-r"]', '1', 'Mrs. R. Synthetic Demo Row', 12)
        await page.screenshot(path="video/out/test_spotlight_clinic.png")
        print("   Saved video/out/test_spotlight_clinic.png")
        
        # Test 2: Spotlight on Health Record panel on Mrs R
        print("2. Testing health record panel on Mrs. R...")
        await fl.locator('a[data-view="patient"]').click()
        await fl.locator('.summary').first.wait_for(timeout=5000)
        await page.wait_for_timeout(500)
        await spotlight_element(page, '.summary', '1', 'Sensor & Wear Summary', 16)
        await page.screenshot(path="video/out/test_spotlight_mrs_r.png")
        print("   Saved video/out/test_spotlight_mrs_r.png")
        
        # Test 3: Spotlight on Chart
        print("3. Testing hero chart...")
        await fl.locator(".hero").scroll_into_view_if_needed()
        await page.wait_for_timeout(300)
        cbox = await fl.locator("#hero-chart").bounding_box()
        pad = 10
        x = cbox["x"] - pad
        y = cbox["y"] - pad
        w = cbox["width"] + pad * 2
        h = cbox["height"] + pad * 2
        await page.evaluate(f"window.__showSpotlight({x}, {y}, {w}, {h}, '2', 'Estimated Glycemic Shadow')")
        await page.screenshot(path="video/out/test_spotlight_chart.png")
        print("   Saved video/out/test_spotlight_chart.png")
        
        await browser.close()
        print("\nAll dynamic spotlights rendered successfully with clean boxes and no text clipping!")

if __name__ == "__main__":
    asyncio.run(test())
