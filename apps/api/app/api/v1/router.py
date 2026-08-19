from fastapi import APIRouter

from app.api.v1.routers import health, me, schools

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(me.router)
api_router.include_router(schools.router)

# Registered as each phase lands (see docs/07-roadmap.md):
#   catalog, teaching_kit, resources, voice, library, analytics, admin
