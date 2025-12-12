import httpx
from bs4 import BeautifulSoup
import logging
import asyncio

logger = logging.getLogger(__name__)

PREFECTURE_MAP = {
    "北海道": "01", "青森県": "02", "岩手県": "03", "宮城県": "04", "秋田県": "05", "山形県": "06", "福島県": "07",
    "茨城県": "08", "栃木県": "09", "群馬県": "10", "埼玉県": "11", "千葉県": "12", "東京都": "13", "神奈川県": "14",
    "新潟県": "15", "富山県": "16", "石川県": "17", "福井県": "18", "山梨県": "19", "長野県": "20",
    "岐阜県": "21", "静岡県": "22", "愛知県": "23", "三重県": "24", "滋賀県": "25", "京都府": "26",
    "大阪府": "27", "兵庫県": "28", "奈良県": "29", "和歌山県": "30", "鳥取県": "31", "島根県": "32",
    "岡山県": "33", "広島県": "34", "山口県": "35", "徳島県": "36", "香川県": "37", "愛媛県": "38", "高知県": "39",
    "福岡県": "40", "佐賀県": "41", "長崎県": "42", "熊本県": "43", "大分県": "44", "宮崎県": "45", "鹿児島県": "46",
    "沖縄県": "47"
}

async def fetch_shops(product_code: str, pref_name: str):
    """
    Scrapes gashapon.jp for shops stocking the product in the given prefecture.
    Returns a list of dictionaries containing shop details.
    """
    pref_code = PREFECTURE_MAP.get(pref_name)
    if not pref_code:
        logger.error(f"Invalid prefecture name: {pref_name}")
        return []

    url = "https://gashapon.jp/shop/gplus_list.php"
    params = {
        "pref": pref_code,
        "product_code": product_code
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            # Check if the response is valid HTML
            if "text/html" not in response.headers.get("content-type", ""):
                 logger.error(f"Unexpected content type: {response.headers.get('content-type')}")
                 return []

            return parse_shops(response.text)

    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred while fetching shops: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return []

def parse_shops(html_content: str):
    """
    Parses the HTML content to extract shop information.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    shops = []

    # Note: The selector below is based on observation of similar sites.
    # It might need adjustment if the actual HTML structure differs.
    # Assuming a list of shops in some container. 
    # Based on search results, it seems to be a list.
    
    # Trying to find shop list items. 
    # Since I cannot see the exact HTML, I will try to be generic but specific enough.
    # Usually shop lists are in <ul> or <div> with class like "shop-list" or similar.
    # I will look for elements that look like shop entries.
    
    # Strategy: Look for the main content area and then shop blocks.
    # If this fails during verification, I will need to adjust.
    
    # Common pattern in Japanese store locators:
    # <div class="shop_list"> ... <dl class="shop_detail"> ... <dt>Shop Name</dt> ...
    
    # Let's try to find elements that contain shop names.
    # I'll look for common class names found in such sites or generic structure.
    
    # Updated strategy based on typical Bandai sites:
    # Look for elements with class containing 'shop' or 'store'.
    
    # Placeholder implementation - needs verification against real HTML
    # I will try to find any list elements that contain text.
    
    # Let's assume a structure based on "gplus_list.php" naming.
    # It likely returns a list of shops.
    
    # Attempt 1: Look for specific classes if possible.
    # Since I don't have them, I will try to extract anything that looks like a shop name and address.
    
    # For now, I will implement a robust search for "shop names" assuming they are in headers or bold text within a list.
    
    # Let's try to find a container.
    main_content = soup.find("div", id="main_content") or soup.find("div", class_="main_content") or soup.body
    
    if not main_content:
        return []

    # This is a best-guess selector. 
    # In a real scenario, I would inspect the HTML. 
    # Since I can't, I will try to capture typical structures.
    shop_items = main_content.find_all("div", class_="shop-list-item") # Hypothetical class
    
    if not shop_items:
        # Fallback: try finding dl/dt/dd structures which are common for lists
        shop_items = main_content.find_all("dl", class_="shop_detail")

    if not shop_items:
         # Fallback 2: Try finding simple <li> elements inside a <ul> with class 'shop_list'
         ul = main_content.find("ul", class_="shop_list")
         if ul:
             shop_items = ul.find_all("li")

    for item in shop_items:
        name_el = item.find("h3") or item.find("dt") or item.find("strong")
        address_el = item.find("p", class_="address") or item.find("dd")
        
        if name_el:
            name = name_el.get_text(strip=True)
            address = address_el.get_text(strip=True) if address_el else "住所不明"
            shops.append({
                "name": name,
                "address": address
            })
            
    return shops
