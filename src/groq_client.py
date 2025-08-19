import os
from typing import Generator, List, Dict, Any, Optional
from groq import Groq

class GroqChatClient:
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("GROQ_API_KEY manquant.")
        self.client = Groq(api_key=api_key)
        self.model = model

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.4,
        max_tokens: Optional[int] = None
    ) -> Generator[str, None, None]:
        """
        Génère des chunks de texte depuis Groq (streaming).
        """
        resp = self.client.chat.completions.create(
            messages=messages,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in resp:
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                yield content

    def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.4,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Non-stream completion.
        """
        resp = self.client.chat.completions.create(
            messages=messages,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        return resp.choices[0].message.content or ""