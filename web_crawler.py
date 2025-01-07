import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import logging
import signal
import sys

class KompasNewsCrawler:
    def __init__(self):
        self.base_url = "https://www.kompas.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.articles = []
        self.is_running = True
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Ctrl+C 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Ctrl+C 입력 시 호출되는 핸들러"""
        print("\n크롤링을 중단합니다...")
        self.is_running = False

    def get_page_content(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logging.error(f"URL 요청 중 에러 발생: {url}, 에러: {str(e)}")
            return None

    def parse_article(self, article_url, category):
        content_html = self.get_page_content(article_url)
        if not content_html:
            return None

        soup = BeautifulSoup(content_html, 'html.parser')
        
        try:
            title = soup.select_one('.read__title').text.strip() if soup.select_one('.read__title') else \
                    soup.select_one('.article__title').text.strip()
            date = soup.select_one('.article__date').text.strip() if soup.select_one('.article__date') else \
                   soup.select_one('.read__time').text.strip()
            content = ' '.join([p.text.strip() for p in soup.select('.article__text p')])
            
            article_data = {
                'title': title,
                'content': content,
                'date': date,
                'article_url': article_url,
                'category': category
            }
            return article_data
            
        except Exception as e:
            logging.error(f"기사 파싱 중 에러 발생: {article_url}, 에러: {str(e)}")
            return None

    def crawl_category(self, category):
        page = 1
        while self.is_running:  # is_running 플래그 확인
            url = f"{self.base_url}/tag/{category}?page={page}"
            logging.info(f"페이지 크롤링 중: {url}")
            
            page_html = self.get_page_content(url)
            if not page_html:
                break

            soup = BeautifulSoup(page_html, 'html.parser')
            article_links = soup.select('.article__list .article__link')
            
            if not article_links:
                logging.info(f"더 이상 기사가 없습니다. 마지막 페이지: {page}")
                break

            for link in article_links:
                if not self.is_running:  # 각 기사 처리 전 중단 여부 확인
                    break
                    
                article_url = link.get('href')
                if article_url:
                    article_data = self.parse_article(article_url, category)
                    if article_data:
                        self.articles.append(article_data)
                        logging.info(f"기사 수집 완료: {article_data['title']}")
                    time.sleep(1)

            if not self.is_running:  # 다음 페이지로 넘어가기 전 중단 여부 확인
                break
                
            page += 1
            time.sleep(2)

    def save_to_json(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({'articles': self.articles}, f, ensure_ascii=False, indent=2)
        logging.info(f"데이터가 {filename}에 저장되었습니다.")

def main():
    crawler = KompasNewsCrawler()
    category = input("크롤링할 카테고리를 입력하세요 (예: sports): ")
    
    print("크롤링을 시작합니다. 중단하려면 Ctrl+C를 누르세요.")
    
    start_time = datetime.now()
    logging.info(f"크롤링 시작: {start_time}")
    
    try:
        crawler.crawl_category(category)
    except Exception as e:
        logging.error(f"크롤링 중 오류 발생: {str(e)}")
    finally:
        if crawler.articles:  # 수집된 기사가 있는 경우에만 저장
            filename = f"kompas_{category}_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
            crawler.save_to_json(filename)
            
            end_time = datetime.now()
            logging.info(f"크롤링 {'완료' if crawler.is_running else '중단'}: {end_time}")
            logging.info(f"총 소요시간: {end_time - start_time}")
            logging.info(f"수집된 총 기사 수: {len(crawler.articles)}")

if __name__ == "__main__":
    main()
