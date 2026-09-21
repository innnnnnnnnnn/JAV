import requests
from bs4 import BeautifulSoup
from datetime import datetime

class OneJAVCrawler:
    BASE_URL = "https://onejav.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def get_video_by_code(self, code):
        """
        Search for a specific code and return the video info (primarily the new torrent URL).
        """
        url = f"{self.BASE_URL}/search/{code}"
        print(f"Searching for code: {code} at {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                print(f"Search failed for {code}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error searching for {code}: {e}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        cards = soup.select('.card')
        
        for card in cards:
            # Check if this card matches the code
            title_tag = card.select_one('.title a')
            if title_tag:
                found_code = title_tag.get_text(strip=True).upper()
                # Remove hyphens for comparison if needed, or just exact match
                if code.upper().replace('-', '') == found_code.replace('-', ''):
                    video = {'code': found_code}
                    
                    # Torrent Link
                    torrent_tag = card.select_one('a.button.is-primary.is-fullwidth')
                    if torrent_tag:
                        href = torrent_tag.get('href')
                        if href:
                            video['torrent_url'] = self.BASE_URL + href
                    
                    # Title
                    level_tag = card.select_one('.level.has-text-grey-dark')
                    if level_tag:
                        video['title'] = level_tag.get_text(strip=True)
                        
                    return video

        print(f"No exact match found for {code} in search results.")
        return None

    def get_daily_videos(self, date_str=None):
        """
        date_str: YYYY/MM/DD
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y/%m/%d")
        
        videos = []
        page = 1
        
        while True:
            url = f"{self.BASE_URL}/{date_str}?page={page}"
            print(f"Fetching: {url}")
            
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code != 200:
                    print(f"Reached end of pages or failed at page {page}: {response.status_code}")
                    break
            except Exception as e:
                print(f"Error fetching page {page}: {e}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            cards = soup.select('.card')
            
            if not cards:
                print(f"No cards found on page {page}. Stopping.")
                break
            
            found_on_page = 0
            for card in cards:
                video = {}
                
                # Code and Size
                title_tag = card.select_one('.title a')
                if title_tag:
                    video['code'] = title_tag.get_text(strip=True)
                    
                size_tag = card.select_one('.title .is-size-6')
                if size_tag:
                    video['size'] = size_tag.get_text(strip=True)
                
                # Title/Description
                level_tag = card.select_one('.level.has-text-grey-dark')
                if level_tag:
                    video['title'] = level_tag.get_text(strip=True)
                
                # Image
                img_tag = card.select_one('img.image')
                if img_tag:
                    video['image'] = img_tag.get('src')
                
                # Tags
                tags = [tag.get_text(strip=True) for tag in card.select('.tag')]
                video['tags'] = tags
                
                # Torrent Link
                torrent_tag = card.select_one('a.button.is-primary.is-fullwidth')
                if torrent_tag:
                    href = torrent_tag.get('href')
                    if href:
                        video['torrent_url'] = self.BASE_URL + href
                
                if 'code' in video:
                    videos.append(video)
                    found_on_page += 1
            
            print(f"Found {found_on_page} videos on page {page}.")
            page += 1
            
            # Anti-abuse delay
            import time
            time.sleep(0.5)

        return videos

if __name__ == "__main__":
    crawler = OneJAVCrawler()
    # Test with today's date if possible or a known date
    # current_date = datetime.now().strftime("%Y/%m/%d")
    test_date = "2026/03/29"
    results = crawler.get_daily_videos(test_date)
    for v in results[:3]:
        print(v)
