# Web Crawler for Kompas.com

This web crawler allows you to scrape articles from Kompas.com based on user-defined topics. Below is a list of suggested keywords that can be used as topics for crawling.

## Available Topics

You can use the following keywords as topics to crawl articles from Kompas.com:

### Sports
- `sports`
- `football`
- `basketball`
- `tennis`
- `golf`

### Fashion
- `fashion`
- `style`
- `clothing`
- `beauty`
- `trends`

### Relationship
- `relationship`
- `love`
- `dating`
- `marriage`
- `family`

### Health
- `health`
- `fitness`
- `nutrition`
- `wellness`
- `medicine`

### Technology
- `technology`
- `gadgets`
- `innovation`
- `software`
- `hardware`

### Economy
- `economy`
- `finance`
- `business`
- `market`
- `investment`

### Politics
- `politics`
- `government`
- `election`
- `policy`
- `diplomacy`

### Education
- `education`
- `school`
- `university`
- `learning`
- `teaching`

### Travel
- `travel`
- `tourism`
- `destination`
- `adventure`
- `vacation`

### Food
- `food`
- `cuisine`
- `recipe`
- `cooking`
- `dining`

## How to Use

1. Run the `web_crawler.py` script.
2. Enter the topic you want to crawl when prompted.
3. The crawler will fetch articles related to the specified topic and save them in a JSON file.

## Note

- Ensure that the topic you enter is one of the available keywords listed above.
- The crawler uses Selenium and requires ChromeDriver to be installed.

## Kompas.com Selector Examples

When using the `NewsCrawler` class for Kompas.com, you can use the following CSS selectors:

- **Base URL**: `https://www.kompas.com`
- **Article List Selector**: `.article__list`
- **Article Content Selector**: `.read__content`
- **Date Selector**: `.read__time`

These selectors can be used as input when initializing the `NewsCrawler` class to scrape articles from Kompas.com. 