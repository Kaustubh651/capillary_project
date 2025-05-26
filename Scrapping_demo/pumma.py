# puma_scraper_json.py
import asyncio
import json
import os
from urllib.parse import urljoin
from playwright.async_api import async_playwright

PUMA_DEALS_URL = "https://in.puma.com/in/en/shop-all-apparel"
OUTPUT_FILE = "puma_offers.json"

async def scrape_puma_deals():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(PUMA_DEALS_URL)
        await page.wait_for_selector("[data-test-id=product-list-item]")

        items = await page.query_selector_all("[data-test-id=product-list-item]")
        offers = []
        for item in items:
            # Title
            h3 = await item.query_selector("h3")
            title = (await h3.inner_text()).strip() if h3 else ""

            # Description
            promo = await item.query_selector("[data-test-id=promotion-callout-message]")
            description = (await promo.inner_text()).strip() if promo else ""

            # Expiry (not provided on Puma deals page)
            expiry = ""

            # Brand
            brand = "PUMA"

            # Offer link (absolute URL)
            a = await item.query_selector("a[data-test-id=product-list-item-link]")
            href = await a.get_attribute("href") if a else ""
            link = urljoin(PUMA_DEALS_URL, href) if href else ""

            offers.append({
                "title": title,
                "description": description,
                "expiry": expiry,
                "brand": brand,
                "link": link
            })

        await browser.close()
        return offers

async def main():
    new_offers = await scrape_puma_deals()

    # load existing offers if file exists
    if os.path.isfile(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
                if not isinstance(existing, list):
                    existing = []
            except json.JSONDecodeError:
                existing = []
    else:
        existing = []

    # append new offers
    combined = existing + new_offers

    # write back
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"Loaded {len(existing)} existing, added {len(new_offers)} new, total {len(combined)} → {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
