import logging
import os
from dotenv import load_dotenv
from .asr import create_asr_pipeline
from .llm_client import GeminiClient


load_dotenv()
log = logging.getLogger(__name__)

LLM_PROMPT_FILE = os.getenv("LLM_SYSTEM_PROMPT_FILE")


class Summarizer:
    def __init__(self):
        self.asr = create_asr_pipeline()

        prompt = ""
        if os.path.exists(LLM_PROMPT_FILE):
            with open(LLM_PROMPT_FILE, "r") as f:
                prompt = f.read()

        self.llm = GeminiClient(system_prompt=prompt)
        log.info("Summarizer initialized with Gemini")

    def transcribe(self, audio_path):
        result = self.asr(audio_path)
        return result.get("text", "")

    def summarize(self, audio_path):
        transcript = self.transcribe(audio_path)
        if not transcript:
            log.warning(f"Empty transcript: {audio_path}")
            return ""

        return self.llm.summarize_text(transcript)
