# src/crawler/raw_crawler.py

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import random
from pathlib import Path
from typing import List, Optional, Dict
import json
import time

from ..database.db_manager import DatabaseManager
from ..utils.config import get_random_headers, LAPTOP_URLS

class RawCrawler:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger('RawCrawler')
        self.urls = LAPTOP_URLS
        
        # Keywords to identify combo deals
        self.combo_keywords = [
            'combo', 'bundle', 'with bag', 'with mouse', 
            'with accessories', '+ mouse', '+ bag',
            'with backpack', '+ backpack', 'with headphone',
            'with keyboard', '+ keyboard', '+ headphone'
        ]

    async def create_session(self):
        """Create an aiohttp session with ScraperAPI proxy"""
        proxies = [
            "Add your Api keys here"
        ]
        
        connector = aiohttp.TCPConnector(
            ssl=False,
            limit=1  # Limit concurrent connections
        )
        
        timeout = aiohttp.ClientTimeout(
            total=60,      # Total timeout
            connect=10,    # Connection timeout
            sock_read=30   # Socket read timeout
        )
        
        if proxies:
            proxy = random.choice(proxies)
            return aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                proxy=proxy
            )
        else:
            return aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )

    def save_debug_html(self, content: str, page: int):
        """Save HTML content for debugging."""
        try:
            debug_dir = Path("debug_html")
            debug_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = debug_dir / f"page_{page}_{timestamp}.html"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.logger.debug(f"Saved debug HTML to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save debug HTML: {str(e)}")

    async def extract_product_links(self, session: aiohttp.ClientSession, base_url: str, page: int) -> List[str]:
        """Extract product URLs from a listing page."""
        retries = 0
        max_retries = 5
        base_delay = 10  # Base delay in seconds
        
        while retries < max_retries:
            try:
                url = f"{base_url}&page={page}"
                headers = get_random_headers()
                
                # Add random delay between requests
                await asyncio.sleep(random.uniform(5, 15))
                
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Save HTML for debugging
                        self.save_debug_html(content, page)
                        
                        # Debug log to check the content
                        self.logger.debug(f"Page content length: {len(content)}")
                        
                        # Check for bot detection
                        if "To discuss automated access to Amazon data please contact" in content:
                            raise Exception("Bot detection triggered")
                        if "api-services-support@amazon.com" in content:
                            raise Exception("Bot detection triggered")
                        if "Sorry, we just need to make sure you're not a robot" in content:
                            raise Exception("CAPTCHA detected")
                            
                        soup = BeautifulSoup(content, 'lxml')
                        
                        # Try different selectors that Amazon might use
                        products = []
                        selectors = [
                            'div[data-asin]:not([data-asin=""])',  # Standard product cards
                            'div.s-result-item[data-asin]:not([data-asin=""])',  # Alternative format
                            'div.sg-col-inner div[data-asin]:not([data-asin=""])',  # Another variation
                            '.s-main-slot div[data-asin]:not([data-asin=""])'  # Main slot products
                        ]
                        
                        for selector in selectors:
                            products = soup.select(selector)
                            if products:
                                self.logger.debug(f"Found products using selector: {selector}")
                                break
                        
                        if not products:
                            self.logger.warning(f"No products found on page {page} using any selector")
                            # Save the HTML content for inspection
                            debug_file = f"debug_html/no_products_page_{page}_{int(time.time())}.html"
                            with open(debug_file, 'w', encoding='utf-8') as f:
                                f.write(content)
                            return []
                            
                        links = []
                        for product in products:
                            try:
                                asin = product.get('data-asin')
                                if not asin:
                                    continue
                                    
                                # Try different title selectors
                                title_elem = None
                                title_selectors = [
                                    'h2 a.a-text-normal',
                                    'h2 span.a-text-normal',
                                    '.a-size-medium.a-text-normal',
                                    '.a-size-base-plus.a-text-normal',
                                    'h2 a span'  # Another common pattern
                                ]
                                
                                for selector in title_selectors:
                                    title_elem = product.select_one(selector)
                                    if title_elem:
                                        break
                                
                                if not title_elem:
                                    continue
                                    
                                title = title_elem.text.strip().lower()
                                
                                # Skip combo deals
                                if any(keyword in title for keyword in self.combo_keywords):
                                    self.logger.debug(f"Skipping combo deal: {title}")
                                    continue
                                
                                # Extract price if available
                                price_elem = product.select_one('.a-price-whole')
                                price = price_elem.text.strip() if price_elem else None
                                
                                product_url = f"https://www.amazon.in/dp/{asin}"
                                links.append(product_url)
                                self.logger.debug(f"Found product: {title} ({product_url}) - Price: {price}")
                                
                            except Exception as e:
                                self.logger.error(f"Error processing product: {str(e)}")
                                continue
                        
                        self.logger.info(f"Found {len(links)} valid products on page {page}")
                        return links
                        
                    elif response.status == 503 or response.status == 429:
                        retries += 1
                        delay = base_delay * (2 ** retries) + random.uniform(1, 5)
                        self.logger.warning(f"Rate limited (Status {response.status}). Retrying in {delay:.2f} seconds...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        self.logger.error(f"Failed to fetch page {page}: Status {response.status}")
                        return []
                        
            except Exception as e:
                self.logger.error(f"Error on page {page}: {str(e)}")
                retries += 1
                if retries < max_retries:
                    delay = base_delay * (2 ** retries) + random.uniform(1, 5)
                    self.logger.warning(f"Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"Max retries reached for page {page}")
                    return []
                    
        return []

    async def crawl_product(self, session: aiohttp.ClientSession, url: str) -> bool:
        """Crawl a single product page."""
        retries = 0
        max_retries = 3
        base_delay = 5
        
        while retries < max_retries:
            try:
                headers = get_random_headers()
                await asyncio.sleep(random.uniform(2, 5))  # Random delay
                
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status != 200:
                        if response.status in [503, 429]:
                            retries += 1
                            delay = base_delay * (2 ** retries) + random.uniform(1, 3)
                            self.logger.warning(f"Rate limited on product page. Retrying in {delay:.2f} seconds...")
                            await asyncio.sleep(delay)
                            continue
                        self.logger.error(f"Failed to fetch {url}: Status {response.status}")
                        return False
                        
                    content = await response.text()
                    
                    # Check for bot detection
                    if "To discuss automated access to Amazon data please contact" in content:
                        raise Exception("Bot detection triggered")
                    if "Sorry, we just need to make sure you're not a robot" in content:
                        raise Exception("CAPTCHA detected")
                    
                    # Basic validation that it's a laptop product page
                    soup = BeautifulSoup(content, 'lxml')
                    title_elem = soup.select_one('#productTitle')
                    if not title_elem:
                        self.logger.warning(f"No product title found for {url}")
                        return False
                    
                    title = title_elem.text.strip()
                    
                    # Skip if it's a combo deal
                    if any(keyword in title.lower() for keyword in self.combo_keywords):
                        self.logger.debug(f"Skipping combo deal product: {title}")
                        return False
                    
                    # Extract additional metadata
                    metadata = {
                        'title': title,
                        'asin': url.split('/dp/')[-1].split('/')[0],
                        'crawled_at': datetime.utcnow(),
                        'price': None,
                        'rating': None,
                        'num_reviews': None
                    }
                    
                    # Try to extract price
                    price_elem = soup.select_one('#priceblock_ourprice, #priceblock_dealprice, .a-price .a-offscreen')
                    if price_elem:
                        metadata['price'] = price_elem.text.strip()
                    
                    # Try to extract rating
                    rating_elem = soup.select_one('#acrPopover .a-text-normal')
                    if rating_elem:
                        metadata['rating'] = rating_elem.text.strip()
                    
                    # Try to extract number of reviews
                    reviews_elem = soup.select_one('#acrCustomerReviewText')
                    if reviews_elem:
                        metadata['num_reviews'] = reviews_elem.text.strip()
                    
                    # Store raw data
                    await self.db_manager.save_raw_data(
                        url=url,
                        html_content=content,
                        metadata=metadata
                    )
                    
                    self.logger.info(f"Successfully crawled {url}")
                    return True
                    
            except Exception as e:
                self.logger.error(f"Error crawling {url}: {str(e)}")
                retries += 1
                if retries < max_retries:
                    delay = base_delay * (2 ** retries)
                    await asyncio.sleep(delay)
                    continue
                return False
        
        return False

    async def run(self, max_pages: int = 20):
        """Main crawler function."""
        self.logger.info("Starting crawler")
        total_products = 0
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                session = await self.create_session()
                async with session:
                    # Process each URL
                    for url_index, base_url in enumerate(self.urls, 1):
                        self.logger.info(f"Processing URL {url_index}/{len(self.urls)}")
                        
                        # Crawl listing pages
                        for page in range(1, max_pages + 1):
                            self.logger.info(f"Processing page {page}")
                            
                            # Get product links from the page
                            links = await self.extract_product_links(session, base_url, page)
                            if not links:
                                self.logger.info(f"No more products found after page {page}")
                                break
                            
                            # Crawl each product
                            for link in links:
                                success = await self.crawl_product(session, link)
                                if success:
                                    total_products += 1
                                await asyncio.sleep(random.uniform(1, 3))  # Random delay between products
                            
                            await asyncio.sleep(random.uniform(2, 5))  # Random delay between pages
                        
                        # Delay between URLs
                        if url_index < len(self.urls):
                            await asyncio.sleep(random.uniform(5, 10))
                    
                    self.logger.info(f"Crawling completed. Total products processed: {total_products}")
                    return
                    
            except Exception as e:
                self.logger.error(f"Error in crawler run: {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    delay = 60 * retry_count  # Increase delay with each retry
                    self.logger.warning(f"Retrying entire crawl in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    self.logger.error("Max retries reached for crawler run")
                    break
        
        self.logger.info(f"Crawling completed with {total_products} products processed")