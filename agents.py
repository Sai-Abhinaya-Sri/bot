import time
import base64
import requests

from config import (
    SARVAM_API, SARVAM_API_KEY, MODEL_ID,
    SARVAM_TTS_URL, TTS_MODEL, TTS_SPEAKER, TTS_SAMPLE_RATE, TTS_LANGUAGE_MAP,
)


# ================= TEXT-TO-SPEECH =================

def text_to_speech(text, language_info):
    """
    Convert text to speech using Sarvam Bulbul v3.
    Returns raw WAV bytes on success, or None on failure.

    - Automatically picks the correct BCP-47 language code from language_info.
    - Falls back to English voice for unsupported languages.
    - Truncates text to 2500 chars (Bulbul v3 limit) to avoid API errors.
    - Strips markdown symbols so they aren't read aloud.
    """
    import re

    lang_code = language_info.get('language_code', 'en')
    target_lang = TTS_LANGUAGE_MAP.get(lang_code, 'en-IN')   # fallback → English

    # Strip markdown so TTS doesn't read "asterisk asterisk" etc.
    clean_text = re.sub(r'[*_`#>~|]', '', text)
    clean_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_text)  # [label](url) → label
    clean_text = clean_text.strip()

    # Bulbul v3 max = 2500 chars
    if len(clean_text) > 2500:
        clean_text = clean_text[:2497] + "..."

    if not clean_text:
        return None

    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text":                 clean_text,
        "target_language_code": target_lang,
        "model":                TTS_MODEL,
        "speaker":              TTS_SPEAKER,
        "pace":                 1.0,
        "speech_sample_rate":   TTS_SAMPLE_RATE,
    }

    print(f"🔊 TTS: lang={target_lang}, chars={len(clean_text)}")

    try:
        res = requests.post(SARVAM_TTS_URL, headers=headers, json=payload, timeout=30)
        if res.status_code == 200:
            audios = res.json().get("audios", [])
            if audios:
                wav_bytes = base64.b64decode(audios[0])
                print(f"✅ TTS success: {len(wav_bytes)} bytes")
                return wav_bytes
            print("⚠️ TTS: empty audios list in response")
        else:
            print(f"❌ TTS failed ({res.status_code}): {res.text[:200]}")
    except Exception as e:
        print(f"❌ TTS exception: {e}")

    return None


# ================= LLM CALLER =================

def call_llm(messages, language_info=None):
    max_retries = 3
    retry_delay = 2

    # Reinforce language lock at the end of the system prompt
    lang_instruction = ""
    if language_info:
        lang_code = language_info['language_code']
        lang_name = language_info['language_name']
        is_romanized = language_info['is_romanized']

        if is_romanized and lang_code != 'en':
            lang_instruction = (
                f"\n\n⚠️ FINAL REMINDER: The user wrote in {lang_name} using Roman script (code-mixed). "
                f"Your ENTIRE response must be in {lang_name} Roman script. "
                f"Every sentence must contain {lang_name} words written in English letters. "
                f"Do NOT produce full English sentences. Do NOT use native script."
            )
        elif not is_romanized and lang_code != 'en':
            lang_instruction = (
                f"\n\n⚠️ FINAL REMINDER: Respond ONLY in {lang_name} native script. "
                f"Do NOT use Roman/English letters for {lang_name} words."
            )

    if messages and messages[0].get('role') == 'system':
        messages[0]['content'] += lang_instruction

    for attempt in range(max_retries):
        try:
            headers = {
                "Authorization": f"Bearer {SARVAM_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": MODEL_ID,
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7,
            }

            print(f"\n🔍 LLM API Call (Attempt {attempt + 1}/{max_retries})")
            res = requests.post(SARVAM_API, headers=headers, json=payload, timeout=60)
            print(f"📥 Status: {res.status_code}")

            if res.status_code == 403:
                return "❌ Invalid Sarvam API key. Get one at https://dashboard.sarvam.ai"
            if res.status_code == 429:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return "❌ Rate limit exceeded. Try again shortly."
            if res.status_code != 200:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return f"❌ API Error: Status {res.status_code}"

            result = res.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if not result:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return "❌ Empty response from LLM"

            print(f"✅ LLM Success: {len(result)} chars")
            return result

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return "❌ Request timeout. Try again."
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return f"❌ Error: {str(e)[:100]}"

    return "❌ Failed after multiple retries"


# ================= STYLE HELPER =================

def _build_style_example(lang_name, is_roman):
    if is_roman:
        return (
            f"EXAMPLE of correct {lang_name} Roman-script (code-mixed) style:\n"
            f"  Q: How to create a campaign?\n"
            f"  A: Campaign create cheyyataniki, dashboard lo 'Campaigns' section ki velli, "
            f"'Create Campaign' button click cheyyandi. Appudu name, audience, message add cheyyandi. "
            f"Ready aithe 'Activate' cheyyandi!\n"
            f"Notice: {lang_name} words + English technical terms mixed together — "
            f"NO full English sentences, NO pure native script."
        )
    else:
        return (
            f"EXAMPLE of correct {lang_name} native script style:\n"
            f"  Q: How to create a campaign?\n"
            f"  A: కేంపెయిన్ క్రియేట్ చేయడానికి డాష్‌బోర్డ్‌లో 'Campaigns' సెక్షన్‌కి వెళ్ళి, "
            f"'Create Campaign' బటన్ క్లిక్ చేయండి.\n"
            f"Notice: Full {lang_name} native script — only technical product terms stay in English."
        )


# ================= SMART AGENT =================

def smart_agent(q, context, language_info):
    lang_name = language_info['language_name']
    is_roman = language_info['is_romanized']

    if is_roman:
        script_type = f"Roman script code-mixed style ({lang_name} words written in English letters, mixed with English technical terms)"
        anti_rule = f"DO NOT write full sentences in English. DO NOT use {lang_name} native script characters."
    else:
        script_type = f"{lang_name} native script"
        anti_rule = f"DO NOT write in Roman/English letters. DO NOT respond in pure English."

    style_example = _build_style_example(lang_name, is_roman)

    system_prompt = f"""You are a WeNext AI assistant.

### LANGUAGE LOCK — READ CAREFULLY:
The user is writing in: {lang_name} ({script_type})
You MUST reply in the EXACT same style. This is non-negotiable.

### WHAT THIS MEANS:
- Required output: {script_type}
- {anti_rule}
- Mirror the user's sentence structure, tone, and word-mixing ratio exactly.
- Use English ONLY for product/technical terms (button names, feature names, UI labels).
- Every other word must be in {lang_name}.

### STYLE REFERENCE:
{style_example}

### SCOPE:
- Answer ONLY WeNext-related questions (features, campaigns, automation, CRM, pricing).
- For unrelated questions: politely redirect in the user's style.
- For greetings: respond warmly in the user's style."""

    user_payload = f"Context from Documentation:\n{context}\n\nUser Question: {q}"

    return call_llm([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_payload}
    ], language_info)


# ================= WORKFLOW AGENT =================

WENEXT_NODES = """
WENEXT AUTOMATION NODES:

📥 TRIGGERS (15) - Start your automation:
- Starting Step, Webhook Trigger, Campaign Button Trigger, Google Sheet Trigger
- Order Created, Order Updated, Abandoned Cart, New Subscriber
- Order Shipped, Out For Delivery, Order Delivered, Order Paid
- Order Cancelled, Refund Created, WhatsApp Order Received

💬 MESSAGING (11) - Send to user:
- Send Message, Send Template, Send Image, Send Video, Send Audio
- Send Document, Send List, WhatsApp Flow, Send Product, Send Products, AI Agent

📝 USER INPUT (3):
- User Input, Multiple Choice, Address

⚙️ OPERATIONS (7):
- Send Email, Collect Payment, Set Stage
- Get Sheet Records, Add Sheet Record, Update Sheet Record, Delete Sheet Record

🔀 LOGIC & CONTROL (5):
- Condition, HTTP Request, Set Tag, Loop, Wait

💾 DATA STORE (4):
- Create Record, Get Records, Update Record, Delete Record

🛑 END: End
"""


def workflow_agent(q, history, language_info):
    context = ""
    if history:
        for h in history[-5:]:
            context += f"User: {h['q']}\nAssistant: {h['a']}\n"

    if len(q.split()) <= 6 and not any(h.get('q', '').lower().count('automat') for h in history):
        return (
            "👍 Let's build your WeNext automation!\n\n"
            "📋 **What do you want to automate?**\n\n"
            "Examples:\n"
            "- Welcome new customers\n"
            "- Confirm orders automatically\n"
            "- Recover abandoned carts\n"
            "- Qualify leads\n\n"
            "Tell me what you need! 🚀"
        )

    system = f"""You are a WeNext automation expert helping users build WhatsApp workflows.

{WENEXT_NODES}

YOUR JOB:
1. Understand what user wants to automate
2. Build workflow using ONLY nodes listed above
3. Guide step-by-step (one or two steps at a time)
4. Use format: Trigger → Action → Logic → Action

RESPONSE FORMAT:
**Step [N]: [Action]** [emoji]
Node: [Exact Node Name]
Purpose: [What it does]
Setup: [How to configure]

RULES:
✅ Use ONLY nodes from list above
✅ Keep responses under 200 words
✅ Ask before showing next steps"""

    return call_llm([
        {"role": "system", "content": system},
        {"role": "user", "content": f"{context}\nUser: {q}"}
    ], language_info)
