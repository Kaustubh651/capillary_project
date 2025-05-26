# nykaa.py
import asyncio
import json
import os
from playwright.async_api import async_playwright

PAGE_URL    = "https://www.nykaa.com/sp/offers-native/offers"
OUTPUT_FILE = "nykaa_offers.json"

async def scrape_nykaa_offers():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # go to the offers page
        await page.goto(PAGE_URL, wait_until="networkidle")

        # wait for the Next.js data blob
        await page.wait_for_selector("#__NEXT_DATA__", timeout=20000)

        # grab and parse the JSON state
        state = await page.eval_on_selector(
            "#__NEXT_DATA__",
            "el => JSON.parse(el.textContent)"
        )

        # navigate into the JSON to find the offers list
        offers = (
            state
            .get("props", {})
            .get("pageProps", {})
            .get("offerDetailsMetadata", {})
            .get("offersList", [])
        )

        await browser.close()
        return offers

async def main():
    raw = await scrape_nykaa_offers()

    # normalize
    cleaned = []
    for o in raw:
        cleaned.append({
            "name":       o.get("productName", "").strip(),
            "variant":    o.get("variantName", "").strip(),
            "sale_price": o.get("salePrice", "").strip(),
            "mrp_price":  o.get("mrpPrice", "").strip(),
            "discount":   o.get("discountPercent", "").strip(),
            "rating":     o.get("avgRating", "").strip(),
            "reviews":    o.get("ratingCount", "").strip(),
            "link":       "https://www.nykaa.com" + o.get("productUrl", ""),
            "image":      o.get("imageUrl", ""),
        })

    # merge with existing file if any
    if os.path.exists(OUTPUT_FILE):
        try:
            existing = json.load(open(OUTPUT_FILE, encoding="utf-8"))
        except json.JSONDecodeError:
            existing = []
    else:
        existing = []

    combined = existing + cleaned
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"Loaded {len(existing)} existing, scraped {len(cleaned)} new, total {len(combined)} → {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
