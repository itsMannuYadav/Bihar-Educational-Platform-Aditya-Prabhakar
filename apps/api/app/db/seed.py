"""Seed a handful of real Bihar government schools so the onboarding school
picker has something to search against in dev/demo. Not a UDISE import — see
docs/07-roadmap.md Phase 3 for the real seeding task.

Run with: uv run python -m app.db.seed
"""

import asyncio

from sqlalchemy import select

from app.db.models.school import School
from app.db.session import async_session_factory

DEMO_SCHOOLS = [
    {
        "name": "Gram Panchayat Middle School, Nalanda",
        "district": "Nalanda",
        "block": "Bihar Sharif",
    },
    {"name": "Utkramit Madhya Vidyalaya, Gaya", "district": "Gaya", "block": "Gaya Sadar"},
    {"name": "Rajkiya Madhya Vidyalaya, Patna", "district": "Patna", "block": "Patna Sadar"},
    {
        "name": "Uchch Vidyalaya, Muzaffarpur",
        "district": "Muzaffarpur",
        "block": "Muzaffarpur Sadar",
    },
    {"name": "Middle School, Bhagalpur", "district": "Bhagalpur", "block": "Sabour"},
    {
        "name": "Project Balika Uchch Vidyalaya, Darbhanga",
        "district": "Darbhanga",
        "block": "Darbhanga Sadar",
    },
    {"name": "Utkramit High School, Purnia", "district": "Purnia", "block": "Purnia East"},
    {"name": "Madhya Vidyalaya, Begusarai", "district": "Begusarai", "block": "Begusarai"},
]


async def seed_schools() -> None:
    async with async_session_factory() as db:
        existing = (await db.execute(select(School.name))).scalars().all()
        existing_names = set(existing)

        to_add = [School(**s) for s in DEMO_SCHOOLS if s["name"] not in existing_names]
        if not to_add:
            print("Schools already seeded, nothing to do.")
            return

        db.add_all(to_add)
        await db.commit()
        print(f"Seeded {len(to_add)} schools.")


if __name__ == "__main__":
    asyncio.run(seed_schools())
