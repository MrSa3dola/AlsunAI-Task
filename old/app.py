from fastapi import FastAPI

from old.whatsapp_webhook import whatsapp_router

app = FastAPI()
app.include_router(whatsapp_router)
