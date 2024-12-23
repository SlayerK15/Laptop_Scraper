# src/utils/config.py
import random

# URLs for laptop listings
LAPTOP_URLS = [
    "https://www.amazon.in/s?i=computers&rh=n%3A1375424031%2Cp_123%3A110955%2Cp_n_condition-type%3A8609960031&s=popularity-rank&dc&fs=true&qid=1734952189&rnid=8609959031&ref=sr_nr_p_n_condition-type_1&ds=v1%3AaHJuJcWCckD1PNjoM3r%2B6yetBRIw3xTOb5tdaCSnjTU",
    "https://www.amazon.in/s?i=computers&rh=n%3A976392031%2Cn%3A1375424031%2Cp_123%3A308445%2Cp_n_condition-type%3A8609960031&s=popularity-rank&dc&fs=true&ds=v1%3Ao3LoCk2sb%2FDKwc0bXdeE6OCYBgMRoffJPwwLXYIdHio&qid=1734952239&ref=sr_ex_n_1",
    "https://www.amazon.in/s?i=computers&rh=n%3A1375424031%2Cp_n_condition-type%3A8609960031%2Cp_123%3A391242&s=popularity-rank&dc&fs=true&ds=v1%3A6QJ0V3GwPj63QF3fdaqutr4yb%2B%2FvfGzYr5xFzDeDDNw&qid=1734645356&rnid=91049095031&ref=sr_nr_p_123_1",
    "https://www.amazon.in/s?i=computers&rh=n%3A1375424031%2Cp_n_condition-type%3A8609960031%2Cp_123%3A219979&s=popularity-rank&dc&fs=true&ds=v1%3AORH4hW9cI123nFdep2YGVohvEhcKnGaBtzxa%2Bum0Ex8&qid=1734645428&rnid=91049095031&ref=sr_nr_p_123_2",
    "https://www.amazon.in/s?i=computers&rh=n%3A1375424031%2Cp_n_condition-type%3A8609960031%2Cp_123%3A247341&s=popularity-rank&dc&fs=true&ds=v1%3AjKEmTy4Xl5HNzPs63%2BNQCfgsLqkT7ouBs9NqTbaFzXo&qid=1734645448&rnid=91049095031&ref=sr_nr_p_123_1",
    "https://www.amazon.in/s?i=computers&rh=n%3A1375424031%2Cp_n_condition-type%3A8609960031%2Cp_123%3A241862&s=popularity-rank&dc&fs=true&ds=v1%3A%2BmvyY5H6kdeipgSo2vwQagATvMIAEv%2BkEXujEwj4G4E&qid=1734645462&rnid=91049095031&ref=sr_nr_p_123_2",
    "https://www.amazon.in/s?i=computers&rh=n%3A1375424031%2Cp_n_condition-type%3A8609960031%2Cp_123%3A378555&s=popularity-rank&dc&fs=true&qid=1734645477&rnid=91049095031&ref=sr_nr_p_123_1&ds=v1%3A10EkrlUMuF5ej28H7x%2BBpTYo1MXx5Tp%2FCcAxP5YcFME",
    "https://www.amazon.in/s?i=computers&rh=n%3A1375424031%2Cp_n_condition-type%3A8609960031%2Cp_123%3A46655&s=popularity-rank&dc&fs=true&ds=v1%3Av%2BgWlo66LCF89x7QZtz0x6OJqjwDp%2FY7LYn6hRpnRho&qid=1734645496&rnid=91049095031&ref=sr_nr_p_123_1",
    "https://www.amazon.in/s?i=computers&rh=n%3A1375424031%2Cp_n_condition-type%3A8609960031%2Cp_123%3A1500397&s=popularity-rank&dc&fs=true&ds=v1%3A2ue6KLcxDHee9TvzViFExCiXgzDEhLqWPE27VagfBow&qid=1734645512&rnid=91049095031&ref=sr_nr_p_123_2",
    ]

# MongoDB settings
MONGODB_URI = "mongodb://localhost:27017"
DATABASE_NAME = "raw_laptop_data"
COLLECTION_NAME = "raw_pages"

# List of User-Agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Edge/120.0.0.0"
]

def get_random_headers():
    """Generate random headers for each request"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "Pragma": "no-cache"
    }

# Crawler settings
MAX_PAGES = 80
DELAY_BETWEEN_REQUESTS = 1
DELAY_BETWEEN_PAGES = 2
MAX_RETRIES = 3
RETRY_DELAY = 5

# Logging settings
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = 'logs/crawler.log'
