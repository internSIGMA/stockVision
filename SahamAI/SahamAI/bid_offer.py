import requests
from bs4 import BeautifulSoup

def get_bid_offer(stock_code):
    url = f"https://www.rti.co.id/stock/{stock_code}"
    
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Contoh parsing (HARUS disesuaikan dengan struktur HTML terbaru)
    bid_table = soup.find("table", {"id": "bid"})
    offer_table = soup.find("table", {"id": "offer"})
    
    bid_data = []
    offer_data = []
    
    if bid_table:
        rows = bid_table.find_all("tr")
        for row in rows[1:]:
            cols = row.find_all("td")
            bid_data.append({
                "price": cols[0].text.strip(),
                "lot": cols[1].text.strip()
            })
    
    if offer_table:
        rows = offer_table.find_all("tr")
        for row in rows[1:]:
            cols = row.find_all("td")
            offer_data.append({
                "price": cols[0].text.strip(),
                "lot": cols[1].text.strip()
            })
    
    return bid_data, offer_data

# contoh penggunaan
bid, offer = get_bid_offer("BBCA")
print("BID:", bid)
print("OFFER:", offer)