import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime
import signal
from concurrent.futures import ThreadPoolExecutor
import sys

class NewsCrawler:
    def __init__(self, base_url, article_list_selector, article_content_selector, date_selector, headers=None):
        self.base_url = base_url
        self.article_list_selector = article_list_selector
        self.article_content_selector = article_content_selector
        self.date_selector = date_selector
        self.headers = headers if headers else {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': base_url,
            'Connection': 'keep-alive',
        }
        self.articles = []
        self.processed_urls = set()
        self.is_running = True
        self.session = None
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        print("\nStopping the crawling process...")
        self.is_running = False

    def is_valid_content(self, text):
        if not text or len(text.strip()) < 15:
            return False
        if text.isupper():
            return False
        return True

    async def init_session(self):
        self.session = aiohttp.ClientSession()

    async def close_session(self):
        if self.session:
            await self.session.close()

    async def get_page_content(self, url):
        try:
            async with self.session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    html = await response.text()
                    with open('debug.html', 'w', encoding='utf-8') as f:
                        f.write(html)
                    logging.info(f"HTML response length: {len(html)}")
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    logging.info("Main sections of the page:")
                    for tag in soup.find_all(['div', 'section'], class_=True)[:10]:
                        logging.info(f"Tag: {tag.name}, Class: {tag.get('class')}")
                    
                    return html
                logging.error(f"HTTP error: {response.status}")
                return None
        except Exception as e:
            logging.error(f"Error occurred while requesting URL: {url}, Error: {str(e)}")
            return None

    async def fetch_article_content(self, url):
        try:
            async with self.session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    content_elem = soup.select_one(self.article_content_selector)
                    date_elem = soup.select_one(self.date_selector)
                    
                    content = ''
                    date = ''
                    
                    if content_elem:
                        paragraphs = content_elem.select('p')
                        content = ' '.join([p.text.strip() for p in paragraphs])
                    
                    if date_elem:
                        date = date_elem.text.strip()
                    
                    return {
                        'content': content,
                        'date': date
                    }
                return {'content': '', 'date': ''}
        except Exception as e:
            logging.error(f"Failed to fetch article content: {url}, Error: {str(e)}")
            return {'content': '', 'date': ''}

    async def parse_article_list(self, html, category):
        soup = BeautifulSoup(html, 'html.parser')
        logging.info("Starting HTML parsing")
        
        articles = soup.select(self.article_list_selector)
        logging.info(f"Number of articles found: {len(articles)}")
        
        tasks = []
        parsed_articles = []
        
        for article in articles:
            if not self.is_running:
                break
                
            try:
                title_elem = article.select_one('a')
                
                if title_elem:
                    article_url = title_elem.get('href')
                    
                    if article_url in self.processed_urls:
                        logging.info(f"Skipping duplicate article: {title_elem.text.strip()[:30]}...")
                        continue
                    
                    article_data = {
                        'title': title_elem.text.strip(),
                        'article_url': article_url,
                        'category': category,
                        'content': '',
                        'date': ''
                    }
                    
                    if self.is_valid_content(article_data['title']):
                        self.processed_urls.add(article_url)
                        tasks.append(self.fetch_article_content(article_url))
                        parsed_articles.append(article_data)
                        logging.info(f"New article found: {article_data['title'][:30]}...")
            
            except Exception as e:
                logging.error(f"Error occurred while parsing article: {str(e)}")
                continue
        
        if tasks:
            results = await asyncio.gather(*tasks)
            for article, result in zip(parsed_articles, results):
                article['content'] = result['content']
                article['date'] = result['date']
        
        logging.info(f"Number of new articles parsed from this page: {len(parsed_articles)}")
        logging.info(f"Total number of unique articles processed: {len(self.processed_urls)}")
        return parsed_articles

    async def crawl_category(self, category):
        page = 1
        try:
            await self.init_session()
            
            while self.is_running:
                url = f"{self.base_url}/tag/{category}?page={page}"
                logging.info(f"Crawling page: {url}")
                
                html = await self.get_page_content(url)
                if not html:
                    break

                new_articles = await self.parse_article_list(html, category)
                if not new_articles:
                    logging.info(f"No more new articles. Last page: {page}")
                    break
                
                self.articles.extend(new_articles)
                page += 1
                await asyncio.sleep(0.5)
                
        finally:
            await self.close_session()
            logging.info(f"Crawling completed. Total number of unique articles collected: {len(self.processed_urls)}")

    def save_to_json(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'total_articles': len(self.articles),
                'articles': self.articles
            }, f, ensure_ascii=False, indent=2)
        logging.info(f"Data saved to {filename}")

async def main():
    base_url = input("Enter the base URL of the news site: ")
    article_list_selector = input("Enter the CSS selector for the article list: ")
    article_content_selector = input("Enter the CSS selector for the article content: ")
    date_selector = input("Enter the CSS selector for the article date: ")
    category = input("Enter the category to crawl (e.g., wellness): ")
    
    crawler = NewsCrawler(base_url, article_list_selector, article_content_selector, date_selector)
    
    print("Starting the crawl. Press Ctrl+C to stop.")
    
    start_time = datetime.now()
    logging.info(f"Crawl started at {start_time}")
    
    try:
        await crawler.crawl_category(category)
    except Exception as e:
        logging.error(f"Error occurred during crawling: {str(e)}")
    finally:
        if crawler.articles:
            filename = f"{base_url.split('//')[1].split('/')[0]}_{category}_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
            crawler.save_to_json(filename)
            
            end_time = datetime.now()
            logging.info(f"Crawl completed {'successfully' if crawler.is_running else 'stopped'}: {end_time}")
            logging.info(f"Total time taken: {end_time - start_time}")
            logging.info(f"Total number of articles collected: {len(crawler.articles)}")

if __name__ == "__main__":
    asyncio.run(main())
