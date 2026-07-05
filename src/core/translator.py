from .interfaces import ITranslator
import litellm

class LiteLLMTranslator(ITranslator):
    def __init__(self, model: str = "ollama/llama3", mock: bool = False):
        self.model = model
        # Use mock=True if running in an environment without LLM credentials/server
        self.mock = mock

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text.strip():
            return ""
            
        if self.mock:
            return f"[Translating from {source_lang} to {target_lang}]: {text}"

        prompt = (f"You are a professional radio communication translator. "
                  f"Translate the following intercepted text from {source_lang} to {target_lang}. "
                  f"Provide ONLY the translation, no extra explanations or conversational text. "
                  f"\nText:\n{text}")
                  
        try:
            response = litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Translation error: {e}")
            return f"[Translation failed] {text}"
