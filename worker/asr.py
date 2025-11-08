from transformers import pipeline
import logging
from dotenv import load_dotenv
import os
import torch

load_dotenv()
log = logging.getLogger(__name__)

ASR_MODEL = os.getenv("ASR_MODEL", "openai/whisper-medium")


def create_asr_pipeline():
    device = 0 if torch.cuda.is_available() else -1
    log.info(f"Loading ASR model {ASR_MODEL} on {device}")
    return pipeline("automatic-speech-recognition", model=ASR_MODEL, device=device)
