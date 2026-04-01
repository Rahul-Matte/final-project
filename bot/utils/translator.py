import requests

def translate(text, target="en"):
    """
    Translates text using LibreTranslate API.
    """
    if target == "en":
        return text

    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source='auto', target=target).translate(text)
        return translated
    except Exception as e:
        print(f"Translation Error: {e}")
        return text
