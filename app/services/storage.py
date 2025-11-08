import os
from datetime import datetime
from pathlib import Path

AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "audios"))
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def save_audio_file(upload_file) -> str:
    file_id = datetime.now().strftime("%Y_%m_%d %H_%M_%S")
    file_path = AUDIO_DIR / f"{file_id}.wav"

    with open(file_path, "wb") as f:
        f.write(upload_file.file.read())

    return file_id
