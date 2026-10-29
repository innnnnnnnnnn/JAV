import requests
import re
import time
from bs4 import BeautifulSoup
from datetime import datetime

class OneJAVCrawler:
    SOURCES = ["https://onejav.com", "https://ffjav.com"]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6"
        })

    def get_video_by_code(self, code):
        """
        Search for a specific code and return the video info (primarily the new torrent URL).
        Tries onejav.com first, and automatically falls back to ffjav.com if onejav is unavailable or returns 403.
        Supports automatic hyphenation fallback (e.g. SNOS413 <-> SNOS-413) to ensure 100% match rate.
        """
        code_norm = code.upper().replace('-', '')
        
        # Build query variants: e.g. ["SNOS413", "SNOS-413"] or ["SNOS-413", "SNOS413"]
        query_variants = [code]
        m = re.match(r'^([A-Za-z]+)(\d+)$', code)
        if m:
            hyphen_variant = f"{m.group(1)}-{m.group(2)}"
            if hyphen_variant not in query_variants:
                query_variants.append(hyphen_variant)
        elif '-' in code:
            dehyphen_variant = code.replace('-', '')
            if dehyphen_variant not in query_variants:
                query_variants.append(dehyphen_variant)

        for base_url in self.SOURCES:
            for q in query_variants:
                url = f"{base_url}/search/{q}"
                print(f"Searching for code: {q} at {url}")

                try:
                    response = self.session.get(url, timeout=12)
                    if response.status_code != 200:
                        print(f"[{base_url}] Search failed for {q}: {response.status_code}, trying next...")
                        break  # If domain returned 403 or error, move to next base_url
                except Exception as e:
                    print(f"[{base_url}] Error searching for {q}: {e}, trying next...")
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                cards = soup.select('.card')

                for card in cards:
                    torrent_tag = card.select_one('a.button.is-primary.is-fullwidth')
                    if not torrent_tag:
                        continue
                    href = torrent_tag.get('href')
                    if not href:
                        continue
                    torrent_url = href if href.startswith('http') else base_url + href

                    title_tag = card.select_one('.title a')
                    title_text = title_tag.get_text(strip=True) if title_tag else ''

                    # Match code: check torrent filename or title text
                    matched = False
                    found_code = code

                    m_code = re.search(r'(?:onejav|ffjav)\.com_([a-zA-Z0-9_-]+)\.torrent', href, re.I)
                    if m_code and m_code.group(1).upper().replace('-', '') == code_norm:
                        matched = True
                        found_code = m_code.group(1).upper()
                    elif code_norm in title_text.upper().replace('-', ''):
                        matched = True
                        tokens = title_text.split()
                        if tokens and tokens[0].upper().replace('-', '') == code_norm:
                            found_code = tokens[0].upper()

                    if matched:
                        level_tag = card.select_one('.level.has-text-grey-dark')
                        clean_title = level_tag.get_text(strip=True) if (level_tag and level_tag.get_text(strip=True)) else title_text
                        clean_title = re.sub(r'\s*torrent\s*$', '', clean_title, flags=re.I)
                        clean_title = re.sub(rf'^{re.escape(found_code)}\s*', '', clean_title, flags=re.I).strip()

                        size_tag = card.select_one('.title .is-size-6')
                        size = (size_tag.get_text(strip=True) if size_tag else "") or torrent_tag.get_text(strip=True)

                        img_tag = card.select_one('img.image')
                        image = img_tag.get('src') if img_tag else None

                        tags = [t.get_text(strip=True) for t in card.select('.tag')]

                        return {
                            'code': found_code or code,
                            'title': clean_title,
                            'size': size,
                            'image': image,
                            'tags': tags,
                            'torrent_url': torrent_url
                        }

                print(f"[{base_url}] No exact match found for {q} in search results.")

        return None

    def get_daily_videos(self, date_str=None):
        """
        date_str: YYYY/MM/DD
        Tries primary source first, falls back if failed.
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y/%m/%d")

        for base_url in self.SOURCES:
            videos = []
            page = 1
            source_failed = False
            print(f"Fetching daily videos from {base_url} for {date_str}...")

            while True:
                url = f"{base_url}/{date_str}?page={page}"
                print(f"Fetching: {url}")

                try:
                    response = self.session.get(url, timeout=12)
                    if response.status_code != 200:
                        print(f"[{base_url}] Reached end of pages or failed at page {page}: {response.status_code}")
                        if page == 1:
                            source_failed = True
                        break
                except Exception as e:
                    print(f"[{base_url}] Error fetching page {page}: {e}")
                    if page == 1:
                        source_failed = True
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                cards = soup.select('.card')

                if not cards:
                    print(f"[{base_url}] No cards found on page {page}. Stopping.")
                    break

                found_on_page = 0
                for card in cards:
                    torrent_tag = card.select_one('a.button.is-primary.is-fullwidth')
                    if not torrent_tag:
                        continue
                    href = torrent_tag.get('href')
                    if not href:
                        continue
                    torrent_url = href if href.startswith('http') else base_url + href

                    title_tag = card.select_one('.title a')
                    title_text = title_tag.get_text(strip=True) if title_tag else ''

                    # Extract code
                    code = title_text.split()[0] if title_text else ''
                    m = re.search(r'(?:onejav|ffjav)\.com_([a-zA-Z0-9_-]+)\.torrent', href, re.I)
                    if m:
                        code = m.group(1).upper()

                    level_tag = card.select_one('.level.has-text-grey-dark')
                    clean_title = level_tag.get_text(strip=True) if (level_tag and level_tag.get_text(strip=True)) else title_text
                    clean_title = re.sub(r'\s*torrent\s*$', '', clean_title, flags=re.I)
                    clean_title = re.sub(rf'^{re.escape(code)}\s*', '', clean_title, flags=re.I).strip()

                    size_tag = card.select_one('.title .is-size-6')
                    size = (size_tag.get_text(strip=True) if size_tag else "") or torrent_tag.get_text(strip=True)

                    img_tag = card.select_one('img.image')
                    image = img_tag.get('src') if img_tag else None

                    tags = [t.get_text(strip=True) for t in card.select('.tag')]

                    video = {
                        'code': code,
                        'size': size,
                        'title': clean_title,
                        'image': image,
                        'tags': tags,
                        'torrent_url': torrent_url
                    }

                    if code:
                        videos.append(video)
                        found_on_page += 1

                print(f"[{base_url}] Found {found_on_page} videos on page {page}.")
                page += 1
                time.sleep(0.5)

            if not source_failed and videos:
                return videos
            else:
                print(f"[{base_url}] Failed to get daily videos, trying next source...")

        return []

if __name__ == "__main__":
    crawler = OneJAVCrawler()
    test_code = "SKMJ801"
    print("Testing get_video_by_code:", crawler.get_video_by_code(test_code))
