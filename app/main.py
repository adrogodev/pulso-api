from fastapi import FastAPI
from app.adapters.api.search_controller import router as search_router
from app.adapters.api.album_controller import router as album_router

app = FastAPI(title="RythmX Backend")

@app.get("/")
def root():
    return {"message": "Hello desde Python con FastAPI"}

# Registrar routers
app.include_router(search_router)
app.include_router(album_router)

