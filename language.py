import time
import requests
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

from config import LANGUAGE_MAP, INDIC_SCRIPT_RANGES, SARVAM_TRANSLATE_API, SARVAM_API_KEY


# ================= VOICE CONFIG =================

def get_voice_config(selected_lang_name):
    """
    Bridges UI language label → Sarvam STT code + language_info for agents.
    Extend this dict to support more languages without changing any other file.
    """
    configs = {
        "Telugu": {"stt_code": "te-IN", "lang_code": "te", "is_roman": True},
        "Hindi":  {"stt_code": "hi-IN", "lang_code": "hi", "is_roman": True},
        "Tamil":  {"stt_code": "ta-IN", "lang_code": "ta", "is_roman": True},
        "Kannada":{"stt_code": "kn-IN", "lang_code": "kn", "is_roman": True},
        "English":{"stt_code": "en-IN", "lang_code": "en", "is_roman": False},
    }
    return configs.get(selected_lang_name, configs["Telugu"])


# ================= SCRIPT DETECTION =================

def has_native_script(text, lang_code):
    if lang_code not in INDIC_SCRIPT_RANGES:
        return False
    start, end = INDIC_SCRIPT_RANGES[lang_code]
    return any(start <= ord(c) <= end for c in text)


def is_completely_romanized(text):
    indic_ranges = list(INDIC_SCRIPT_RANGES.values())
    for char in text:
        code = ord(char)
        if 0x0600 <= code <= 0x06FF:
            return False
        for start, end in indic_ranges:
            if start <= code <= end:
                return False
    return True


def detect_user_language_and_script(text):
    text_is_romanized = is_completely_romanized(text)

    try:
        language_code = detect(text)
    except Exception:
        language_code = 'en'

    is_mixed = text_is_romanized and language_code != 'en'

    result = {
        'language_code': language_code,
        'language_name': LANGUAGE_MAP.get(language_code, 'English'),
        'is_romanized': text_is_romanized,
        'is_mixed': is_mixed,
    }

    print(f"🌍 Language Detection: {result['language_name']} | romanized: {text_is_romanized} | mixed: {is_mixed}")
    return result


# ================= TRANSLATION =================

def translate_to_english(text, source_lang_code, language_info):
    if source_lang_code == 'en':
        print(f"✅ Query already in English: {text[:100]}")
        return text

    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            headers = {
                "Authorization": f"Bearer {SARVAM_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "input": text,
                "source_language_code": "auto",
                "target_language_code": "en-IN",
            }

            print(f"🔄 Translating {language_info['language_name']} → English (Attempt {attempt + 1}/{max_retries})")
            res = requests.post(SARVAM_TRANSLATE_API, headers=headers, json=payload, timeout=30)

            if res.status_code == 200:
                translated = res.json().get("translated_text", "").strip()
                if translated and len(translated) > 2:
                    print(f"✅ Translation successful: {translated[:100]}")
                    return translated
            elif res.status_code == 429:
                time.sleep(retry_delay * 2)
                continue
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay)

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
        except Exception as e:
            print(f"⚠️ Translation exception: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)

    print(f"⚠️ Translation failed after {max_retries} attempts, using original")
    return text


def translate_response_to_user_language(response_text, language_info):
    user_lang = language_info['language_code']
    user_script = 'romanized' if language_info['is_romanized'] else 'native'

    if user_lang == 'en':
        return response_text

    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            headers = {
                "Authorization": f"Bearer {SARVAM_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "source_language_code": "en",
                "target_language_code": user_lang,
                "input": response_text,
            }
            if language_info['is_romanized']:
                payload["script"] = "roman"

            print(f"🔄 Translating response → {language_info['language_name']} ({user_script}, Attempt {attempt + 1})")
            res = requests.post(SARVAM_TRANSLATE_API, headers=headers, json=payload, timeout=30)

            if res.status_code == 200:
                translated = res.json().get("translated_text", "").strip()
                if translated and len(translated) > 2:
                    return translated
            elif res.status_code == 429:
                time.sleep(retry_delay * 2)
                continue

            if attempt < max_retries - 1:
                time.sleep(retry_delay)

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
        except Exception as e:
            print(f"⚠️ Response translation exception: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)

    print(f"⚠️ Response translation failed, returning English response")
    return response_text
