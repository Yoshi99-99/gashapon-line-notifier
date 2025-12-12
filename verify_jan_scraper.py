import asyncio
import logging
from app.scraper import fetch_shops

logging.basicConfig(level=logging.INFO)

async def main():
    # User provided JAN code
    jan_code = "4582769860256000"
    pref = "東京都"
    
    print(f"Testing scraper for {pref} - {jan_code}...")
    shops = await fetch_shops(jan_code, pref)
    
    print(f"Found {len(shops)} shops.")
    for shop in shops:
        print(f"- {shop['name']}: {shop['address']}")

if __name__ == "__main__":
    asyncio.run(main())
