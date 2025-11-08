import logging
from fastapi import FastAPI
from app.api import router
from app.services.rabbitmq import RabbitClient

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Note taker")
app.include_router(router)

rabbit_client = RabbitClient()


@app.on_event("startup")
async def startup_event():
    rabbit_client.start_result_consumer()


@app.on_event("shutdown")
async def shutdown_event():
    rabbit_client.stop()
