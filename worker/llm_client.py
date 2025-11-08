import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()


class GeminiClient:
    def __init__(self, system_prompt: str = ""):
        self.system_prompt = system_prompt.strip()
        self.model_name = os.getenv("LLM_MODEL", "gemini-2.5-flash")
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_output_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")),
        )

    def summarize_text(self, transcript: str) -> str:
        messages = []
        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt))
        messages.append(HumanMessage(content=transcript))

        response = self.llm.invoke(messages)
        return response.content
