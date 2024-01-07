from api import config
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from api.routers import es
from mangum import Mangum

settings = config.get_settings()

app = FastAPI(title=settings.app_name, description=settings.description, version=settings.version)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.whitelist)
app.include_router(es.router)


@app.on_event("startup")
def load_prerequisites():
    print("starting app")


@app.get("/info")
async def info(settings: config.Settings = Depends(config.get_settings)):
    return {
        "app_name": settings.app_name,
        "description": settings.description,
        "version": settings.version,
    }


handler = Mangum(app)
