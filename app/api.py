from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from .services.rabbitmq import RabbitClient, RESULTS
from .services.storage import save_audio_file
from pathlib import Path
import logging


log = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
router = APIRouter()

rabbit_client = RabbitClient()


@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".wav"):
        raise HTTPException(status_code=400, detail="Only .wav files are supported")

    file_id = save_audio_file(file)
    payload = {"id": file_id}
    rabbit_client.publish_task(payload)
    log.info(f"Published task: {file_id}")
    return file_id


@router.get("/get-summary/{file_id}")
async def get_summary(file_id: str):
    print(f"GET RESULT: {RESULTS}")
    summary = RESULTS.get(file_id)
    if summary:
        return summary

    return None
