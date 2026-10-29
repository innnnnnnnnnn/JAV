import urllib.request
import urllib.parse
import json
import logging
try:
    import deepl
except ImportError:
    deepl = None
from config import DEEPL_API_KEY

logger = logging.getLogger(__name__)

class TextTranslator:
    def __init__(self):
        self.translator = None
        if deepl and DEEPL_API_KEY:
            try:
                self.translator = deepl.Translator(DEEPL_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize DeepL translator: {e}")

    def _google_translate(self, text, target_lang="zh-TW", source_lang="auto"):
        """
        Free fallback translation using Google Translate API endpoint.
        """
        if not text:
            return text
        try:
            url = (
                "https://translate.googleapis.com/translate_a/single?client=gtx"
                f"&sl={source_lang}&tl={target_lang}&dt=t&q=" + urllib.parse.quote(text)
            )
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data and data[0]:
                    parts = [part[0] for part in data[0] if part and part[0]]
                    return "".join(parts)
        except Exception as e:
            logger.error(f"Google Translation error: {e}")
        return text

    def translate_to_chinese(self, text):
        if not text:
            return ""

        if self.translator:
            try:
                result = self.translator.translate_text(text, target_lang="ZH-HANT")
                return result.text
            except Exception as e:
                logger.warning(f"DeepL Translation error ({e}), falling back to Google Translate...")

        return self._google_translate(text)

    def translate_video(self, video):
        """
        Translates title and tags of a video object.
        Tries DeepL first; if quota exceeded or fails, seamlessly falls back to Google Translate.
        """
        texts_to_translate = []
        has_title = bool(video.get('title'))
        tags = video.get('tags', [])

        if has_title:
            texts_to_translate.append(video['title'])

        texts_to_translate.extend(tags)

        if not texts_to_translate:
            video['title_zh'] = ""
            video['tags_zh'] = []
            return video

        # 1. Try DeepL
        translated_success = False
        if self.translator:
            try:
                results = self.translator.translate_text(texts_to_translate, target_lang="ZH-HANT")
                if not isinstance(results, list):
                    results = [results]

                result_texts = [r.text for r in results]
                idx = 0
                if has_title:
                    video['title_zh'] = result_texts[idx]
                    video['title'] = video['title_zh']
                    idx += 1
                else:
                    video['title_zh'] = ""

                translated_tags = result_texts[idx:]
                video['tags_zh'] = translated_tags
                video['tags'] = translated_tags
                translated_success = True
            except Exception as e:
                logger.warning(f"DeepL Translation error ({e}), falling back to Google Translate...")

        # 2. Fallback to Google Translate if DeepL failed or not available
        if not translated_success:
            if has_title:
                zh_title = self._google_translate(video.get('title', ''))
                video['title_zh'] = zh_title
                video['title'] = zh_title
            else:
                video['title_zh'] = ""

            translated_tags = [self._google_translate(t) for t in tags]
            video['tags_zh'] = translated_tags
            video['tags'] = translated_tags

        return video


if __name__ == "__main__":
    translator = TextTranslator()
    sample = {
        "title": "葵いぶきを限界集落に置いてきた。AV女優ならオッパイとマ○コだけで帰ってこい！",
        "tags": ["巨乳", "単体作品"]
    }
    translated = translator.translate_video(sample)
    print("Translated sample:")
    print("Title:", translated.get("title_zh"))
    print("Tags:", translated.get("tags_zh"))
