import urllib.request
import urllib.parse
import json
import logging
import re

logger = logging.getLogger(__name__)

class TextTranslator:
    def __init__(self):
        self.google_clients = ['dict-chrome-ex', 'at', 'it']
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def _google_translate(self, text, target_lang="zh-TW", source_lang="ja"):
        """
        Free and unlimited Google Translate using Chrome extension and mobile client IDs.
        These client IDs bypass datacenter 429 IP bans.
        """
        if not text or not text.strip():
            return text

        for client in self.google_clients:
            try:
                url = (
                    "https://translate.googleapis.com/translate_a/single?"
                    f"client={client}&sl={source_lang}&tl={target_lang}&dt=t&q="
                    + urllib.parse.quote(text)
                )
                req = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        if data and data[0]:
                            parts = [p[0] for p in data[0] if p and p[0]]
                            translated = "".join(parts).strip()
                            if translated:
                                return translated
            except Exception as e:
                logger.debug(f"Google translate client {client} failed: {e}")
                continue

        return None

    def _mymemory_translate(self, text, target_lang="zh-TW", source_lang="ja"):
        """
        Backup free translator using MyMemory API.
        """
        if not text or not text.strip():
            return text
        try:
            url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair={source_lang}|{target_lang}"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                res = data.get("responseData", {}).get("translatedText")
                if res and "MYMEMORY WARNING" not in res:
                    return res.strip()
        except Exception as e:
            logger.debug(f"MyMemory translation error: {e}")
        return None

    def translate_to_chinese(self, text):
        if not text or not text.strip():
            return ""

        # 1. Try Google Translate (dict-chrome-ex / at / it)
        trans = self._google_translate(text)
        if trans:
            return trans

        # 2. Try MyMemory
        trans = self._mymemory_translate(text)
        if trans:
            return trans

        return text

    def translate_video(self, video):
        """
        Translates title and tags of a video object to Traditional Chinese.
        """
        if not video:
            return video

        raw_title = video.get('title', '')
        code = video.get('code', '')
        tags = video.get('tags', [])

        # Clean title before translating: remove leading code if present (e.g., "SNOS-413 ")
        clean_title = raw_title
        if code:
            code_pattern = re.escape(code)
            clean_title = re.sub(rf'^{code_pattern}\s*', '', clean_title, flags=re.I)
        # Also strip generic prefix like ABC-123
        clean_title = re.sub(r'^[A-Za-z0-9]+-[0-9]+\s*', '', clean_title, flags=re.I).strip()

        if clean_title:
            zh_title = self.translate_to_chinese(clean_title)
            video['title_zh'] = zh_title
            video['title'] = zh_title
        else:
            video['title_zh'] = raw_title

        # Translate tags
        translated_tags = []
        for tag in tags:
            # Don't translate pure codes or short English acronyms
            if re.match(r'^[A-Za-z0-9_-]+$', tag):
                translated_tags.append(tag)
            else:
                zh_tag = self.translate_to_chinese(tag)
                translated_tags.append(zh_tag or tag)

        video['tags_zh'] = translated_tags
        video['tags'] = translated_tags

        return video


if __name__ == "__main__":
    t = TextTranslator()
    test_video = {
        'code': 'SNOS-413',
        'title': 'SNOS-413 「先生ともっと一緒にいたいです…」 ウブな図書委員の雫のような美乳に我を失い何度も吐精してしまった担任教師 早坂奏音',
        'tags': ['パイズリ', '女子校生', '巨乳', '早坂奏音']
    }
    res = t.translate_video(test_video)
    print("Translated Video:")
    print("Title:", res['title_zh'])
    print("Tags:", res['tags_zh'])
