import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime
import signal
from concurrent.futures import ThreadPoolExecutor
import sys

class KompasNewsCrawler:
    def __init__(self):
        self.base_url = "https://www.kompas.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.kompas.com/',
            'Connection': 'keep-alive',
        }
        self.articles = []
        self.processed_urls = set()  # 처리된 URL을 저장할 set
        self.is_running = True
        self.session = None
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        print("\n크롤링을 중단합니다...")
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
                    logging.info(f"HTML 응답 길이: {len(html)}")
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    logging.info("페이지 주요 섹션:")
                    for tag in soup.find_all(['div', 'section'], class_=True)[:10]:
                        logging.info(f"태그: {tag.name}, 클래스: {tag.get('class')}")
                    
                    return html
                logging.error(f"HTTP 에러: {response.status}")
                return None
        except Exception as e:
            logging.error(f"URL 요청 중 에러 발생: {url}, 에러: {str(e)}")
            return None

    async def fetch_article_content(self, url):
        try:
            async with self.session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 기사 본문 선택자
                    content_elem = soup.select_one('.read__content')
                    if content_elem:
                        # 본문의 모든 문단을 가져와서 합침
                        paragraphs = content_elem.select('p')
                        content = ' '.join([p.text.strip() for p in paragraphs])
                        return content
                return ''
        except Exception as e:
            logging.error(f"기사 본문 가져오기 실패: {url}, 에러: {str(e)}")
            return ''

    async def parse_article_list(self, html, category):
        soup = BeautifulSoup(html, 'html.parser')
        logging.info("HTML 파싱 시작")
        
        articles = soup.select('.article__list')
        logging.info(f"발견된 기사 수: {len(articles)}")
        
        tasks = []
        parsed_articles = []
        
        for article in articles:
            if not self.is_running:
                break
                
            try:
                title_elem = article.select_one('a')
                
                if title_elem:
                    article_url = title_elem.get('href')
                    
                    # URL이 이미 처리된 경우 건너뛰기
                    if article_url in self.processed_urls:
                        logging.info(f"중복 기사 건너뛰기: {title_elem.text.strip()[:30]}...")
                        continue
                    
                    article_data = {
                        'title': title_elem.text.strip(),
                        'article_url': article_url,
                        'category': category,
                        'date': ''
                    }
                    
                    if self.is_valid_content(article_data['title']):
                        self.processed_urls.add(article_url)  # URL 추가
                        tasks.append(self.fetch_article_content(article_url))
                        parsed_articles.append(article_data)
                        logging.info(f"새로운 기사 발견: {article_data['title'][:30]}...")
            
            except Exception as e:
                logging.error(f"기사 파싱 중 에러 발생: {str(e)}")
                continue
        
        # 모든 기사 본문을 동시에 가져옴
        if tasks:
            contents = await asyncio.gather(*tasks)
            for article, content in zip(parsed_articles, contents):
                article['content'] = content
        
        logging.info(f"이 페이지에서 파싱된 새로운 기사 수: {len(parsed_articles)}")
        logging.info(f"총 처리된 고유 기사 수: {len(self.processed_urls)}")
        return parsed_articles

    async def crawl_category(self, category):
        page = 1
        try:
            await self.init_session()
            
            while self.is_running:
                url = f"{self.base_url}/tag/{category}?page={page}"
                logging.info(f"페이지 크롤링 중: {url}")
                
                html = await self.get_page_content(url)
                if not html:
                    break

                new_articles = await self.parse_article_list(html, category)
                if not new_articles:
                    logging.info(f"더 이상 새로운 기사가 없습니다. 마지막 페이지: {page}")
                    break
                
                self.articles.extend(new_articles)
                page += 1
                await asyncio.sleep(0.5)
                
        finally:
            await self.close_session()
            logging.info(f"크롤링 완료. 총 수집된 고유 기사 수: {len(self.processed_urls)}")

    def save_to_json(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'total_articles': len(self.articles),
                'articles': self.articles
            }, f, ensure_ascii=False, indent=2)
        logging.info(f"데이터가 {filename}에 저장되었습니다.")

async def main():
    crawler = KompasNewsCrawler()
    category = input("크롤링할 카테고리를 입력하세요 (예: wellness): ")
    
    print("크롤링을 시작합니다. 중단하려면 Ctrl+C를 누르세요.")
    
    start_time = datetime.now()
    logging.info(f"크롤링 시작: {start_time}")
    
    try:
        await crawler.crawl_category(category)
    except Exception as e:
        logging.error(f"크롤링 중 오류 발생: {str(e)}")
    finally:
        if crawler.articles:
            filename = f"kompas_{category}_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
            crawler.save_to_json(filename)
            
            end_time = datetime.now()
            logging.info(f"크롤링 {'완료' if crawler.is_running else '중단'}: {end_time}")
            logging.info(f"총 소요시간: {end_time - start_time}")
            logging.info(f"수집된 총 기사 수: {len(crawler.articles)}")

if __name__ == "__main__":
    asyncio.run(main())
