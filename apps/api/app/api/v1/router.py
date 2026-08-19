from fastapi import APIRouter

from app.api.v1.routers import catalog, health, me, schools

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(me.router)
api_router.include_router(schools.router)
api_router.include_router(catalog.router)

# Registered as each phase lands (see docs/07-roadmap.md):
#   teaching_kit, resources, voice, library, analytics, admin
