import asyncio
import logging
from app.scraper import fetch_shops

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

async def main():
    # Example product code and prefecture
    # Note: This product code might not be valid, but we test the mechanism.
    # If we had a real product code from the research phase, we would use it.
    # Since we couldn't find one, we'll use a dummy or try to find one if possible.
    # Let's use a likely invalid one to see how it handles empty results, 
    # or if we can find a real one, that's better.
    
    # Trying a generic test.
    product_code = "4549660700000" # Random JAN-like code, likely no results
    pref = "東京都"
    
    print(f"Testing scraper for {pref} - {product_code}...")
    shops = await fetch_shops(product_code, pref)
    
    print(f"Found {len(shops)} shops.")
    for shop in shops:
        print(f"- {shop['name']}: {shop['address']}")

if __name__ == "__main__":
    asyncio.run(main())
