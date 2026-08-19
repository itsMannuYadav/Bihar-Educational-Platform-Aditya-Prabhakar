from fastapi import APIRouter

from app.api.v1.routers import catalog, health, me, schools, teaching_kit

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(me.router)
api_router.include_router(schools.router)
api_router.include_router(catalog.router)
api_router.include_router(teaching_kit.router)

# Registered as each phase lands (see docs/07-roadmap.md):
#   resources, voice, library, analytics, admin
