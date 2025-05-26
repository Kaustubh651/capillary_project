# flipkart.py
import asyncio
import json
import os
from urllib.parse import urljoin

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

OFFERS_URL = "https://www.flipkart.com/offers-list/bestselling-furniture?screen=dynamic&pk=themeViews%3DFur-BestsellingFurniture-DealCard%3ADT~widgetType%3DdealCard~contentType%3Dneo&bu=MIXED&wid=13.dealCard.OMU_3&otracker=clp_omu_Bestselling%2BFurniture_offers-store_3&otracker1=clp_omu_PINNED_neo%2Fmerchandising_Bestselling%2BFurniture_NA_wc_view-all_3"
BASE_URL   = "https://www.flipkart.com"
OUTPUT_FILE = "flipkart_offers.json"

async def auto_scroll(page, steps=10, delay=1000):
    prev = 0
    for _ in range(steps):
        curr = await page.evaluate(
            "document.querySelectorAll('a._6WQwDJ').length"
        )
        if curr == prev:
            break
        prev = curr
        await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        await page.wait_for_timeout(delay)
    return prev

async def scrape_flipkart_offers():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # load the generic offers list
        await page.goto(OFFERS_URL, wait_until="load", timeout=30000)
        # dismiss login pop-up if it shows
        try:
            await page.click("button._2KpZ6l._2doB4z", timeout=2000)
        except PlaywrightTimeout:
            pass

        # scroll to load all tiles
        total = await auto_scroll(page)

        if total == 0:
            print("❌ No deals found!")
            await browser.close()
            return []

        # each deal tile is an <a class="_6WQwDJ" …>
        tiles = await page.query_selector_all("a._6WQwDJ")
        results = []
        for t in tiles:
            href = await t.get_attribute("href") or ""
            link = urljoin(BASE_URL, href)

            # inside each tile:
            #  • <div class="_2N1WLe">heading
            #  • <div class="_3LU4EM">subheading
            #  • <div class="_1xxHXK">brand
            title_el       = await t.query_selector("div._2N1WLe")
            description_el = await t.query_selector("div._3LU4EM")
            brand_el       = await t.query_selector("div._1xxHXK")

            title       = await title_el.inner_text()       if title_el       else ""
            description = await description_el.inner_text() if description_el else ""
            brand       = await brand_el.inner_text()       if brand_el       else ""

            results.append({
                "title":       title.strip(),
                "description": description.strip(),
                "brand":       brand.strip(),
                "link":        link,
                "expiry":      ""
            })

        await browser.close()
        return results

async def main():
    new_offers = await scrape_flipkart_offers()

    # load existing
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
    else:
        existing = []

    combined = existing + new_offers
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"Loaded {len(existing)} existing, scraped {len(new_offers)} new, total {len(combined)} → {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
