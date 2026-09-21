import deepl

DEEPL_API_KEY = "7c19ad26-b310-4a6a-8575-ccc1fd474b04:fx"

class TextTranslator:
    def __init__(self):
        self.translator = deepl.Translator(DEEPL_API_KEY)

    def translate_to_chinese(self, text):
        if not text:
            return ""
            
        try:
            result = self.translator.translate_text(text, target_lang="ZH-HANT")
            return result.text
        except Exception as e:
            print(f"DeepL Translation error: {e}")
            
        return text

    def translate_video(self, video):
        """
        Translates title and tags of a video object in a single API call.
        """
        texts_to_translate = []
        has_title = bool(video.get('title'))
        tags = video.get('tags', [])
        
        if has_title:
            texts_to_translate.append(video['title'])
            
        texts_to_translate.extend(tags)
        
        if texts_to_translate:
            try:
                # DeepL Python library can take a list of strings
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
                    video['title'] = ""
                    
                translated_tags = result_texts[idx:]
                video['tags_zh'] = translated_tags
                video['tags'] = translated_tags
                
            except Exception as e:
                print(f"DeepL Translation error: {e}")
                video['title_zh'] = video.get('title', '')
                video['tags_zh'] = tags
        else:
            video['title_zh'] = ""
            video['title'] = ""
            video['tags_zh'] = []
            video['tags'] = []
            
        return video

if __name__ == "__main__":
    translator = TextTranslator()
    sample = {
        "title": "Beautiful girl in the rain",
        "tags": ["Action", "Romance"]
    }
    translated = translator.translate_video(sample)
    print(translated)
