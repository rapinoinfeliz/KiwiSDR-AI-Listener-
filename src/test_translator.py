from src.core.translator import LiteLLMTranslator

def test_translator_mock():
    # Given we use mock mode, it shouldn't require an API key
    translator = LiteLLMTranslator(mock=True)
    
    text = "This is a test broadcast."
    result = translator.translate(text, "en", "pt")
    
    assert result is not None
    assert result.startswith("[Translating from en to pt]")
