from fastapi import FastAPI

from api.routes import router

app = FastAPI(title="OmniDesk API")

app.include_router(router, prefix="/api")