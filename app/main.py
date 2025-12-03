from fastapi import FastAPI
from app.infrastructure.config.config_infrastructure import config_infrastructure
from app.application.config.config_application import config_application
from app.api.config.config_api import config_api
from app.api.routes.api_router import api_router


app = FastAPI(title="rythmx")

@app.get("/")
def root():
    return {"message": "rythmx api running..."}

config_infrastructure()
config_application()
config_api()

# Registrar routers
app.include_router(api_router)

