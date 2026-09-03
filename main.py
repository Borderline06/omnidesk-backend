import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from bot.main import telegram_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Al iniciar la API, arranca el bot de Telegram en segundo plano
    await telegram_app.initialize()
    await telegram_app.start()
    asyncio.create_task(telegram_app.updater.start_polling())
    print(">>> Bot de Telegram en línea y escuchando...")

    yield  # La API REST queda activa escuchando a Dashboard / Webhooks

    # 2. Al apagar la API, detiene el bot de Telegram limpiamente
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()
    print(">>> Bot de Telegram detenido.")

app = FastAPI(title="OmniDesk API", lifespan=lifespan)

# Habilitar CORS para conectar con omnidesk-dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {"status": "ok", "message": "OmniDesk Backend y Bot de Telegram en ejecución"}