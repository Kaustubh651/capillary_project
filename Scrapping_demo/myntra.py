# myntra.py
import asyncio
import json
import os
from urllib.parse import urljoin
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout, Error as PlaywrightError

SEARCH_URL  = "https://www.myntra.com/offers"
BASE_URL    = "https://www.myntra.com"
OUTPUT_FILE = "myntra_offers.json"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/113.0.0.0 Safari/537.36"
)

async def auto_scroll(page, max_scrolls=10, delay=1000):
    """Scroll down in steps until no more new items appear or max_scrolls reached."""
    prev_count = 0
    for _ in range(max_scrolls):
        # count how many product cards we have
        curr_count = await page.evaluate(
            """() => document.querySelectorAll('ul.results-base li.product-base').length"""
        )
        if curr_count == prev_count:
            break
        prev_count = curr_count
        # scroll to bottom
        await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        # wait a bit for new items to load
        await page.wait_for_timeout(delay)
    return prev_count

async def scrape_myntra_offers():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=UA, locale="en-IN")
        page = await context.new_page()

        try:
            await page.goto(SEARCH_URL, wait_until="load", timeout=45000)
        except PlaywrightError as e:
            if "ERR_HTTP2_PROTOCOL_ERROR" not in str(e):
                raise

        # auto-scroll until products stop loading
        total = await auto_scroll(page)

        # if still no items, bail out early
        if total == 0:
            print("❌ No products found on the page!")
            await browser.close()
            return []

        # now grab all product cards
        cards = await page.query_selector_all("ul.results-base li.product-base")
        results = []
        for card in cards:
            # link
            a = await card.query_selector("a")
            href = await a.get_attribute("href") or ""
            link = urljoin(BASE_URL, href)

            # image
            img = await card.query_selector("img.img-responsive")
            img_url = await img.get_attribute("src") if img else ""

            # brand / title / sizes
            brand_el = await card.query_selector("h3.product-brand")
            title_el = await card.query_selector("h4.product-product")
            size_el  = await card.query_selector("h4.product-sizes span")
            brand = (await brand_el.inner_text()).strip() if brand_el else ""
            title = (await title_el.inner_text()).strip() if title_el else ""
            sizes = await size_el.inner_text() if size_el else ""

            # prices
            disc_price_el = await card.query_selector("span.product-discountedPrice")
            orig_price_el = await card.query_selector("span.product-strike")
            discount_el   = await card.query_selector("span.product-discountPercentage")
            discounted = (await disc_price_el.inner_text()).strip() if disc_price_el else ""
            struck     = (await orig_price_el.inner_text()).strip() if orig_price_el else ""
            discount   = (await discount_el.inner_text()).strip() if discount_el else ""

            results.append({
                "brand": brand,
                "title": title,
                "sizes": sizes,
                "discounted_price": discounted,
                "original_price": struck,
                "discount": discount,
                "link": link,
                "image": img_url,
                "expiry": ""
            })

        await browser.close()
        return results

async def main():
    new_offers = await scrape_myntra_offers()

    # load existing
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
    else:
        existing = []

    # append & save
    combined = existing + new_offers
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"Loaded {len(existing)} existing, scraped {len(new_offers)} new, total {len(combined)} → {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
