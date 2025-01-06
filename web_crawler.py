import requests
from bs4 import BeautifulSoup

def is_advertisement(element):
    # Check for advertisement-related elements
    ad_indicators = ['ad', 'ads', 'advertisement', 'sponsor', 'promoted']
    classes = element.get('class', [])
    id_attr = element.get('id', '')
    
    return any(indicator in ' '.join(classes).lower() or indicator in id_attr.lower() 
              for indicator in ad_indicators)

def get_content_quality(text):
    # Evaluate text quality based on length
    if len(text) < 20:
        return "low"
    elif len(text) < 100:
        return "medium"
    return "high"

def guess_content_label(text):
    # Estimate content label based on keywords
    categories = {
        'tech': ['programming', 'software', 'technology', 'computer', 'digital'],
        'sports': ['football', 'basketball', 'sports', 'athlete', 'game'],
        'news': ['breaking', 'report', 'announced', 'according'],
        'education': ['learning', 'study', 'education', 'academic', 'school']
    }
    
    text_lower = text.lower()
    for label, keywords in categories.items():
        if any(keyword in text_lower for keyword in keywords):
            return label
    return "general"

def is_menu_or_button(text):
    # Identify menu items, buttons, logos, etc.
    menu_patterns = [
        'menu', 'home', 'login', 'signup', 'search', 'about', 'contact',
        '메뉴', '홈', '로그인', '회원가입', '검색', '소개', '연락처'
    ]
    
    # Check if text has 3 or fewer words and each word is short
    words = text.split()
    if len(words) <= 3:
        return True
    
    # Check for menu/button patterns
    text_lower = text.lower()
    if any(pattern in text_lower for pattern in menu_patterns):
        return True
        
    # Check for special characters in short text
    if len(text) < 15 and any(char in text for char in '»>→◀▶▼▲'):
        return True
        
    return False

def crawl_website(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all non-advertisement text elements
        text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div'])
        
        results = []
        for element in text_elements:
            if is_advertisement(element):
                continue
                
            text = element.get_text().strip()
            words = text.split()
            
            # Enhanced text filtering conditions
            if (text and 
                len(words) > 3 and  # More than 3 words
                len(text) > 15 and  # Minimum length
                not is_menu_or_button(text) and  # Not a menu/button
                not text.isupper()):  # Not all uppercase
                
                result = {
                    "text": text,
                    "metadata": {
                        "label": guess_content_label(text),
                        "url": url,
                        "quality": get_content_quality(text),
                        "tag_name": element.name,
                        "classes": element.get('class', []),
                    }
                }
                results.append(result)

        # Save results to JSON file
        import json
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "url": url,
                "crawled_at": datetime.now().isoformat(),
                "total_items": len(results),
                "items": results
            }, f, ensure_ascii=False, indent=2)
            
        print(f"\nCrawling results saved to {filename}")
        return results

    except requests.exceptions.RequestException as e:
        print(f"Error occurred while fetching the webpage: {e}")
        return []

# Usage example
url = "https://lifestyle.kompas.com/fashion"
results = crawl_website(url)