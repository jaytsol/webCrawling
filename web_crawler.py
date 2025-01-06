import requests
from bs4 import BeautifulSoup

def crawl_website(url, keyword):
    try:
        # 웹 페이지 요청
        response = requests.get(url)
        response.raise_for_status()  # 요청이 성공했는지 확인

        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')

        # 페이지에서 모든 텍스트 추출
        text = soup.get_text()

        # 키워드 검색
        if keyword.lower() in text.lower():
            print(f"'{keyword}'가 페이지에 포함되어 있습니다.")
        else:
            print(f"'{keyword}'가 페이지에 포함되어 있지 않습니다.")

    except requests.exceptions.RequestException as e:
        print(f"웹 페이지를 가져오는 중 오류가 발생했습니다: {e}")

# 사용 예시
url = "https://kompas.com"
keyword = "sport"
crawl_website(url, keyword)