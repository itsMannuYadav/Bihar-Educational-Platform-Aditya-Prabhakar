from fastapi import APIRouter

from app.api.v1.routers import catalog, health, library, me, resources, schools, teaching_kit, voice

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(me.router)
api_router.include_router(schools.router)
api_router.include_router(catalog.router)
api_router.include_router(teaching_kit.router)
api_router.include_router(resources.router)
api_router.include_router(voice.router)
api_router.include_router(library.router)

# Registered as each phase lands (see docs/07-roadmap.md):
#   analytics, admin
