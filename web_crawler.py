from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
from datetime import datetime

def crawl_news_by_topic(topic):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 3)  # Increase wait time to 3 seconds
    
    try:
        # Construct URLs based on the topic
        base_url = "https://www.kompas.com/tag/"
        topic_url = f"{base_url}{topic}"
        
        print(f"\nTrying URL: {topic_url}")
        driver.get(topic_url)
        
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        
        print(f"Current page title: {driver.title}")
        
        selectors = [
            "//div[contains(@class, 'article__list')]//a",
            "//div[contains(@class, 'latest--article')]//a",
            "//div[contains(@class, 'col-bs10-7')]//a",
            "//div[contains(@class, 'gsc-webResult')]//a"
        ]
        
        results = []
        
        for selector in selectors:
            try:
                print(f"Trying selector: {selector}")
                articles = wait.until(
                    EC.presence_of_all_elements_located((By.XPATH, selector))
                )
                print(f"Found {len(articles)} articles with this selector")
                
                if articles:
                    for article in articles:
                        try:
                            link = article.get_attribute('href')
                            if not link or not link.startswith('http'):
                                continue
                                
                            print(f"Processing article: {link}")
                            
                            driver.execute_script(f"window.open('{link}', '_blank');")
                            driver.switch_to.window(driver.window_handles[-1])
                            
                            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                            
                            title = wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, '.read__title'))
                            ).text
                            
                            content = wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, '.read__content'))
                            ).text
                            
                            date = wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, '.read__time'))
                            ).text
                            
                            if title and content:
                                result = {
                                    "text": content,
                                    "metadata": {
                                        "title": title,
                                        "url": link,
                                        "date": date,
                                        "category": topic,
                                        "source": "Kompas.com"
                                    }
                                }
                                results.append(result)
                                print(f"Successfully collected: {title}")
                            
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
                            
                        except Exception as e:
                            print(f"Error processing individual article: {str(e)}")
                            if len(driver.window_handles) > 1:
                                driver.close()
                                driver.switch_to.window(driver.window_handles[0])
                            continue
                    
                    if results:
                        break
                        
            except Exception as e:
                print(f"Error with selector {selector}: {str(e)}")
                continue
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{topic}_news_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "category": topic,
                "crawled_at": datetime.now().isoformat(),
                "total_items": len(results),
                "items": results
            }, f, ensure_ascii=False, indent=2)
            
        print(f"\nCrawling results saved to {filename}")
        return results
        
    except Exception as e:
        print(f"Major error occurred: {str(e)}")
        return []
        
    finally:
        driver.quit()

if __name__ == "__main__":
    topic = input("Enter the topic you want to crawl: ")
    print(f"Starting crawler for topic: {topic}...")
    news = crawl_news_by_topic(topic)
    print(f"Crawler finished. Found {len(news)} articles.")