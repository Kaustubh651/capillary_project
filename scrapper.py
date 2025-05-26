# master.py
import asyncio
import json
import os
import re
import time
import requests

from urllib.parse import urljoin
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout, Error as PlaywrightError

MAX_SCROLL_TIME = 30  # seconds, for Nykaa paging

# ---------------- Nykaa ----------------
async def scrape_nykaa_offers(url="https://www.nykaa.com/brands/kay-beauty/c/11433?transaction_id=e612d9d74986189b8c99692e60ea4d94&intcmp=nykaa:plp:desktop-category-listing:all:banner:CAROUSEL_V2:1:Kay%20Beauty:11433:e612d9d74986189b8c99692e60ea4d94"):
    """
    Scrape Nykaa by hitting its internal API using the category ID extracted
    from the URL (/c/<id>).
    """
    m = re.search(r"/c/(\d+)", url)
    if not m:
        print(f"❌ Nykaa: invalid URL (no /c/<id>): {url}")
        return []

    cat_id = m.group(1)
    offers = []
    page_no   = 1
    start     = time.time()
    headers   = {"User-Agent": "Mozilla/5.0"}

    while time.time() - start < MAX_SCROLL_TIME:
        api = (
            "https://www.nykaa.com/app-api/index.php/products/list"
            f"?category_id={cat_id}&client=react&filter_format=v2"
            f"&page_no={page_no}&platform=website&sort=popularity"
        )
        try:
            resp = requests.get(api, headers=headers, timeout=30).json()
        except Exception as e:
            print(f"❌ Error fetching Nykaa API page {page_no}: {e}")
            break

        prods = resp.get("response", {}).get("products", [])
        if not prods:
            break

        for p in prods:
            name      = p.get("name", "")
            brand     = p.get("brand", "Nykaa")
            fp        = p.get("final_price", "")
            mrp       = p.get("mrp", "")
            slug      = p.get("slug", "")
            raw_disc  = p.get("discount", "")
            discount  = str(raw_disc).strip()

            offers.append({
                "site":        "Nykaa",
                "title":       f"{discount} off on {name}".strip(),
                "description": f"{name} by {brand} — ₹{fp} (MRP ₹{mrp})",
                "expiry":      p.get("expiry_date", "Not Mentioned"),
                "brand":       brand,
                "link":        f"https://www.nykaa.com{slug}",
                "discount":    discount,
                "image":       p.get("image_url", ""),
                "category":    cat_id,
            })
        page_no += 1

    print(f"✅ Nykaa: scraped {len(offers)} offers")
    return offers

# -------------- Flipkart --------------
OFFERS_URL   = "https://www.flipkart.com/offers-store"
BASE_URL     = "https://www.flipkart.com"

async def auto_scroll_flipkart(page, steps=10, delay=1000):
    prev = 0
    for _ in range(steps):
        curr = await page.evaluate("() => document.querySelectorAll('a._6WQwDJ').length")
        if curr == prev:
            break
        prev = curr
        await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        await page.wait_for_timeout(delay)
    return prev

async def scrape_flipkart_offers():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page    = await browser.new_page()
        await page.goto(OFFERS_URL, wait_until="load", timeout=30000)

        # dismiss login pop-up if present
        try:
            await page.click("button._2KpZ6l._2doB4z", timeout=2000)
        except PlaywrightTimeout:
            pass

        total = await auto_scroll_flipkart(page)
        if total == 0:
            print("❌ Flipkart: no deals found")
            await browser.close()
            return []

        tiles = await page.query_selector_all("a._6WQwDJ")
        results = []
        for t in tiles:
            href = await t.get_attribute("href") or ""
            link = urljoin(BASE_URL, href)

            title_el       = await t.query_selector("div._2N1WLe")
            desc_el        = await t.query_selector("div._3LU4EM")
            brand_el       = await t.query_selector("div._1xxHXK")

            title       = (await title_el.inner_text()).strip() if title_el else ""
            description = (await desc_el.inner_text()).strip() if desc_el else ""
            brand       = (await brand_el.inner_text()).strip() if brand_el else ""

            results.append({
                "site":        "Flipkart",
                "title":       title,
                "description": description,
                "brand":       brand,
                "link":        link,
                "expiry":      ""
            })

        await browser.close()
        print(f"✅ Flipkart: scraped {len(results)} deals")
        return results

# --------------- Puma -----------------
PUMA_DEALS_URL = "https://in.puma.com/in/en/motorsport"

async def scrape_puma_deals():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page    = await browser.new_page()
        await page.goto(PUMA_DEALS_URL, timeout=30000)
        await page.wait_for_selector("[data-test-id=product-list-item]")

        items = await page.query_selector_all("[data-test-id=product-list-item]")
        offers = []
        for item in items:
            title_el  = await item.query_selector("h3")
            promo_el  = await item.query_selector("[data-test-id=promotion-callout-message]")
            link_el   = await item.query_selector("a[data-test-id=product-list-item-link]")

            title       = (await title_el.inner_text()).strip() if title_el else ""
            description = (await promo_el.inner_text()).strip() if promo_el else ""
            href        = await link_el.get_attribute("href") if link_el else ""
            link        = urljoin(PUMA_DEALS_URL, href) if href else ""

            offers.append({
                "site":        "PUMA",
                "title":       title,
                "description": description,
                "expiry":      "",
                "brand":       "PUMA",
                "link":        link
            })

        await browser.close()
        print(f"✅ PUMA: scraped {len(offers)} items")
        return offers

# --------------- Main & merge ---------------
MASTER_FILE = "master_offers.json"

async def main():
    # run all three
    nykaa_offers    = await scrape_nykaa_offers()
    flipkart_offers = await scrape_flipkart_offers()
    puma_offers     = await scrape_puma_deals()

    all_new = nykaa_offers + flipkart_offers + puma_offers

    # load existing if present
    if os.path.exists(MASTER_FILE):
        with open(MASTER_FILE, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
                if not isinstance(existing, list):
                    existing = []
            except json.JSONDecodeError:
                existing = []
    else:
        existing = []

    combined = existing + all_new

    with open(MASTER_FILE, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"Loaded {len(existing)} existing, added {len(all_new)} new, total {len(combined)} → {MASTER_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
