import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.translator import LiteLLMTranslator

def test_translator():
    print("Testing mock translator...")
    mock_translator = LiteLLMTranslator(mock=True)
    text = "Aqui é o rádio central."
    print("Original:", text)
    res = mock_translator.translate(text, source_lang="pt", target_lang="en")
    print("Translated:", res)

if __name__ == "__main__":
    test_translator()
